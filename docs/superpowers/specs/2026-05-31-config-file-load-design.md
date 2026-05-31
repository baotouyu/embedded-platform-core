# Config 文件加载设计

## 背景

当前工程已经有两个相关基础能力：

- `components/config`：提供内存 key/value 配置表，支持 `int`、`bool`、`string` 三类值。
- `components/file`：提供平台无关文件访问接口，host 上已经用 C 标准库文件接口实现。

下一步可以让 config 从文件加载默认配置。这样 Mac/Ubuntu 上可以先跑通“配置文件 -> config 内存表”的链路，后续到
Luban-Lite、RT-Thread 或真实板子时，再把 file 后端映射到目标平台文件系统或存储介质。

本阶段仍然保持小步适配：只做读取配置文件，不做保存、不做热加载、不接 framework 自动初始化。

## 目标

- 在 `components/config/include/ep_config.h` 新增文件加载接口：

```c
int ep_config_load_file(const char *path);
```

- `ep_config_load_file()` 通过 `components/file` 读取文本配置文件。
- 配置文件使用简单、可手写、可测试的行格式：

```text
int log.level=3
bool feature.enabled=true
string network.server=127.0.0.1
```

- 加载成功后，配置写入现有内存表，继续通过已有 get 接口读取。
- 公共头文件仍然保持平台无关，不包含 `ep_file.h`、POSIX、RT-Thread 或 SDK 头文件。
- host/Mac/Ubuntu 上用单元测试验证解析、覆盖、错误路径和 CMake 链接。

## 非目标

- 不保存配置到文件。
- 不实现配置热加载。
- 不解析 JSON、INI、YAML 或 TOML。
- 不支持 section、include、数组、结构体、浮点数或二进制 blob。
- 不支持注释行和行尾注释。
- 不自动创建默认配置文件。
- 不把 config 文件加载接入 `ep_framework_init()`。
- 不适配 Luban-Lite、RT-Thread 或真实 flash/NVRAM。
- 不改变现有 `set/get` API 的语义。

## 方案比较

### 方案一：新增 `ep_config_load_file()`，内部复用 `components/file`

config 暴露一个路径加载接口，内部调用 `ep_file_open/read/close` 读取文本，再复用现有
`ep_config_set_int()`、`ep_config_set_bool()`、`ep_config_set_string()` 写入内存表。

优点：

- API 很小，上层只需要传路径。
- 复用刚建立的 file 抽象，不直接依赖 POSIX。
- 公共头文件不需要暴露 file 细节。
- Mac/Ubuntu 上容易测试，后续换平台 file 后端时 config 不需要改 API。

缺点：

- config 组件开始依赖 file 组件，CMake 链接关系需要补上。
- 第一版只能加载小文件，需要固定缓冲区上限。

### 方案二：由应用层读取文件，再逐项调用 set

config 不新增文件接口，应用层自己读文件、解析并调用 `ep_config_set_*()`。

优点：

- config 组件继续保持纯内存表。
- 不引入 config -> file 的依赖。

缺点：

- 每个应用都要重复解析逻辑。
- 后续平台适配时，上层代码更容易直接依赖 POSIX 或 RTOS 文件接口。
- 不利于形成统一配置入口。

### 方案三：直接接入 JSON/INI 解析库

配置文件使用成熟格式，比如 JSON 或 INI。

优点：

- 格式更通用。
- 后续表达复杂配置更方便。

缺点：

- 第一版目标太大，会引入第三方依赖或较复杂解析器。
- 当前 config 只支持简单 key/value，复杂格式暂时用不上。
- 增加移植到嵌入式平台的成本。

## 推荐方案

采用方案一：新增 `ep_config_load_file()`，内部复用 `components/file`。

理由：

- 当前已经有 file 组件，正好验证组件之间的真实依赖方式。
- config 的上层 API 仍然简单，后续 app/core 只依赖 config，不需要知道文件怎么读。
- 文件格式先保持最小，避免过早引入 JSON/INI 和第三方库。
- 这个能力可以在 Mac 上跑通，再迁移到 Ubuntu 和芯片平台。

## 公共 API 设计

`components/config/include/ep_config.h` 增加：

```c
int ep_config_load_file(const char *path);
```

行为：

- 成功读取并解析完整文件后返回 `EP_OK`。
- `path == 0` 或空路径返回 `EP_ERR_INVAL`。
- config 未初始化时返回 `EP_ERR_UNSUPPORTED`。
- 文件无法打开或读取失败时返回 `EP_ERR_UNSUPPORTED`。
- 文件内容格式错误、key 非法、value 非法时返回 `EP_ERR_INVAL`。
- 内存配置表容量不足时返回 `EP_ERR_BUSY`。

头文件要求：

- `ep_config.h` 仍然不包含 `ep_file.h`。
- `ep_config.h` 仍然不包含平台原生头文件。
- `ep_config_load_file()` 的返回码含义通过文档和测试固定，不在头文件里引入新错误码。

## 文件格式

第一版每行一个配置项：

```text
<type> <key>=<value>
```

支持类型：

```text
int
bool
string
```

示例：

```text
int log.level=3
bool feature.enabled=true
bool feature.disabled=false
string network.server=127.0.0.1
```

解析规则：

- 类型和 key 之间必须有一个空格。
- key 和 value 之间必须有 `=`。
- key 不能为空，继续复用现有 key 长度限制。
- value 不能为空。
- 行尾 `\n` 和 Windows 风格 `\r\n` 都支持。
- 文件最后一行可以没有换行。
- 空行不支持，出现空行返回 `EP_ERR_INVAL`。
- 注释不支持，出现 `# xxx` 这种行返回 `EP_ERR_INVAL`。
- 行首、行尾额外空格不做自动裁剪，避免第一版规则含糊。

## 类型解析

### int

格式：

```text
int <key>=<decimal>
```

规则：

- 只支持十进制整数。
- 支持负数。
- 不支持十六进制、浮点数、空格、单位后缀。
- 解析失败或溢出返回 `EP_ERR_INVAL`。
- 成功后调用 `ep_config_set_int()`。

示例：

```text
int log.level=3
int motor.offset=-12
```

### bool

格式：

```text
bool <key>=<value>
```

规则：

- 只支持 `true` 和 `false`。
- 大小写敏感，`True`、`FALSE`、`1`、`0` 第一版都不支持。
- 成功后调用 `ep_config_set_bool()`，`true` 写入 `1`，`false` 写入 `0`。

示例：

```text
bool feature.enabled=true
bool feature.disabled=false
```

### string

格式：

```text
string <key>=<value>
```

规则：

- value 按 `=` 后面的原始内容保存。
- 不支持引号转义。
- 不支持多行字符串。
- value 长度继续复用现有 string 长度限制。
- 因为 value 不能为空，所以 `string name=` 返回 `EP_ERR_INVAL`。

示例：

```text
string network.server=127.0.0.1
string device.name=demo_board
```

## 文件大小和行长度限制

第一版使用固定缓冲区，避免动态扩展解析器。

建议上限：

```text
EP_CONFIG_FILE_MAX_SIZE  1024
EP_CONFIG_LINE_MAX_LEN   128
```

策略：

- 文件内容超过 `EP_CONFIG_FILE_MAX_SIZE - 1` 返回 `EP_ERR_BUSY`。
- 单行长度达到或超过 `EP_CONFIG_LINE_MAX_LEN` 返回 `EP_ERR_INVAL`。
- 文件读取后补 `'\0'`，按行解析。

这个限制符合当前第一版用途：加载少量启动参数。后续如果真实产品需要更大配置文件，再单独设计流式解析或更大后端。

## 加载过程

`ep_config_load_file(path)` 的流程：

1. 校验 config 已初始化。
2. 校验 `path` 非空。
3. 调用 `ep_file_open(&file, path, EP_FILE_MODE_READ)`。
4. 循环读取文件内容到固定缓冲区。
5. 关闭文件。
6. 按行解析每个配置项。
7. 每行解析成功后调用对应 `ep_config_set_*()`。
8. 全部成功返回 `EP_OK`。

第一版不做事务回滚。也就是说，如果文件前几行已经成功写入，后续某一行格式错误，函数返回错误，但前面已经写入的配置保留。

这个行为简单、容易实现，符合当前内存配置表的定位。后续如果需要“全部成功才生效”，再单独设计临时表和提交机制。

## 覆盖行为

- 文件中 key 已存在时，按现有 `set` 行为覆盖旧值和类型。
- 文件中同一个 key 出现多次时，后面的配置覆盖前面的配置。
- 调用 `ep_config_load_file()` 多次时，新文件里的 key 覆盖已有 key，未出现的 key 保留原值。

这样可以支持“先加载默认配置，再加载产品或调试覆盖配置”的用法。

## 构建接入

`components/config/CMakeLists.txt` 需要把 file 头文件加入私有 include，并链接 file 组件：

```cmake
target_include_directories(ep_components_config
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
    ${CMAKE_SOURCE_DIR}/components/file/include
)

target_link_libraries(ep_components_config
  PRIVATE
    ep_components_file
)
```

根 `CMakeLists.txt` 里已经先添加 config 再添加 file。CMake 允许在 `target_link_libraries()` 调用时引用后面创建的目标，但为了让阅读顺序更自然，可以把：

```cmake
add_subdirectory(components/file)
```

放到 config 前面。

## 测试策略

实现 PR 需要先补测试，再写代码：

- `tests/api_contract/test_config_headers.py`
  - 检查 `ep_config_load_file` 在头文件中暴露。
  - 确认 `ep_config.h` 仍然不包含 `ep_file.h` 或平台原生头文件。
  - 确认 `ep_config.h` 可独立编译。

- `tests/host_unit/test_host_config.py`
  - 检查 config CMake 私有包含 file 头文件目录。
  - 检查 config 链接 `ep_components_file`。
  - 编译 host smoke 程序，链接 `ep_config.c` 和 `ep_file.c`。
  - 验证正常加载 int/bool/string。
  - 验证重复 key 后者覆盖前者。
  - 验证多次加载只覆盖文件中出现的 key。
  - 验证缺失文件返回 `EP_ERR_UNSUPPORTED`。
  - 验证未初始化返回 `EP_ERR_UNSUPPORTED`。
  - 验证空路径、坏格式、未知类型、非法 bool、非法 int、空 value 返回 `EP_ERR_INVAL`。

建议验证命令：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
git diff --check
```

## 验收标准

- `ep_config_load_file()` API 明确，公共头文件仍然平台无关。
- config 通过 `components/file` 读取文件，不直接调用 `fopen`、POSIX 或 RT-Thread API。
- Mac/Ubuntu host 上能从文本文件加载 int/bool/string 配置。
- 文件格式、错误路径、覆盖行为都有测试固定。
- 不修改 framework 自动初始化顺序。
- 不引入 JSON/INI、flash、Luban-Lite 或 RT-Thread 依赖。
