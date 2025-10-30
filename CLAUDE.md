# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**xengym** 是一个名为"Xense Simulator"的高级仿真平台，专为机器人学和物理仿真设计，特别专注于触觉传感和可变形物体交互。该项目结合了机器人仿真、有限元方法(FEM)物理和传感器仿真。

## 核心架构

### 主要入口点
- **主入口**: `xengym/main.py` - 包含 `main()` 函数，驱动 `xengym-demo` 控制台命令
- **控制台命令**: `xengym-demo` (在 setup.py 的 entry_points 中定义)

### 核心模块结构
```
xengym/
├── __init__.py          # 包初始化，导出 Xensim 和 main
├── main.py             # 演示应用程序的主入口点
├── assets/             # 静态资源 (3D模型、URDF文件、FEM数据)
├── ezgym/              # 高级环境包装器
├── fem/                # 有限元方法仿真组件
└── render/             # 渲染和可视化组件
```

## 开发命令

### 构建和安装
```bash
# 安装包
pip install -e .

# 运行演示
xengym-demo

# 从源码构建
python setup.py build
python setup.py install
```

### 规范驱动的开发流程
项目使用 Kiro 风格的规范驱动开发：
```bash
# 初始化项目指导
kiro steering

# 创建规范
kiro spec-init "[feature-description]"
kiro spec-requirements [feature-name]
kiro spec-design [feature-name]
kiro spec-tasks [feature-name]

# 检查进度
kiro spec-status [feature-name]
```

## 关键组件

### FEM 模块 (`xengym/fem/`)
- **simulation.py**: 主FEM求解器，包含网格处理和物理仿真
- **simpleCSR.py**: 简单CSR(压缩稀疏行)实现
- 处理可变形材料仿真，包含邻域计算和平滑处理

### 渲染模块 (`xengym/render/`)
- **robotScene.py**: 支持URDF的主要机器人仿真场景
- **sensorScene.py**: 触觉传感器仿真场景
- **sensorSim.py**: VecTouch传感器仿真实现
- **calibScene.py**: 用于材料参数优化的校准场景
- **simpleScene.py**: 简化场景实现

### 资源管理 (`xengym/assets/`)
- **data/**: FEM仿真数据文件(.npz格式)
- **obj/**: 3D物体文件(.STL, .obj格式)
- **panda/**: Franka Panda机器人URDF和网格文件

## 依赖和框架

### 核心依赖
- **Python 3.9+**: 主要语言
- **numpy<=1.26.4**: 核心数值计算库
- **xensesdk.ezgl**: 自定义3D图形和仿真框架
- **cryptography**: 许可证验证和安全功能

### 重要配置
- **包名**: xengym
- **版本**: v0.2.0
- **Python要求**: 3.9+
- **许可证**: MIT

## 开发注意事项

### 资源管理
- 所有资源在安装期间自动打包
- 资源路径应使用 `xengym/__init__.py` 中的 `ASSET_DIR` 常量
- FEM数据文件使用.npz格式以实现高效加载

### 代码结构
- 模块化设计，FEM、渲染和仿真之间清晰分离
- 部分文件包含中文注释和文档
- 文档和代码中混合使用英文和中文

### 示例用法
项目在 `example/` 目录中包含全面的示例：
- **demo_dif_object.py**: 交互式机器人仿真
- **data_collection.py**: 多进程数据收集
- **calibration_example.py**: 材料参数校准
- **simple_contact_demo.py**: 基本接触仿真

## 关键功能

### 机器人仿真
- Franka Panda机器人仿真，支持URDF
- 关节控制和限制管理
- 实时3D可视化

### 触觉传感器仿真
- VecTouch传感器仿真，基于标记的反馈
- 力和接触可视化
- 基于FEM的可变形材料交互

### 校准系统
- 通过贝叶斯方法进行材料参数优化
- 多目标校准支持
- 标准化数据收集格式