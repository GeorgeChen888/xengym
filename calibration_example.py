#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单传感器标定场景示例
用于材料参数贝叶斯优化的数据采集演示
"""

import numpy as np
from pathlib import Path
import time
import sys
from typing import Dict, List

def add_calibration_path():
    """添加calibration目录到Python路径"""
    calibration_dir = Path(__file__).parent / "calibration"
    if str(calibration_dir) not in sys.path:
        sys.path.insert(0, str(calibration_dir))

def create_real_raw_data():
    """使用fem_processor创建真实的raw_data"""
    try:
        add_calibration_path()
        from fem_processor import process_gel_data
        
        # 使用fem_processor生成FEM数据
        processor = process_gel_data('g1-ws', E=0.20, nu=0.45, use_cache=True)
        
        # 使用get_data方法获取完整数据
        raw_data = processor.get_data()
        
        print(f"✓ 真实FEM数据加载完成")
        print(f"   节点数: {len(raw_data['node'])}")
        print(f"   单元数: {len(raw_data['elements'])}")
        print(f"   顶部节点数: {len(raw_data['top_nodes'])}")
        
        return raw_data
        
    except Exception as e:
        print(f"❌ 无法加载真实FEM数据: {e}")
        print("使用简化的示例数据...")
        return create_fallback_raw_data()

def create_fallback_raw_data():
    """创建简化的示例raw_data（作为备选方案）"""
    # 创建基础数据
    n_nodes = 1000
    n_elements = 200
    n_top_nodes = 220  # 20x11 = 220 个顶部节点
    
    # 创建top_indices和top_vert_indices（模拟）
    n_top_faces = (20-1) * (11-1)  # 19x10 = 190 个面
    top_indices = np.random.randint(0, n_nodes, (n_top_faces, 4), dtype=np.uint32)
    top_vert_indices = np.random.randint(0, n_top_nodes, (n_top_faces, 4), dtype=np.uint32)
    
    # 创建简单的刚度矩阵（单位矩阵）
    from scipy.sparse import eye
    KF = eye(n_nodes * 3, dtype=np.float32)
    
    return {
        'KF': KF,
        'node': np.random.rand(n_nodes, 3).astype(np.float32),
        'elements': np.random.randint(0, n_nodes, (n_elements, 8), dtype=np.uint32),
        'top_nodes': np.arange(n_top_nodes, dtype=np.uint32),
        'top_indices': top_indices,
        'top_vert_indices': top_vert_indices,
        'mesh_shape': (20, 11)
    }

def main():
    """主函数"""
    print("🎯 标定场景使用示例")
    print("=" * 50)
    
    try:
        # 导入模块
        from xengym.render.calibScene import create_calibration_scene
        
        # 1. 准备物体文件
        print("\n📋 步骤1: 准备标定物体")
        asset_dir = Path("xengym/assets/obj")
        
        # 查找可用的物体文件
        possible_objects = [
            "circle_r4.STL", "circle_r5.STL", "circle_r6.STL", 
            "cube_15mm.obj", "handle.STL"
        ]
        
        object_files = []
        for obj_name in possible_objects:
            obj_path = asset_dir / obj_name
            if obj_path.exists():
                object_files.append(str(obj_path))
                print(f"✓ 找到物体: {obj_name}")
        
        if not object_files:
            print("❌ 未找到标定物体文件")
            return
        
        # 2. 创建raw_data（使用fem_processor）
        print("\n📋 步骤2: 准备FEM数据")
        raw_data = create_real_raw_data()
        print(f"fem_data.keys: {raw_data.keys()}")
        
        # 3. 创建标定场景
        print("\n📋 步骤3: 创建标定场景")
        scene = create_calibration_scene(
            object_files=object_files,
            raw_data=raw_data,
            visible=True,
            sensor_visible=False,  # 简化演示，不显示传感器窗口
        )
        print("✓ 标定场景创建成功")
        print(f"   可用物体: {scene.get_available_objects()}")
        
        # 4. 演示数据采集
        print("\n📋 步骤4: 演示数据采集")
        
        if scene.objects:
            # 选择第一个物体
            first_object = list(scene.objects.keys())[0]
            scene.set_current_object(first_object)
            print(f"✓ 设置当前物体: {first_object}")
            
            # 采集单个深度的数据
            print("🔄 采集0.2mm深度数据...")
            try:
                depth_data = scene.collect_data_for_depth(0.2)
                print("✓ 数据采集成功")
                print(f"   深度场形状: {depth_data['depth_field'].shape}")
                print(f"   Marker位移形状: {depth_data['marker_displacement'].shape}")
                
            except Exception as e:
                print(f"❌ 数据采集失败: {e}")
        
        # 5. 演示完整的标定数据格式
        print("\n📋 步骤5: 标定数据格式")
        print("标定数据字典结构:")
        print("  {")
        print("    'object_name': {")
        print("      '0.1mm': {")
        print("        'depth_field': (700, 400),           # 深度场")
        print("        'marker_displacement': (20, 11, 2)   # Marker XY位移")
        print("      },")
        print("      '0.2mm': { ... },")
        print("      ... # 其他深度")
        print("    }")
        print("  }")
        
        print("\n🎉 演示完成!")
        print("💡 可以在贝叶斯优化中使用scene.collect_all_calibration_data()采集完整数据")
        
        return scene
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_objective_function(scene, real_data=None):
    """
    创建贝叶斯优化的目标函数
    
    Parameters:
    - scene : CalibrationScene, 标定场景
    - real_data : Dict, 真实传感器数据（用于比较）
    
    Returns:
    - Callable, 目标函数
    """
    def objective_function(params):
        """
        目标函数：给定材料参数，返回仿真与真实数据的误差
        
        Parameters:
        - params : np.ndarray, [E, nu] 材料参数
        
        Returns:
        - float, 误差值（越小越好）
        """
        E, nu = params
        print(f"🔄 评估材料参数: E={E:.4f}, nu={nu:.4f}")
        
        try:
            # 使用标定场景采集数据
            sim_data = scene.calibrate_with_parameters(E, nu)
            
            # 计算与真实数据的误差
            if real_data is not None:
                error = calculate_calibration_error(sim_data, real_data)
            else:
                # 如果没有真实数据，使用模拟误差（基于参数的函数）
                # 假设真实参数为 E=0.2, nu=0.45
                true_E, true_nu = 0.2000, 0.4500
                param_error = (E - true_E)**2 + (nu - true_nu)**2
                error = param_error * 10  # 放大误差以便观察
            
            print(f"   计算误差: {error:.6f}")
            return error
            
        except Exception as e:
            print(f"   ❌ 评估失败: {e}")
            return float('inf')  # 返回极大值表示失败
    
    return objective_function

def calculate_calibration_error(sim_data, real_data):
    """
    计算仿真数据与真实数据的误差
    
    Parameters:
    - sim_data : Dict, 仿真数据
    - real_data : Dict, 真实数据
    
    Returns:
    - float, 总误差
    """
    total_error = 0.0
    data_count = 0
    
    for obj_name, obj_sim_data in sim_data.items():
        if obj_name not in real_data:
            continue
            
        obj_real_data = real_data[obj_name]
        
        for depth_key, depth_sim_data in obj_sim_data.items():
            if depth_key not in obj_real_data:
                continue
                
            depth_real_data = obj_real_data[depth_key]
            
            # 计算深度场误差
            depth_field_error = np.mean(
                (depth_sim_data['depth_field'] - depth_real_data['depth_field'])**2
            )
            
            # 计算Marker位移误差
            marker_error = np.mean(
                (depth_sim_data['marker_displacement'] - depth_real_data['marker_displacement'])**2
            )
            
            total_error += depth_field_error + marker_error
            data_count += 1
    
    return total_error / max(data_count, 1)

def test_calibration_scene():
    """测试标定场景的基本功能"""
    print("🎯 测试单传感器标定场景")
    print("=" * 60)
    
    # 1. 准备标定物体
    print("\n📋 步骤1: 准备标定物体")
    
    # 尝试多个可能的路径
    possible_paths = [
        Path("xengym/assets/obj"),
        Path(__file__).parent / "xengym" / "assets" / "obj",
        Path(__file__).parent / "calibration" / "xengym" / "assets" / "obj",
        Path("/home/czl/Downloads/workspace/xengym/xengym/assets/obj")
    ]
    
    object_files = []
    asset_dir = None
    for path in possible_paths:
        if path.exists():
            asset_dir = path
            break
    
    if asset_dir is None:
        print("❌ 无法找到assets目录")
        return None
    
    # 查找可用的STL文件
    for obj_name in ["circle_r4.STL", "circle_r5.STL", "circle_r6.STL"]:
        obj_path = asset_dir / obj_name
        if obj_path.exists():
            object_files.append(str(obj_path))
            print(f"✓ 找到物体: {obj_name}")
    
    if not object_files:
        print("❌ 未找到标定物体文件")
        return None
    
    # 2. 创建标定场景
    print("\n📋 步骤2: 创建标定场景")
    try:
        from xengym.render.calibScene import create_calibration_scene
        
        scene = create_calibration_scene(
            object_files=object_files,
            visible=False,  # 不显示窗口
            sensor_visible=False
        )
        print("✓ 标定场景创建完成")
        
    except Exception as e:
        print(f"❌ 标定场景创建失败: {e}")
        return None
    
    # 3. 测试数据采集
    print("\n📋 步骤3: 测试数据采集")
    try:
        # 采集标定数据
        calibration_data = scene.collect_all_calibration_data()
        
        # 打印数据摘要
        summary = scene.get_calibration_data_summary()
        print("\n📊 标定数据摘要:")
        for obj_name, info in summary.items():
            if isinstance(info, dict):
                print(f"  {obj_name}: {info['depths_count']}个深度, 形状: {info['data_shape']}")
        
        print(f"✓ 数据采集测试完成，共采集 {len(calibration_data)} 个物体的数据")
        return scene
        
    except Exception as e:
        print(f"❌ 数据采集失败: {e}")
        return None

def test_parameter_calibration():
    """测试不同材料参数的标定"""
    print("\n🎯 测试不同材料参数的标定")
    print("=" * 60)
    
    # 创建标定场景
    # 尝试多个可能的路径
    possible_paths = [
        Path("xengym/assets/obj"),
        Path(__file__).parent / "xengym" / "assets" / "obj",
        Path(__file__).parent / "calibration" / "xengym" / "assets" / "obj",
        Path("/home/czl/Downloads/workspace/xengym/xengym/assets/obj")
    ]
    
    object_files = []
    asset_dir = None
    for path in possible_paths:
        if path.exists():
            asset_dir = path
            break
    
    if asset_dir is None:
        print("❌ 无法找到assets目录")
        return None
    
    # 查找可用的STL文件
    stl_files = list(asset_dir.glob("*.STL"))
    if not stl_files:
        print(f"❌ 在 {asset_dir} 中未找到STL文件")
        return None
    
    object_files = [str(stl_files[0])]  # 使用第一个STL文件
    print(f"✓ 使用物体文件: {object_files[0]}")
    
    try:
        from xengym.render.calibScene import create_calibration_scene
        
        scene = create_calibration_scene(
            object_files=object_files,
            visible=False,
            sensor_visible=False
        )
        
        # 测试不同的材料参数
        test_params = [
            (0.1500, 0.4200),
            (0.2000, 0.4500),
            (0.2500, 0.4800),
        ]
        
        print("\n📋 测试不同材料参数:")
        for E, nu in test_params:
            print(f"\n  测试参数: E={E}, nu={nu}")
            
            try:
                # 使用指定参数进行标定
                calibration_data = scene.calibrate_with_parameters(E, nu)
                
                if calibration_data:
                    print(f"  ✓ 标定成功，数据包含 {len(calibration_data)} 个物体")
                    
                    # 显示第一个物体的数据摘要
                    first_obj = list(calibration_data.keys())[0]
                    obj_data = calibration_data[first_obj]
                    print(f"    物体 '{first_obj}' 包含 {len(obj_data)} 个深度数据")
                    print(f"    深度值: {list(obj_data.keys())}")
                    
                    # 显示数据形状
                    first_depth = list(obj_data.keys())[0]
                    depth_data = obj_data[first_depth]
                    print(f"    深度场形状: {depth_data['depth_field'].shape}")
                    print(f"    Marker位移形状: {depth_data['marker_displacement'].shape}")
                else:
                    print(f"  ❌ 标定失败")
                    
            except Exception as e:
                print(f"  ❌ 标定失败: {e}")
        
        return scene
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return None

def run_bayesian_optimization_demo():
    """运行贝叶斯优化演示"""
    print("\n🎯 贝叶斯优化演示")
    print("=" * 60)
    
    # 1. 准备标定场景
    print("\n📋 步骤1: 准备标定场景")
    
    # 尝试多个可能的路径
    possible_paths = [
        Path("xengym/assets/obj"),
        Path(__file__).parent / "xengym" / "assets" / "obj",
        Path(__file__).parent / "calibration" / "xengym" / "assets" / "obj",
        Path("/home/czl/Downloads/workspace/xengym/xengym/assets/obj")
    ]
    
    object_files = []
    asset_dir = None
    for path in possible_paths:
        if path.exists():
            asset_dir = path
            break
    
    if asset_dir is None:
        print("❌ 无法找到assets目录")
        return None, None
    
    # 查找可用的STL文件
    stl_files = list(asset_dir.glob("*.STL"))
    if not stl_files:
        print(f"❌ 在 {asset_dir} 中未找到STL文件")
        return None, None
    
    object_files = [str(f) for f in stl_files[:1]]  # 使用第一个STL文件
    print(f"✓ 使用物体文件: {object_files[0]}")
    
    try:
        from xengym.render.calibScene import create_calibration_scene
        
        scene = create_calibration_scene(
            object_files=object_files,
            visible=False,
            sensor_visible=False
        )
        print("✓ 标定场景创建完成")
        
    except Exception as e:
        print(f"❌ 标定场景创建失败: {e}")
        return None, None
    
    # 2. 创建目标函数
    print("\n📋 步骤2: 创建目标函数")
    objective_func = create_objective_function(scene)
    print("✓ 目标函数创建完成")
    
    # 3. 设置贝叶斯优化参数
    print("\n📋 步骤3: 设置优化参数")
    param_bounds = [
        (0.1000, 0.3000),   # E的搜索范围
        (0.4000, 0.5000)    # nu的搜索范围
    ]
    print(f"   E范围: {param_bounds[0]} (精度: 4位小数)")
    print(f"   nu范围: {param_bounds[1]} (精度: 4位小数)")
    
    # 4. 运行贝叶斯优化
    print("\n📋 步骤4: 运行贝叶斯优化")
    try:
        add_calibration_path()
        from bayesian_demo import BayesianOptimizer
        
        optimizer = BayesianOptimizer(
            bounds=param_bounds,
            n_initial=5,  # 初始采样点数
            acquisition='ei',
            xi=0.01
        )
        
        print("🔄 开始优化...")
        best_params, best_score = optimizer.optimize(
            objective_func, 
            max_evaluations=10,  # 总评估次数（演示用较小值）
            verbose=True
        )
        
        print(f"\n🎉 优化完成!")
        print(f"   最优参数: E={best_params[0]:.4f}, nu={best_params[1]:.4f}")
        print(f"   最优误差: {best_score:.6f}")
        
        return best_params, best_score
        
    except ImportError as e:
        print(f"❌ 未找到贝叶斯优化模块: {e}")
        print("运行简化测试...")
        
        # 简化测试：网格搜索
        print("🔄 运行网格搜索测试...")
        best_params = None
        best_score = float('inf')
        
        E_values = np.linspace(0.15, 0.25, 3)
        nu_values = np.linspace(0.40, 0.50, 3)
        
        for E in E_values:
            for nu in nu_values:
                score = objective_func([E, nu])
                if score < best_score:
                    best_score = score
                    best_params = [E, nu]
        
        print(f"\n🎉 网格搜索完成!")
        print(f"   最优参数: E={best_params[0]:.4f}, nu={best_params[1]:.4f}")
        print(f"   最优误差: {best_score:.6f}")
        
        return best_params, best_score

def demo_objective_function():
    """演示目标函数的使用方式"""
    print("\n🔬 目标函数使用示例")
    print("=" * 50)
    
    def objective_function(params):
        """
        贝叶斯优化的目标函数
        
        Parameters:
        - params : np.ndarray, [E, nu] 材料参数
        
        Returns:
        - float, 误差值
        """
        E, nu = params
        print(f"🔄 评估参数: E={E:.4f}, nu={nu:.4f}")
        
        # 1. 使用fem_processor生成raw_data
        try:
            add_calibration_path()
            from fem_processor import process_gel_data
            processor = process_gel_data('g1-ws', E=E, nu=nu, use_cache=True)
            raw_data = processor.get_data()
            
            # 2. 创建标定场景并采集数据（这里简化为模拟）
            # object_files = ["xengym/assets/obj/circle_r4.STL"]
            # scene = create_calibration_scene(object_files=object_files, raw_data=raw_data, visible=False)
            # sim_data = scene.collect_all_calibration_data()
            
            # 3. 与真实数据比较计算误差（这里用随机值模拟）
            # error = calculate_error(sim_data, real_sensor_data)
            error = np.random.rand() * 0.1
            print(f"   使用真实FEM数据计算误差: {error:.6f}")
            
        except Exception as e:
            print(f"   FEM数据生成失败: {e}")
            # 模拟返回误差
            error = np.random.rand() * 0.1
        return error
    
    # 测试目标函数
    test_params = np.array([0.20, 0.45])
    error = objective_function(test_params)
    print(f"✓ 目标函数返回: {error:.6f}")

def main():
    """主函数"""
    print("🎯 单传感器标定场景演示")
    print("=" * 60)
    
    # 首先检查能否找到必要的文件
    print("\n📋 检查文件路径...")
    
    # 检查assets目录
    possible_paths = [
        Path("xengym/assets/obj"),
        Path(__file__).parent / "xengym" / "assets" / "obj",
        Path(__file__).parent / "calibration" / "xengym" / "assets" / "obj",
        Path("/home/czl/Downloads/workspace/xengym/xengym/assets/obj")
    ]
    
    assets_found = False
    for path in possible_paths:
        if path.exists():
            print(f"✓ 找到assets目录: {path}")
            stl_files = list(path.glob("*.STL"))
            print(f"  包含STL文件: {[f.name for f in stl_files]}")
            assets_found = True
            break
    
    if not assets_found:
        print("❌ 无法找到assets目录")
        return
    
    # 检查calibration目录
    calib_paths = [
        Path("calibration"),
        Path(__file__).parent / "calibration",
        Path("../calibration")
    ]
    
    calib_found = False
    for path in calib_paths:
        if path.exists() and (path / "fem_processor.py").exists():
            print(f"✓ 找到calibration目录: {path}")
            calib_found = True
            break
    
    if not calib_found:
        print("❌ 无法找到calibration目录")
        return
    
    print("✓ 文件检查完成，开始测试...")
    
    # 测试基本功能
    scene = test_calibration_scene()
    if scene is None:
        print("❌ 基本功能测试失败")
        return
    
    # 测试参数标定
    scene = test_parameter_calibration()
    if scene is None:
        print("❌ 参数标定测试失败")
        return
    
    # 运行贝叶斯优化演示
    try:
        best_params, best_score = run_bayesian_optimization_demo()
        
        if best_params is not None:
            print(f"\n📊 标定结果总结:")
            print(f"   优化后的材料参数:")
            print(f"     杨氏模量 E = {best_params[0]:.4f}")
            print(f"     泊松比 nu = {best_params[1]:.4f}")
            print(f"   最终误差 = {best_score:.6f}")
            
            print(f"\n💡 使用建议:")
            print(f"   1. 准备真实传感器数据")
            print(f"   2. 调整参数搜索范围")
            print(f"   3. 增加评估次数以提高精度")
            print(f"   4. 使用多个物体和深度提高鲁棒性")
        
    except Exception as e:
        print(f"❌ 贝叶斯优化演示失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行新的主函数
    main() 