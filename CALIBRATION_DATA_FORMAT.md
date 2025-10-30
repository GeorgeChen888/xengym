# 标定数据格式说明

## 简化数据格式

根据需求，标定数据格式已简化，只包含两个核心数据：

### 单个深度数据格式

```python
{
    'depth_field': np.ndarray,           # 形状: (700, 400), 类型: float32, 深度场数据
    'marker_displacement': np.ndarray    # 形状: (20, 11, 2), 类型: float32, Marker XY位移
}
```

### 完整标定数据格式

```python
{
    'object_name': {
        '0.1mm': {
            'depth_field': np.ndarray,           # (700, 400)
            'marker_displacement': np.ndarray    # (20, 11, 2)
        },
        '0.2mm': {
            'depth_field': np.ndarray,           # (700, 400)
            'marker_displacement': np.ndarray    # (20, 11, 2)
        },
        '0.3mm': { ... },
        '0.4mm': { ... },
        '0.5mm': { ... },
        '0.6mm': { ... }
    }
}
```

## 数据说明

### depth_field (深度场)
- **形状**: (700, 400) - 高度700像素，宽度400像素
- **数据类型**: np.float32
- **单位**: mm (毫米)
- **含义**: 传感器表面的侵入深度分布，正值表示物体压入传感器的深度

### marker_displacement (Marker位移场)
- **形状**: (20, 11, 2) - 20行11列的网格，每个点有XY两个位移分量
- **数据类型**: np.float32
- **单位**: mm (毫米)
- **含义**: 传感器表面Marker点的XY平面位移，相对于无接触时的初始位置

## 使用示例

```python
from xengym.render.calibScene import create_calibration_scene

# 创建场景
scene = create_calibration_scene(
    object_files=["path/to/object.STL"],
    raw_data=raw_data
)

# 采集单个深度数据
scene.set_current_object("object")
data = scene.collect_data_for_depth(0.2)

print(f"深度场形状: {data['depth_field'].shape}")           # (700, 400)
print(f"Marker位移形状: {data['marker_displacement'].shape}")  # (20, 11, 2)

# 采集完整标定数据
calibration_data = scene.collect_all_calibration_data()
```

## 贝叶斯优化中的使用

```python
def objective_function(params):
    E, nu = params
    
    # 1. 生成对应材料参数的raw_data
    raw_data = generate_fem_data(E, nu)
    
    # 2. 创建场景并采集仿真数据
    scene = create_calibration_scene(object_files=[...], raw_data=raw_data)
    sim_data = scene.collect_all_calibration_data()
    
    # 3. 计算与真实数据的误差
    error = 0.0
    for obj_name, obj_data in sim_data.items():
        for depth_key, depth_data in obj_data.items():
            # 比较深度场
            depth_error = np.mean((depth_data['depth_field'] - real_data[obj_name][depth_key]['depth_field'])**2)
            # 比较Marker位移
            marker_error = np.mean((depth_data['marker_displacement'] - real_data[obj_name][depth_key]['marker_displacement'])**2)
            error += depth_error + marker_error
    
    return error
```

## 数据访问

```python
# 访问特定物体、特定深度的数据
circle_r4_02mm_depth = calibration_data['circle_r4']['0.2mm']['depth_field']
circle_r4_02mm_marker = calibration_data['circle_r4']['0.2mm']['marker_displacement']

# 遍历所有数据
for obj_name, obj_data in calibration_data.items():
    print(f"物体: {obj_name}")
    for depth_key, depth_data in obj_data.items():
        print(f"  深度: {depth_key}")
        print(f"    深度场: {depth_data['depth_field'].shape}")
        print(f"    Marker位移: {depth_data['marker_displacement'].shape}")
``` 