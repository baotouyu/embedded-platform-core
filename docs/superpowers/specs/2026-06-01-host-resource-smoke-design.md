# host 资源使用冒烟示例设计

## 背景

主工程已经有第一版平台路径接口：

```text
platforms/include/ep_platform_paths.h
```

host/macOS 当前可以返回配置文件路径、资源根目录、图片路径、字体路径和主题路径。现在还缺一个很小的运行示例，证明这些路径不只是能拼出来，也能被 host 程序拿去访问实际资源文件。

## 目标

新增一个 host/macOS 资源冒烟程序，用最小方式验证：

- host 程序可以通过平台路径接口拿到图片、字体、主题资源路径。
- 这些路径指向仓库里的实际资源文件。
- host 程序可以通过现有文件组件打开并读取这些资源。
- CMake 可以单独构建这个冒烟程序。

## 不做什么

本次不做以下内容：

- 不显示图片。
- 不解码图片。
- 不加载真实字体。
- 不解析主题格式。
- 不封装 LVGL API。
- 不新增资源扫描、资源缓存或资源打包机制。
- 不改变现有 `ep_host_lvgl_demo` 和 `ep_host_lvgl_widgets_demo` 的行为。

## 方案

新增一个独立可执行程序：

```text
ep_host_resource_smoke
```

源码放在：

```text
platforms/host/posix/demos/resource_smoke_main.c
```

程序流程：

1. 调用 `ep_platform_image_path("smoke.txt", ...)` 获取图片资源路径。
2. 调用 `ep_platform_font_path("smoke.txt", ...)` 获取字体资源路径。
3. 调用 `ep_platform_theme_path("smoke.txt", ...)` 获取主题资源路径。
4. 用 `ep_file_open()` 打开每个路径。
5. 用 `ep_file_read()` 读取少量内容。
6. 校验每个文件内容不是空。
7. 全部通过时返回 `0`。

新增三个极小占位资源：

```text
resources/host/images/smoke.txt
resources/host/fonts/smoke.txt
resources/host/themes/smoke.txt
```

这些文件只是冒烟验证用的文本资源，不代表图片、字体或主题的正式格式。

## CMake 接入

在 `platforms/host/posix/CMakeLists.txt` 中新增：

```text
add_executable(ep_host_resource_smoke ...)
```

链接：

- `ep_components_file`
- `ep_platform_api`

同时编译 host 路径实现：

```text
paths/ep_host_platform_paths.c
```

这样资源冒烟程序不依赖 LVGL，不依赖 SDL2，也不要求 macOS arm64 才能构建。

## 测试

新增测试文件：

```text
tests/host_unit/test_host_resource_smoke.py
```

测试内容：

- 验证 `platforms/host/posix/CMakeLists.txt` 声明 `ep_host_resource_smoke`。
- 验证 demo 源文件存在，并使用平台路径接口和文件组件。
- 验证三个 host 占位资源存在且不是空文件。
- 通过 CMake 构建 `ep_host_resource_smoke`。
- 运行 `ep_host_resource_smoke`，要求返回 `0`。

## 错误处理

冒烟程序遇到以下情况直接返回非零错误码：

- 平台路径接口返回错误。
- 路径缓冲区不足。
- 资源文件无法打开。
- 文件读取失败。
- 资源文件为空。

错误码只用于冒烟测试定位，不作为公共 API。

## 后续方向

这个冒烟程序通过后，后面可以继续做两条线：

- UI 线：在 LVGL demo 里使用平台路径接口加载真实图片或字体。
- 工具线：增加资源拷贝、检查或打包脚本。

这两条线都应该作为单独 PR，不和本次冒烟示例混在一起。
