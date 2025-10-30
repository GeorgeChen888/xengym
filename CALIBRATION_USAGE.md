# 单传感器标定场景使用说明

## 概述

这个标定场景专门用于材料参数的贝叶斯优化，支持单传感器和多物体的法向按压数据采集。

## 主要功能

### 1. 标定场景 (CalibrationScene)

位置：`xengym/render/calibScene.py`

主要特性：
- 支持动态更新FEM材料参数
- 多物体标定数据采集
- 标准化的数据输出格式
- 专为贝叶斯优化设计

### 2. 标定示例 (calibration_example.py)

主要功能：
- 基本功能测试
- 参数标定演示
- 贝叶斯优化集成
- 完整的使用流程

## 使用方法

### 1. 基本使用

```python
from xengym.render.calibScene import create_calibration_scene

# 准备物体文件
object_files = [
    "xengym/assets/obj/circle_r4.STL",
    "xengym/assets/obj/circle_r5.STL"
]

# 创建标定场景
scene = create_calibration_scene(
    object_files=object_files,
    visible=False,  # 不显示窗口
    sensor_visible=False
)

# 采集标定数据
calibration_data = scene.collect_all_calibration_data()
```

### 2. 使用特定材料参数

```python
# 使用指定的材料参数进行标定
E = 0.2  # 杨氏模量
nu = 0.45  # 泊松比

calibration_data = scene.calibrate_with_parameters(E, nu)
```

### 3. 集成到贝叶斯优化

```python
def objective_function(params):
    E, nu = params
    
    # 使用标定场景采集数据
    sim_data = scene.calibrate_with_parameters(E, nu)
    
    # 计算与真实数据的误差
    error = calculate_calibration_error(sim_data, real_data)
    
    return error

# 在贝叶斯优化中使用
best_params, best_score = optimizer.optimize(objective_function, ...)
```

## 数据格式

标定数据采用三层字典结构：

```
{
    "object_name": {
        "0.1mm": {
            "depth_field": (700, 400),           # 深度场数据
            "marker_displacement": (20, 11, 2)   # Marker XY位移
        },
        "0.2mm": { ... },
        ...
    }
}
```

## 关键参数

### 按压深度
- 默认深度：[0.1, 0.2, 0.3, 0.4, 0.5, 0.6] mm
- 可在 `CalibrationScene` 中修改 `press_depths`

### 数据尺寸
- 深度场：700×400
- Marker位移：20×11×2

### 材料参数范围
- 杨氏模量 E：通常在 0.1-0.4 MPa
- 泊松比 nu：通常在 0.3-0.5

## 依赖关系

1. **fem_processor.py** - FEM数据处理
2. **bayesian_demo.py** - 贝叶斯优化算法
3. **xengym.render.calibScene** - 标定场景
4. **xengym.fem.simulation** - FEM仿真

## 示例运行

```bash
# 运行标定示例
python calibration_example.py

# 运行贝叶斯优化演示
python bayesian_calibration_demo.py
```

## 注意事项

1. **物体文件**：确保STL文件存在于 `xengym/assets/obj/` 目录
2. **FEM数据**：首次运行时会生成缓存，后续运行会更快
3. **内存使用**：大量物体或深度数据可能占用较多内存
4. **计算时间**：FEM计算可能较慢，建议使用缓存

## 扩展功能

### 1. 添加新物体
```python
# 在创建场景时添加新的物体文件
object_files.append("xengym/assets/obj/new_object.STL")
```

### 2. 自定义按压深度
```python
# 修改场景的按压深度
scene.press_depths = [0.1, 0.3, 0.5]  # 自定义深度
```

### 3. 多目标优化
```python
# 可以扩展为多目标优化
def multi_objective_function(params):
    E, nu = params
    sim_data = scene.calibrate_with_parameters(E, nu)
    
    # 计算多个误差指标
    error1 = calculate_depth_error(sim_data, real_data)
    error2 = calculate_marker_error(sim_data, real_data)
    
    return [error1, error2]
```

## 故障排除

1. **找不到物体文件**：检查路径是否正确
2. **FEM计算失败**：检查材料参数是否合理
3. **内存不足**：减少物体数量或深度数量
4. **缓存问题**：删除缓存目录重新生成