# cJSON 和 SQLite 第三方库接入设计

## 背景

主工程已经有第三方库目录边界：

```text
third_party/external/
third_party/prebuilt/
```

当前 EasyLogger 作为源码快照接入，LVGL 作为 host/macOS 预编译包接入。接下来需要把 cJSON 和 SQLite 接入主工程，为后续菜谱解析、用户数据、本地数据库和网络 JSON 数据处理做准备。

## 上游版本

本次选择当前稳定版本：

| 库 | 版本 | 来源 |
| --- | --- | --- |
| cJSON | `v1.7.19` | GitHub `DaveGamble/cJSON` release |
| SQLite | `3.53.1` | SQLite 官方 download 页面 `sqlite-amalgamation-3530100.zip` |

SQLite 使用官方 amalgamation 产物，只接入 `sqlite3.c`、`sqlite3.h`、`sqlite3ext.h` 和官方声明文件。这样主工程不用引入完整 SQLite 源码树。

## 目标

本次目标是把两个第三方库正规接入主工程：

- cJSON 可以作为 CMake 静态库目标被链接。
- SQLite 可以作为 CMake 静态库目标被链接。
- host/macOS 能编译并运行最小 smoke 测试。
- 文档能说明源码来源、版本和后续升级方式。

## 不做什么

本次不做以下内容：

- 不封装 cJSON API。
- 不封装 SQLite API。
- 不新增 JSON 组件。
- 不新增数据库组件。
- 不做菜谱解析。
- 不做用户数据存储。
- 不设计数据库 schema。
- 不处理真实平台 SQLite 持久化策略。
- 不把 cJSON 或 SQLite 改成平台适配层的一部分。

## 目录设计

新增源码快照目录：

```text
third_party/external/cjson/
third_party/external/sqlite/
```

cJSON 目录保留：

```text
third_party/external/cjson/cJSON.c
third_party/external/cjson/cJSON.h
third_party/external/cjson/LICENSE
third_party/external/cjson/VERSION.txt
```

SQLite 目录保留：

```text
third_party/external/sqlite/sqlite3.c
third_party/external/sqlite/sqlite3.h
third_party/external/sqlite/sqlite3ext.h
third_party/external/sqlite/LICENSE.md
third_party/external/sqlite/VERSION.txt
```

`VERSION.txt` 记录版本、来源 URL 和同步时间，方便以后升级时追踪。

## CMake 设计

新增：

```text
third_party/CMakeLists.txt
```

根 `CMakeLists.txt` 增加：

```cmake
add_subdirectory(third_party)
```

第三方库目标：

```text
ep_thirdparty_cjson
ep_thirdparty_sqlite
```

cJSON 目标：

- 静态库。
- 编译 `third_party/external/cjson/cJSON.c`。
- 公开 include 目录 `third_party/external/cjson`。

SQLite 目标：

- 静态库。
- 编译 `third_party/external/sqlite/sqlite3.c`。
- 公开 include 目录 `third_party/external/sqlite`。
- 先使用 SQLite 默认配置，不增加自定义裁剪宏。

## 测试设计

新增 host 单元测试：

```text
tests/host_unit/test_thirdparty_cjson_sqlite.py
```

测试内容：

1. 检查第三方源码文件存在。
2. 检查 `VERSION.txt` 记录版本。
3. 检查 CMake 目标存在。
4. 用 CMake 构建一个最小 smoke 程序：
   - cJSON：解析 `{"name":"host"}`，读取 `name` 字段。
   - SQLite：打开 `:memory:`，执行 `create table t(id integer);`。

这个测试只证明“源码快照能被主工程消费”，不验证业务逻辑。

## 文档同步

更新：

```text
docs/architecture/repository-layout.md
docs/architecture/project-overview.md
docs/development/roadmap.md
```

文档需要说明：

- cJSON 和 SQLite 属于 `third_party/external/` 源码快照。
- 主工程当前只暴露第三方 CMake 目标。
- 业务层后续可以选择直接使用第三方 API，或者再补 `components/recipe_parser`、`components/user_data` 等平台无关组件。

## 后续方向

cJSON 接入后，适合继续做：

- 菜谱 JSON 解析组件。
- 网络 JSON 数据解析。
- 配置导入导出。

SQLite 接入后，适合继续做：

- 用户数据组件。
- 本地收藏、历史记录、设备状态缓存。
- host 上的本地数据库 smoke。

真实平台适配时，需要再根据平台能力决定 SQLite 是否启用文件持久化，或者只启用内存数据库。
