# 技术设计: 数据可视化查看器

## 1. 概述

本文档为 `data-viewer` 功能提供技术设计。该工具将是一个独立的Python应用程序，使用 `PyQt` 和 `pyqtgraph` 构建，用于浏览和分析 `xengym` 的采集数据。

## 2. 文件结构

新的可视化脚本将位于：
- `example/data_viewer.py`

该文件将包含实现可视化功能所需的所有代码。

## 3. 核心技术栈

- **GUI框架**: `PyQt5` 或 `PyQt6` 将用于构建应用程序的主窗口和控件。
- **绘图库**: `pyqtgraph` 将用于高效显示图像和2D散点图，因为它与PyQt集成良好且性能高。
- **图像处理**: `OpenCV-Python (cv2)` 用于处理图像颜色空间转换（BGR到RGB）。
- **数据处理**: `numpy` 和 `pickle` 将分别用于数据操作和文件加载。

## 4. 类结构

将设计一个主类 `DataViewer` 来管理整个应用程序。

```python
class DataViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        # 1. 初始化UI组件 (下拉菜单, 复选框, 绘图窗口)
        # 2. 连接UI信号到槽函数 (例如，当用户选择一个新对象时)
        # 3. 初始化数据加载逻辑

    def init_ui(self):
        # 创建主窗口布局、控件面板和绘图网格
        pass

    def populate_object_dropdown(self):
        # 扫描 xengym/data/obj/ 目录并填充对象下拉菜单
        pass

    def on_object_selected(self, object_name):
        # 当用户选择一个对象时，加载其轨迹并填充轨迹选择器
        pass

    def on_trj_selected(self, trj_name):
        # 当用户选择一个轨迹时，加载第一帧数据
        pass

    def load_frame_data(self, frame_index):
        # 从 .pkl 文件加载特定帧的数据
        # 返回一个包含所有图像和节点数据的字典
        pass

    def update_visuals(self, data):
        # 根据加载的数据更新所有图像和绘图
        # 处理BGR到RGB的转换
        pass

    def keyPressEvent(self, event):
        # 监听空格键事件以切换到下一帧
        pass

    def next_frame(self):
        # 增加帧计数器并加载下一帧数据
        pass
```

## 5. UI 布局

- **主窗口**: 将使用 `QMainWindow`。
- **中央控件**: 一个 `QWidget` 将包含一个 `QVBoxLayout`。
- **控件面板**: 一个 `QHBoxLayout` 将包含：
  - `QComboBox` 用于选择对象。
  - `QComboBox` 用于选择轨迹。
  - `QCheckBox` 分别用于 `sensor_0` 和 `sensor_1`。
  - `QLabel` 用于显示当前帧号。
- **可视化网格**: 一个 `pyqtgraph.GraphicsLayoutWidget` 将用于以网格形式组织所有图像和绘图，从而轻松实现并排比较。

## 6. 数据流

1.  **启动**: `DataViewer` 初始化，扫描 `xengym/data/obj` 目录，并填充对象下拉菜单。
2.  **选择对象**: 用户从下拉菜单中选择一个对象。`on_object_selected` 被触发，扫描所选对象的目录以查找所有轨迹（`trj_*`），并填充轨迹下拉菜单。
3.  **选择轨迹**: 用户选择一个轨迹。`on_trj_selected` 被触发，将帧索引重置为0，并调用 `load_frame_data(0)`。
4.  **加载数据**: `load_frame_data` 从相应的 `.pkl` 文件加载数据。
5.  **更新显示**: `update_visuals` 接收数据，并使用 `pyqtgraph` 的 `setImage()` 和 `setData()` 方法更新所有可见的图像项和绘图项。对于BGR图像，在显示前使用 `cv2.cvtColor` 进行转换。
6.  **下一帧**: 用户按空格键，`next_frame` 增加帧索引，并重复步骤4-5。

## 7. 核心逻辑实现

- **帧切换**: `keyPressEvent` 将捕获键盘事件。如果按下的是 `Qt.Key_Right`，则调用 `next_frame`。如果按下的是 `Qt.Key_Left`，则调用 `prev_frame`。
- **动画播放**: “播放/暂停”按钮将调用 `toggle_animation` 方法。该方法将启动或停止一个 `QTimer`。当 `QTimer` 运行时，它将以设定的间隔（例如100毫秒）重复调用 `next_frame` 方法。
- **传感器对比**: UI将为每个传感器和数据类型创建单独的 `pyqtgraph` 视图。`QCheckBox` 的状态将决定哪些视图是可见的。如果 `sensor_0` 的复选框被选中，其对应的视图将被填充数据；如果未选中，则视图将被清空或隐藏。
- **颜色转换**: 在 `update_visuals` 方法中，从 `data` 字典中检索到的 `rectify_real`、`diff_real` 和 `depth_real` 图像在传递给 `pyqtgraph` 之前，将使用 `cv2.cvtColor(image, cv2.COLOR_BGR2RGB)` 进行转换。
