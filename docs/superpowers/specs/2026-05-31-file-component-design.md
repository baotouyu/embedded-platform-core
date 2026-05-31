# File 文件组件设计

## 背景

当前工程已经具备 host POSIX 启动、OSAL 基础能力、event、timer、log、config，并且 framework 已经统一初始化：

```text
log -> config -> event -> timer
```

下一步还不急着适配真实芯片平台。为了继续在 Mac/Ubuntu 上把基础能力补稳，可以先建立
`components/file` 文件组件。

file 的价值是给后续能力提供统一文件入口：

- config 后续可以从文件加载。
- log 后续可以写文件。
- 平台参数或调试数据后续可以保存到 host 文件或 RTOS 文件系统。

本阶段只设计第一版 host 可测的文件读写组件，不接 flash，也不直接适配 Luban-Lite 或 RT-Thread。

## 目标

- 新增 `components/file` 组件。
- 暴露平台无关公共头文件 `components/file/include/ep_file.h`。
- 提供最小文件句柄类型：

```c
typedef struct ep_file ep_file_t;
```

- 提供打开、读取、写入、关闭接口：

```c
int ep_file_open(ep_file_t **file, const char *path, int mode);
int ep_file_read(ep_file_t *file, void *buffer, size_t buffer_size, size_t *bytes_read);
int ep_file_write(ep_file_t *file, const void *buffer, size_t buffer_size, size_t *bytes_written);
int ep_file_close(ep_file_t *file);
```

- 提供文件打开模式：

```c
#define EP_FILE_MODE_READ      (1 << 0)
#define EP_FILE_MODE_WRITE     (1 << 1)
#define EP_FILE_MODE_CREATE    (1 << 2)
#define EP_FILE_MODE_TRUNCATE  (1 << 3)
#define EP_FILE_MODE_APPEND    (1 << 4)
```

- 公共头文件保持平台无关，不暴露 `FILE`、`pthread.h`、`unistd.h`、`fcntl.h`、`rtthread.h` 或 SDK 头文件。
- 第一版实现可以在 Mac/Ubuntu host 上通过测试验证读写闭环。

## 非目标

- 不实现目录创建、目录遍历或删除文件。
- 不实现 seek、tell、flush、stat、rename。
- 不实现异步文件 IO。
- 不实现文件锁。
- 不实现 mount、分区、文件系统格式化。
- 不接 flash、NVRAM、EEPROM 或 EasyFlash。
- 不接真实 Luban-Lite、RT-Thread 或板级 SDK。
- 不把 config 改成从文件加载。
- 不把 log 改成写文件。
- 不把 file 接入 `ep_framework_init()` 自动初始化。

## 方案比较

### 方案一：components/file 包装 C 标准库文件接口

`components/file` 内部在 host 上使用 C 标准库 `fopen`、`fread`、`fwrite`、`fclose`。
公共接口只暴露 `ep_file_*`，不把 `FILE *` 暴露给上层。

优点：

- Mac/Ubuntu 上容易验证。
- 不需要新增 OSAL 文件接口。
- 公共 API 可以保持平台无关。
- 后续 RTOS 或 Luban-Lite 可以在组件内部替换成 DFS、POSIX-like API 或平台文件接口。

缺点：

- 第一版实现内部仍依赖 C 标准库文件能力。
- 如果后续裸机没有文件系统，需要单独设计 flash/key-value 后端。

### 方案二：先设计 OSAL file，再由 components/file 包装 OSAL

先在 `osal/include` 增加 `ep_osal_file.h`，host POSIX 实现 OSAL file，components/file 再调用 OSAL。

优点：

- 平台边界更严格。
- 后续 RTOS port 形态更统一。

缺点：

- 当前只有 components/file 一个使用方，先加 OSAL file 会多一层抽象。
- 需要同时设计 OSAL API、组件 API 和 platform port，PR 变大。

### 方案三：直接让 config 使用 POSIX/stdio 文件接口

不单独做 file 组件，后续 config 需要文件时直接读取文件。

优点：

- 短期代码量最少。

缺点：

- config 会直接绑定平台文件接口。
- log、config、其他组件后续会各自处理文件，边界会散。
- 不符合当前工程“基础能力组件化”的方向。

## 推荐方案

采用方案一：第一版 `components/file` 包装 C 标准库文件接口。

推荐原因：

- 当前主要目标是在 Mac/Ubuntu 上小步跑通文件能力。
- 第一版 API 可以先稳定下来，后续 config/log 使用同一套 `ep_file_*`。
- 不提前引入 OSAL file，避免为了一个组件扩散到更大平台抽象。
- 不把 `FILE *` 泄漏到公共头文件，后续内部换成 RT-Thread DFS 或 Luban-Lite 文件接口时，上层不用改。

## 公共 API 设计

`components/file/include/ep_file.h`：

```c
#ifndef EP_FILE_H
#define EP_FILE_H

#include <stddef.h>

#define EP_FILE_MODE_READ      (1 << 0)
#define EP_FILE_MODE_WRITE     (1 << 1)
#define EP_FILE_MODE_CREATE    (1 << 2)
#define EP_FILE_MODE_TRUNCATE  (1 << 3)
#define EP_FILE_MODE_APPEND    (1 << 4)

typedef struct ep_file ep_file_t;

int ep_file_open(ep_file_t **file, const char *path, int mode);
int ep_file_read(ep_file_t *file, void *buffer, size_t buffer_size, size_t *bytes_read);
int ep_file_write(ep_file_t *file, const void *buffer, size_t buffer_size, size_t *bytes_written);
int ep_file_close(ep_file_t *file);

#endif
```

接口语义：

- `ep_file_open()` 成功后通过 `file` 输出句柄。
- `ep_file_close()` 关闭句柄并释放内部资源。
- `ep_file_read()` 尝试读取最多 `buffer_size` 字节，通过 `bytes_read` 返回实际读取字节数。
- `ep_file_write()` 尝试写入 `buffer_size` 字节，通过 `bytes_written` 返回实际写入字节数。
- `bytes_read` 和 `bytes_written` 可以为 `0`。调用方不关心实际字节数时可以传空指针。

## 打开模式

第一版支持以下组合：

```text
EP_FILE_MODE_READ
EP_FILE_MODE_WRITE | EP_FILE_MODE_CREATE
EP_FILE_MODE_WRITE | EP_FILE_MODE_CREATE | EP_FILE_MODE_TRUNCATE
EP_FILE_MODE_WRITE | EP_FILE_MODE_CREATE | EP_FILE_MODE_APPEND
EP_FILE_MODE_READ  | EP_FILE_MODE_WRITE
EP_FILE_MODE_READ  | EP_FILE_MODE_WRITE | EP_FILE_MODE_CREATE
```

建议 host stdio 映射：

```text
READ                                -> "rb"
WRITE | CREATE                      -> "ab+"
WRITE | CREATE | TRUNCATE           -> "wb"
WRITE | CREATE | APPEND             -> "ab"
READ | WRITE                        -> "rb+"
READ | WRITE | CREATE               -> "ab+"
READ | WRITE | CREATE | TRUNCATE    -> "wb+"
```

不支持的组合返回 `EP_ERR_INVAL`。例如：

- `mode == 0`
- 只有 `CREATE`，没有 `READ` 或 `WRITE`
- `APPEND` 和 `TRUNCATE` 同时出现
- `READ | APPEND` 但没有 `WRITE`

## 内部数据模型

第一版内部句柄可以是：

```c
struct ep_file {
    FILE *handle;
};
```

该结构只放在 `components/file/src/ep_file.c` 内部。公共头文件只前置声明 `ep_file_t`。

后续平台替换时可以改成：

```c
struct ep_file {
    int fd;
};
```

或 RTOS 文件对象指针，但不影响上层。

## 错误处理

返回值使用现有 `ep_osal_err.h` 中的错误码：

- 成功返回 `EP_OK`。
- 参数非法返回 `EP_ERR_INVAL`。
- 打开失败、读写失败、关闭失败返回 `EP_ERR_UNSUPPORTED`。
- 内部句柄分配失败返回 `EP_ERR_BUSY`。

参数校验：

- `ep_file_open()` 中 `file == 0`、`path == 0`、空路径、非法 mode 返回 `EP_ERR_INVAL`。
- `ep_file_read()` 中 `file == 0`、`buffer == 0` 且 `buffer_size > 0` 返回 `EP_ERR_INVAL`。
- `ep_file_write()` 中 `file == 0`、`buffer == 0` 且 `buffer_size > 0` 返回 `EP_ERR_INVAL`。
- `ep_file_close()` 中 `file == 0` 返回 `EP_ERR_INVAL`。

读写字节数策略：

- read/write 开始前如果输出字节数指针非空，先置为 `0`。
- `buffer_size == 0` 时 read/write 返回 `EP_OK`，实际字节数为 `0`。
- 文件读到 EOF 时 read 返回 `EP_OK`，`bytes_read == 0`。
- `fread` 或 `fwrite` 发生错误时返回 `EP_ERR_UNSUPPORTED`。

## 构建接入

新增目录结构：

```text
components/file/
├── CMakeLists.txt
├── include/
│   └── ep_file.h
└── src/
    └── ep_file.c
```

根 `CMakeLists.txt` 增加：

```cmake
add_subdirectory(components/file)
```

建议放在 `components/config` 后面：

```cmake
add_subdirectory(components/log)
add_subdirectory(components/config)
add_subdirectory(components/file)
```

`components/file/CMakeLists.txt`：

```cmake
add_library(ep_components_file STATIC
  src/ep_file.c
)

target_include_directories(ep_components_file
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
)
```

host POSIX 和 linux demo 最终目标第一版可以先不链接 `ep_components_file`，因为 framework 还不会使用 file。
如果全仓构建需要构建静态库，根 CMake 的 `add_subdirectory(components/file)` 已足够。

## 与 config/log 的关系

本阶段 file 只是独立组件，不改 config/log 行为。

后续可以单独设计：

- `ep_config_load_file(const char *path)` 或 config 后端加载机制。
- EasyLogger 文件插件或 `components/log` 自己调用 `ep_file_write()`。
- 平台启动时从默认配置文件加载参数。

这样做的原因是 file API 还需要先稳定，不应该在同一个 PR 里同时改 config 和 log。

## 测试策略

实现 PR 需要先补测试，再改实现：

- `tests/api_contract/test_file_headers.py`
  - 检查 `ep_file.h` 存在。
  - 检查 `ep_file.h` 可独立编译。
  - 检查公共头文件不暴露 `FILE`、`stdio.h`、`unistd.h`、`fcntl.h`、`rtthread.h` 或平台目录。
- `tests/host_unit/test_host_file.py`
  - 检查 `components/file` 接入 CMake。
  - 编译并运行 host C 冒烟程序：
    - 写入新文件。
    - 关闭后重新打开读取。
    - 校验读出的内容。
    - 校验 append 行为。
    - 校验 truncate 行为。
    - 校验非法参数返回错误。
    - 校验读 EOF 返回 `EP_OK` 且字节数为 `0`。
- 保持现有 host/api 测试通过。

建议验证命令：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
git diff --check
```

## 验收标准

- `components/file/include/ep_file.h` 平台无关，不暴露 host 或 RTOS 原生文件类型。
- `components/file` 能被 CMake 构建为 `ep_components_file`。
- Mac/Ubuntu host 上可以通过 `ep_file_*` 完成写、读、追加、截断、关闭。
- 非法参数和不支持模式返回明确错误码。
- 本阶段不修改 config、log、framework 初始化链路。
- 本阶段不接 flash、真实 Luban-Lite、RT-Thread 或板级 SDK。
