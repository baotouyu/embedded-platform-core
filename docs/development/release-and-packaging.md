# 发布和打包流程

本文说明 `embedded-platform-core` 后续发布、打包和平台产物的边界。当前先定义规则，不新增打包脚本。

## 基本原则

- 主工程发布公共框架代码、平台无关组件、host 验证程序和小型第三方产物。
- 主工程不提交大型厂商 SDK。
- 每个平台的最终产物可以不同，但必须能说明可执行文件、配置文件、资源目录和第三方库来自哪里。
- LVGL 这类平台差异明显的库，优先通过 `third_party/prebuilt/<name>/<platform>` 消费产物。
- 发布流程先从 host/macOS 跑通，再扩展到真实 RTOS 和 Linux 平台。

## host/macOS 产物

host/macOS 是当前主要开发和验证平台。

建议发布产物包括：

```text
build/platforms/host/posix/ep_platform_host_posix
build/platforms/host/posix/ep_host_resource_smoke
build/platforms/host/posix/ep_host_lvgl_demo
build/platforms/host/posix/ep_host_lvgl_widgets_demo
config/profiles/host.cfg
resources/host/
resources/common/
third_party/prebuilt/lvgl/host_macos/
```

说明：

- `ep_platform_host_posix` 是 host 框架主程序。
- `ep_host_resource_smoke` 用于验证资源路径和文件读取。
- `ep_host_lvgl_demo` 和 `ep_host_lvgl_widgets_demo` 用于验证 host LVGL 窗口。
- `config/profiles/host.cfg` 是 host 默认配置文件。
- `resources/host/` 放 host 调试资源。
- `resources/common/` 放多平台可复用资源。
- `third_party/prebuilt/lvgl/host_macos/` 是 host/macOS 使用的 LVGL 预编译包。

host/macOS 第一阶段可以不做安装包，先以构建目录产物加配置和资源目录的方式验证。

当前提供 host/macOS 发布包脚本：

```bash
python3 tools/scripts/package_host.py --clean
```

默认输出：

```text
out/packages/host_macos/
```

目录结构：

```text
out/packages/host_macos/bin/
out/packages/host_macos/config/profiles/host.cfg
out/packages/host_macos/resources/host/
out/packages/host_macos/resources/common/
out/packages/host_macos/manifest.txt
```

这个脚本只生成本地目录包，不做压缩包、签名或安装器。

当前脚本生成的是 host 运行包，不复制 `third_party/prebuilt/lvgl/host_macos/`。host 可执行文件已经静态链接 LVGL；后续如果需要源码构建包或 SDK 同步包，再单独扩展脚本。

## 匠芯创 Luban Lite 产物

匠芯创 Luban Lite 后续属于 RTOS 类平台。

建议产物边界包括：

```text
platforms/rtos/luban_lite/
config/profiles/luban_lite.cfg
resources/luban_lite/
resources/common/
third_party/prebuilt/lvgl/luban_lite/
vendor/
```

说明：

- `platforms/rtos/luban_lite/` 放主工程侧平台适配代码。
- `config/profiles/luban_lite.cfg` 放 Luban Lite 平台启动配置。
- `resources/luban_lite/` 放 Luban Lite 专用资源。
- `resources/common/` 放公共资源。
- `third_party/prebuilt/lvgl/luban_lite/` 放从 Luban Lite SDK 或独立 LVGL 仓库产出的头文件、静态库和 manifest。
- `vendor/` 只作为厂商 SDK 边界。大型 SDK 不直接提交进主工程。

Luban Lite 的最终固件或 SDK app 产物应由对应 SDK 构建系统产出。主工程负责提供公共代码、平台适配代码和需要同步进去的资源/库边界。

## 全志 Linux 产物

全志 Linux 后续属于 Linux 用户态平台。

建议产物边界包括：

```text
platforms/linux/tina/
config/profiles/tina.cfg
resources/tina/
resources/common/
third_party/prebuilt/lvgl/tina/
```

说明：

- `platforms/linux/tina/` 放全志 Linux 平台适配代码。
- `config/profiles/tina.cfg` 放该平台运行配置。
- `resources/tina/` 放该平台专用资源。
- `third_party/prebuilt/lvgl/tina/` 放该平台 LVGL 预编译产物。
- Linux 侧优先使用标准用户态接口，不引入伪厂商 SDK 层。

全志 Linux 的发布产物一般是 Linux 可执行文件、配置文件、资源目录和需要随程序部署的第三方库产物。

## 配置文件规则

平台配置文件放在：

```text
config/profiles/<platform>.cfg
```

示例：

```text
config/profiles/host.cfg
config/profiles/luban_lite.cfg
config/profiles/tina.cfg
```

配置文件只描述启动参数、功能开关和少量平台运行参数。大型资源、数据库文件、厂商 SDK 配置不塞进这里。

## 资源目录规则

资源目录按公共资源和平台资源拆分：

```text
resources/common/
resources/host/
resources/luban_lite/
resources/tina/
```

规则：

- `resources/common/` 放所有平台都可复用的图片、字体、主题等资源。
- `resources/<platform>/` 放平台专用资源。
- 平台代码通过 `ep_platform_resource_root_path()` 和相关路径接口获取资源位置。
- UI 代码不要硬编码 `resources/host`、`resources/luban_lite` 或 `resources/tina`。

## 第三方库规则

源码快照放在：

```text
third_party/external/
```

预编译包放在：

```text
third_party/prebuilt/
```

当前已经使用：

```text
third_party/external/EasyLogger
third_party/external/cjson
third_party/external/sqlite
third_party/prebuilt/lvgl/host_macos
```

规则：

- cJSON 和 SQLite 作为源码快照接入主工程。
- LVGL 按平台产出预编译包，每个平台可以有自己的 `lvgl.a`、头文件和配置。
- 主工程只消费 LVGL 产物，不直接维护所有平台的 LVGL 源码配置。
- 预编译包必须带版本和能力说明，方便判断图片解码、字体、本地文件系统等能力是否开启。

## 发布前检查

每次准备发布或同步平台产物前，至少检查：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
```

host/macOS 还应该手动验证：

```bash
./build/platforms/host/posix/ep_platform_host_posix
./build/platforms/host/posix/ep_host_resource_smoke
./build/platforms/host/posix/ep_host_lvgl_demo
```

真实平台后续需要增加自己的编译命令、烧录命令和冒烟测试命令。