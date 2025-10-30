# 任务列表: 数据可视化查看器

## 阶段 1: 项目设置和基础UI

- [ ] **任务 1.1**: 在 `example/` 目录下创建一个新文件 `data_viewer.py`。
- [ ] **任务 1.2**: 导入所有必要的库 (`PyQt`, `pyqtgraph`, `cv2`, `numpy`, `os`, `pickle`)。
- [ ] **任务 1.3**: 创建主应用程序类 `DataViewer(QMainWindow)`。
- [ ] **任务 1.4**: 设置主窗口，包括标题、大小和中央布局。
- [ ] **任务 1.5**: 创建控件面板，并添加以下UI组件：
    - [ ] `QComboBox` 用于选择对象 (`object_combo`)。
    - [ ] `QComboBox` 用于选择轨迹 (`trj_combo`)。
    - [ ] `QCheckBox` 用于 `sensor_0`。
    - [ ] `QCheckBox` 用于 `sensor_1`。
    - [ ] `QLabel` 用于显示帧号 (`frame_label`)。
    - [ ] `QPushButton` 用于“上一帧” (`prev_button`)。
    - [ ] `QPushButton` 用于“播放/暂停” (`play_pause_button`)。
- [ ] **任务 1.6**: 在主窗口中添加一个 `pyqtgraph.GraphicsLayoutWidget` 用于显示可视化内容。

## 阶段 2: 数据加载和UI逻辑

- [ ] **任务 2.1**: 实现 `populate_object_dropdown` 方法，扫描 `xengym/data/obj` 目录并填充对象下拉菜单。
- [ ] **任务 2.2**: 将 `object_combo` 的 `currentIndexChanged` 信号连接到 `on_object_selected` 槽函数。
- [ ] **任务 2.3**: 实现 `on_object_selected` 方法，根据所选对象填充 `trj_combo`。
- [ ] **任务 2.4**: 将 `trj_combo` 的 `currentIndexChanged` 信号连接到 `on_trj_selected` 槽函数。
- [ ] **任务 2.5**: 实现 `on_trj_selected` 方法，加载所选轨迹的第一帧数据。
- [ ] **任务 2.6**: 实现 `load_frame_data(frame_index)` 方法，从 `.pkl` 文件中读取并返回数据。

## 阶段 3: 可视化实现

- [ ] **任务 3.1**: 在 `GraphicsLayoutWidget` 中为每个数据项（图像和节点图）创建 `pyqtgraph` 的 `ImageItem` 和 `PlotItem`。
- [ ] **任务 3.2**: 实现 `update_visuals(data)` 方法，用加载的数据更新所有 `ImageItem` 和 `PlotItem`。
- [ ] **任务 3.3**: 在 `update_visuals` 中，为BGR格式的图像（`rectify_real`, `diff_real`, `depth_real`）添加 `cv2.cvtColor` 转换逻辑。
- [ ] **任务 3.4**: 将传感器复选框的 `stateChanged` 信号连接到 `update_visuals`，以控制相应视图的显示和隐藏。

## 阶段 4: 交互功能

- [ ] **任务 4.1**: 实现 `keyPressEvent` 来处理键盘输入。
    - [ ] 按下右方向键 (`Qt.Key_Right`) 时调用 `next_frame`。
    - [ ] 按下左方向键 (`Qt.Key_Left`) 时调用 `prev_frame`。
- [ ] **任务 4.2**: 实现 `next_frame` 方法，处理帧索引的增加和循环。
- [ ] **任务 4.3**: 实现 `prev_frame` 方法，处理帧索引的减少和循环。
- [ ] **任务 4.4**: 将 `prev_button` 的 `clicked` 信号连接到 `prev_frame`。
- [ ] **任务 4.5**: 实现 `toggle_animation` 方法。
    - [ ] 创建一个 `QTimer` 实例。
    - [ ] `toggle_animation` 方法可以启动/停止计时器。
    - [ ] 将计时器的 `timeout` 信号连接到 `next_frame`。
- [ ] **任务 4.6**: 将 `play_pause_button` 的 `clicked` 信号连接到 `toggle_animation`。

## 阶段 5: 收尾工作

- [ ] **任务 5.1**: 添加必要的错误处理（例如，当数据目录或文件不存在时）。
- [ ] **任务 5.2**: 编写代码注释和文档字符串，解释关键部分的逻辑。
- [ ] **任务 5.3**: 在 `if __name__ == "__main__":` 块中添加启动应用程序的代码。
- [ ] **任务 5.4**: 对代码进行最终测试，确保所有功能都按预期工作。
