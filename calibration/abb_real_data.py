#!/usr/bin/env python3
"""
真实机器人数据采集脚本
用于为calibration.py采集真实的触觉传感器数据
兼容calibration.py的数据格式要求

数据格式：
{
    "物体名": {
        "traj_0": {
            "step_000": {
                "marker_displacement": np.array,  # (20, 11, 2) marker位移
                "force_xyz": np.array,            # (3,) 三维力
                "sensor_pose": dict,              # TCP位姿
                "metadata": dict,                 # 轨迹/步信息
                "depth_field": None
            },
            ...
        },
        ...
    }
}
"""

import argparse
import cv2
import sys
import os
import time
from time import sleep
import numpy as np
import pandas as pd
from datetime import datetime
from threading import Thread
from pathlib import Path
from typing import Dict, List, Optional
import yaml
import json
import pickle
import copy

from pyabb import ABBRobot, Logger, Affine
from pyati.ati_sensor import ATISensor
from xensesdk import Sensor

# 添加项目路径
PROJ_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJ_DIR))

from example.MarkerInterp import MarkerInterpolator

logger = Logger(log_level='DEBUG', name="ABB_Real_Data", log_path=None)

TIME_STAMP = str(datetime.now().strftime('%y_%m_%d__%H_%M_%S'))


def _load_available_objects(traj_path: Path) -> List[str]:
    if not traj_path.exists():
        return []
    try:
        with open(traj_path, 'r', encoding='utf-8') as fp:
            cfg = json.load(fp)
        return list(cfg.keys()) if isinstance(cfg, dict) else []
    except Exception:
        return []


class TactileSensor():
    """真实触觉传感器管理类，适配calibration数据格式"""
    def __init__(self):
        """初始化xense触觉传感器"""
        self.sensor = Sensor.create(0)
        marker_init = self.sensor.selectSensorInfo(Sensor.OutputType.Marker2DInit)
        self.marker_interpolator = MarkerInterpolator(marker_init)

    def get_data(self):
        """获取传感器数据"""
        marker_2D = self.sensor.selectSensorInfo(Sensor.OutputType.Marker2D)
        marker_displacement = self.marker_interpolator.interpolate(marker_2D)
        return marker_displacement

    def release(self):
        """释放传感器"""
        self.sensor.release()


class ABBDataCollector():
    """ABB机器人数据采集器"""
    def __init__(self, pose0, object_name="cube", config_file=None, storage_file=None):
        """
        初始化数据采集器

        Args:
            pose0: 初始位置 [x, y, z, qw, qx, qy, qz]
            object_name: 物体名称
            config_file: 配置文件路径
        """
        self.object_name = object_name

        # 加载配置
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self._get_default_config()

        self.step_settle_time = float(self.config.get('step_settle_time', 0.3))
        self.safe_offset_mm = float(self.config.get('safe_offset_mm', 1.0))
        self.frame_interval = float(self.config.get('frame_interval', 0.1))
        self.data_frames = int(self.config.get('data_frames', 10))
        self.trajectory_config = self._load_trajectory_config()

        # 数据汇总文件
        default_storage = PROJ_DIR / "calibration" / "data" / "real_calibration_data.pkl"
        self.storage_file = Path(storage_file) if storage_file else default_storage
        self.storage_file.parent.mkdir(exist_ok=True, parents=True)

        # 初始化机器人
        self.robot = ABBRobot(
            ip="192.168.125.1",
            port_motion=5000,
            port_logger=5001,
            port_signal=5002,
        )
        logger.warning("Connect to Server")
        self.robot.initialize()

        # 设置运动参数
        self.robot.set_acceleration(0.5, 0.5)
        self.robot.set_velocity(20, 20)

        pose0_init = [574.33, -176.67, 194.89, 0, 1, 0, 0]  # 默认初始位置
        self.robot.moveCart(pose0_init)
        self._check_joint_limit()
        time.sleep(1)

        # 移动到初始位置
        self.pose0 = pose0
        self.robot.moveCart(self.pose0)

        time.sleep(1)

        logger.info(f"init pose: {self.robot.get_cartesian()}")
        logger.info(f"init velocity: {self.robot.get_velocity()}")

        # 初始化ATI传感器
        self.ati = ATISensor(ip="192.168.1.10", filter_on=False)
        time.sleep(2)
        self.ati.tare()

        # 初始化触觉传感器
        self.sensor = TactileSensor()
        self.rot_sensor = (Affine(a=90, c=180) * Affine(c=-45)).rotation()

        # 接触检测参数
        self.z_cont = None  # 接触位置，将在运行时确定
        self.cont_th = self.config.get('contact_threshold', -0.05)

        # 存储采集的数据 (calibration.py格式)
        self.calibration_data = {}

    def _get_default_config(self):
        """获取默认配置"""
        return {
            'contact_threshold': -0.02,
            'approach_speed': 1,  # mm/s
            'press_speed': 8,      # mm/s
            'max_force': -1,      # N
            'data_frames': 30,     # 每步采集数据帧数
            'frame_interval': 0.1,  # 帧间隔时间 s
            'step_settle_time': 0.3,  # 每步运动后的等待时间 s
            'safe_offset_mm': 8.0    # 安全抬起高度 mm
        }

    def _load_trajectory_config(self) -> Dict[str, Dict[str, List[Dict[str, float]]]]:
        """读取轨迹配置"""
        traj_path = PROJ_DIR / "calibration" / "obj" / "traj.json"
        if not traj_path.exists():
            logger.warning(f"未找到轨迹配置文件: {traj_path}")
            return {}

        try:
            with open(traj_path, 'r', encoding='utf-8') as fp:
                raw_config = json.load(fp)
        except Exception as exc:
            logger.error(f"轨迹配置解析失败: {exc}")
            return {}

        normalized: Dict[str, Dict[str, List[Dict[str, float]]]] = {}

        for obj_name, traj_dict in raw_config.items():
            if not isinstance(traj_dict, dict):
                continue

            obj_trajs: Dict[str, List[Dict[str, float]]] = {}

            for traj_name, steps_payload in traj_dict.items():
                steps: List[Dict[str, float]] = []

                if isinstance(steps_payload, list):
                    for entry in steps_payload:
                        if isinstance(entry, dict):
                            dx = float(entry.get("x", 0.0))
                            dy = float(entry.get("y", 0.0))
                            dz = float(entry.get("z", 0.0))
                            steps.append({"x": dx, "y": dy, "z": dz})
                        elif isinstance(entry, (list, tuple)) and len(entry) == 3:
                            dx, dy, dz = map(float, entry)
                            steps.append({"x": dx, "y": dy, "z": dz})
                elif isinstance(steps_payload, dict) and {"x", "y", "z"} <= steps_payload.keys():
                    x_seq = steps_payload.get("x", [])
                    y_seq = steps_payload.get("y", [])
                    z_seq = steps_payload.get("z", [])
                    for dx, dy, dz in zip(x_seq, y_seq, z_seq):
                        steps.append({"x": float(dx), "y": float(dy), "z": float(dz)})

                if steps:
                    obj_trajs[traj_name] = steps

            if obj_trajs:
                normalized[obj_name] = obj_trajs

        if not normalized:
            logger.warning("轨迹配置中没有可用的轨迹")

        return normalized

    def _check_joint_limit(self):
        """检查关节限位"""
        current_joint = self.robot.get_joint()
        if current_joint[5] > 180:
            self.robot.moveJoint(
                current_joint[0], current_joint[1], current_joint[2],
                current_joint[3], current_joint[4], current_joint[5] - 360
            )
        elif current_joint[5] < -180:
            self.robot.moveJoint(
                current_joint[0], current_joint[1], current_joint[2],
                current_joint[3], current_joint[4], current_joint[5] + 360
            )

    def get_robot_xyz(self):
        """获取机器人当前位置"""
        pose = self.robot.get_cartesian()
        return pose.x, pose.y, pose.z

    def get_ati_data(self):
        """获取ATI传感器数据"""
        return self.ati.data.copy()

    def get_sensor_force_xyz(self):
        force_xyz = self.get_ati_data()[0:3]
        return self.rot_sensor @ force_xyz

    def move_to_xyz(self, x, y, z):
        """移动到指定位置"""
        cp = self.robot.get_cartesian()
        target_pose = Affine(x=x, y=y, z=z, a=cp.a, b=cp.b, c=cp.c)
        self.robot.moveCart(target_pose)
        while self.robot.moving:
            time.sleep(self.step_settle_time)

    def move_delta_xyz(self, dx=0, dy=0, dz=0):
        """移动到指定位置"""
        cp = self.robot.get_cartesian()
        target_pose = Affine(x=cp.x + dx, y=cp.y + dy, z=cp.z + dz, a=cp.a, b=cp.b, c=cp.c)
        self.robot.moveCart(target_pose)
        while self.robot.moving:
            time.sleep(self.step_settle_time)


    def relative_move(self, x=0, y=0, z=0, Rz=0, Ry=0, Rx=0):
        """相对移动"""
        cp = self.robot.get_cartesian()
        target_pose = (Affine(x=cp.x, y=cp.y, z=cp.z, a=cp.a, b=cp.b, c=cp.c) *
                      Affine(x=x, y=y, z=z, a=Rz, b=Ry, c=Rx))
        self.robot.moveCart(target_pose)
        while self.robot.moving:
            time.sleep(0.01)


    def move_to_contact(self):
        """移动到刚好接触的位置"""
        logger.info("开始寻找接触位置...")
        if self.z_cont is not None:
            self.robot.set_velocity(20,20)
            cp = self.robot.get_cartesian()
            self.move_to_xyz(cp.x, cp.y, self.z_cont + 0.1)
        else:
            self.move_to_xyz(556.97, -200.20, 115.05 + 0.1)

        # 设置较慢的接近速度
        self.robot.set_velocity(self.config['approach_speed'], self.config['approach_speed'])

        is_contact = False

        while not is_contact:
            # 安全检测
            fz = self.get_ati_data()[2]
            if fz <= self.config['max_force']:
                logger.error(f'力过大，退出: {fz}N')
                raise RuntimeError(f'Force too large: {fz}N')

            fz_current = self.get_ati_data()[2]
            logger.debug(f'ATI Z方向力: {fz_current}N')

            # 检测接触
            if fz_current <= self.cont_th:
                self.z_cont = self.robot.get_cartesian().z
                logger.info(f"检测到接触，接触位置: {self.z_cont}mm")
                is_contact = True
                break

            # 向下移动
            self.move_delta_xyz(dz=-0.01)
            time.sleep(0.2)

        if not is_contact:
            raise RuntimeError("未检测到接触")

        # 恢复正常速度
        self.robot.set_velocity(self.config['press_speed'], self.config['press_speed'])

    def collect_calibration_data(self) -> Dict[str, Dict[str, Dict]]:
        """按轨迹采集真实触觉数据"""
        logger.info(f"开始采集 {self.object_name} 的轨迹数据...")

        trajectories = self.trajectory_config.get(self.object_name, {})
        if not trajectories:
            logger.warning(f"物体 {self.object_name} 未在轨迹配置中找到，跳过")
            self.calibration_data[self.object_name] = {}
            return {self.object_name: {}}

        object_data: Dict[str, Dict[str, Dict]] = {}

        for traj_name, steps in trajectories.items():
            try:
                traj_data = self._execute_trajectory(traj_name, steps)
                if traj_data:
                    object_data[traj_name] = traj_data
            except Exception as exc:
                logger.error(f"轨迹 {traj_name} 执行失败: {exc}")

        self.calibration_data[self.object_name] = object_data
        logger.info(f"物体 {self.object_name} 采集完成，共 {len(object_data)} 条轨迹")
        return {self.object_name: object_data}

    def _execute_trajectory(self, trajectory_name: str, steps: List[Dict[str, float]]) -> Dict[str, Dict]:
        """执行单条轨迹并采集每一步的数据"""
        if not steps:
            return {}

        logger.info(f"执行轨迹 {trajectory_name}，共 {len(steps)} 步")

        self.move_to_safe_height()
        time.sleep(self.step_settle_time)
        self.move_to_contact()
        time.sleep(self.step_settle_time)

        trajectory_data: Dict[str, Dict] = {}

        for idx, step in enumerate(steps):
            dx = float(step.get('x', 0.0))
            dy = float(step.get('y', 0.0))
            dz = float(step.get('z', 0.0))

            self.move_delta_xyz(dx=dx, dy=dy, dz=dz)

            metadata = {
                'trajectory': trajectory_name,
                'step_index': idx,
                'commanded_delta_mm': (dx, dy, dz)
            }

            step_data = self._collect_current_step_data(metadata=metadata)
            if step_data:
                step_key = f"step_{idx:03d}"
                trajectory_data[step_key] = step_data

        self.move_to_safe_height()
        time.sleep(self.step_settle_time)

        logger.info(f"轨迹 {trajectory_name} 完成，采集 {len(trajectory_data)} 条数据")
        return trajectory_data

    def _collect_current_step_data(self, metadata: Optional[Dict] = None) -> Dict:
        """采集当前姿态下的数据"""
        try:
            force_data_list = []
            marker_disp = self.sensor.get_data()
            for _ in range(self.data_frames):
                force_xyz = self.get_sensor_force_xyz()
                force_data_list.append(force_xyz)
                time.sleep(self.frame_interval)
            avg_force = np.mean(force_data_list, axis=0)

            data = {
                'marker_displacement': marker_disp.astype(np.float32),
                'force_xyz': avg_force.astype(np.float32),
                'metadata': metadata or {},
                'depth_field': None
            }

            logger.debug(f"step {metadata['step_index'] if metadata else 'unknown'}: force={avg_force}")
            return data

        except Exception as e:
            logger.error(f"当前步数据采集失败: {e}")
            raise

    def move_to_safe_position(self):
        """移动到安全位置"""
        self.robot.set_velocity(20, 20)
        safe_z = self.pose0[2] + max(self.safe_offset_mm, 50)
        current_pose = self.robot.get_cartesian()
        self.move_to_xyz(current_pose.x, current_pose.y, safe_z)
        time.sleep(1)

    def move_to_safe_height(self):
        """移动到安全高度（相对于接触位置）"""
        if self.z_cont is not None:
            safe_z = self.z_cont + self.safe_offset_mm
        else:
            safe_z = self.pose0[2] + self.safe_offset_mm

        current_pose = self.robot.get_cartesian()
        self.move_to_xyz(current_pose.x, current_pose.y, safe_z)
        time.sleep(0.5)

    def _load_storage(self) -> Dict:
        if not self.storage_file.exists():
            return {}
        try:
            with open(self.storage_file, 'rb') as fp:
                data = pickle.load(fp)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            logger.error(f"读取汇总文件失败: {exc}")
            return {}

    def _save_storage(self, data: Dict):
        with open(self.storage_file, 'wb') as fp:
            pickle.dump(data, fp)
        logger.info(f"汇总数据已写入: {self.storage_file}")

    def save_calibration_data(self):
        """将采集结果写入统一汇总文件"""
        if not self.calibration_data:
            logger.warning("无采集数据可保存")
            return self.storage_file

        storage = self._load_storage()

        for obj_name, obj_data in self.calibration_data.items():
            storage.setdefault(obj_name, {})
            for traj_name, traj_steps in obj_data.items():
                storage[obj_name].setdefault(traj_name, {})
                for step_key, step_data in traj_steps.items():
                    if step_key in storage[obj_name][traj_name]:
                        logger.warning(
                            f"覆盖已有数据: {obj_name}/{traj_name}/{step_key}")
                    storage[obj_name][traj_name][step_key] = copy.deepcopy(step_data)

        self._save_storage(storage)
        logger.info(
            f"已更新对象 {list(self.calibration_data.keys())} 的轨迹数据 -> {self.storage_file}")
        return self.storage_file

    def cleanup(self):
        """清理资源"""
        logger.info("清理资源...")

        # 移动到安全位置
        self.move_to_safe_position()

        # 保存数据
        if self.calibration_data:
            self.save_calibration_data()

        # 释放传感器
        try:
            self.sensor.release()
        except:
            pass

        # 关闭机器人马达
        try:
            time.sleep(1)
            self.robot.sig_motor_off()
        except:
            pass

        logger.info("清理完成")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ABB真实触觉数据采集")
    parser.add_argument("--object", required=True, default="circle_r3", help="需要采集的物体名称，与traj.json保持一致")
    parser.add_argument("--pose", nargs=7, type=float, metavar=('x', 'y', 'z', 'qw', 'qx', 'qy', 'qz'),
                        help="机器人初始位姿，未提供时使用脚本内默认")
    parser.add_argument("--config", type=str, default=None, help="自定义采集配置文件路径")
    parser.add_argument("--storage", type=str, default=None, help="统一汇总数据文件路径")
    parser.add_argument("--dry-run", action="store_true", help="仅验证配置与轨迹，不执行采集")
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    traj_path = PROJ_DIR / "calibration" / "obj" / "traj.json"
    available_objects = _load_available_objects(traj_path)

    if available_objects and args.object not in available_objects:
        logger.error(f"物体 {args.object} 不在轨迹配置中。可用物体: {available_objects}")
        return

    pose0_default = [574.33 - 32 + 28.5/2, -176.67 - 32 + 17.2 / 2, 94.89 + 20 + 20, 0, 1, 0, 0]

    pose0 = args.pose if args.pose else pose0_default

    collector = ABBDataCollector(
        pose0=pose0,
        object_name=args.object,
        config_file=args.config,
        storage_file=args.storage
    )

    if args.dry_run:
        logger.info("dry-run 模式：仅检查配置，不执行运动")
        logger.info(f"可用轨迹: {list(collector.trajectory_config.get(args.object, {}).keys())}")
        collector.cleanup()
        return

    try:
        calibration_data = collector.collect_calibration_data()

        logger.info("标定数据采集完成")
        for obj_name, obj_data in calibration_data.items():
            logger.info(f"物体: {obj_name}, 轨迹数: {len(obj_data)}")
            for traj_name, steps in obj_data.items():
                logger.info(f"  {traj_name}: {len(steps)} steps")

    except Exception as e:
        logger.error(f"数据采集过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        collector.cleanup()


if __name__ == '__main__':
    main()
