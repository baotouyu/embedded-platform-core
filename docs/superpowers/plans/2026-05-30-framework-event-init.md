# Framework Event Init Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `ep_framework_init()` 初始化全局 event bus，使框架启动链路默认具备事件基础。

**Architecture:** core 层通过 `ep_event.h` 调用 `ep_event_init()`，继续由 `ep_framework_start()` 负责启动顺序和失败传播。构建上只给 `ep_core` 增加 event 公共头路径，最终可执行文件继续链接 `ep_components_event`。

**Tech Stack:** C11、CMake、`components/event`、host POSIX 测试、pytest。

---

## 文件结构

- Modify: `core/src/ep_framework.c`
  - include `ep_event.h`，并在 `ep_framework_init()` 中调用 `ep_event_init()`。
- Modify: `core/CMakeLists.txt`
  - 给 `ep_core` 增加 `components/event/include` 私有 include 路径。
- Modify: `tests/host_unit/test_framework_bootstrap.py`
  - 锁定 framework 到 event 的源码和 CMake 接入关系。

## Task 1: 锁定 framework 到 event 的接入契约

**Files:**
- Modify: `tests/host_unit/test_framework_bootstrap.py`

- [ ] **Step 1: 写失败的接入测试**

修改 `tests/host_unit/test_framework_bootstrap.py` 的 `test_framework_bootstrap_symbols_exist()`，
在现有断言后追加：

```python
    assert '#include "ep_event.h"' in source
    assert "return ep_event_init();" in source
    assert "${CMAKE_SOURCE_DIR}/components/event/include" in cmake
```

修改后的函数应包含：

```python
def test_framework_bootstrap_symbols_exist():
    header = Path("core/include/ep_framework.h").read_text()
    app_header = Path("app/include/app_main.h").read_text()
    source = Path("core/src/ep_framework.c").read_text()
    cmake = Path("core/CMakeLists.txt").read_text()
    assert "int ep_platform_boot(void);" in header
    assert "int ep_framework_init(void);" in header
    assert "int ep_framework_start(void);" in header
    assert "int app_main(void);" in app_header
    assert "int ep_framework_init(void)" in source
    assert "int ep_framework_start(void)" in source
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in cmake
    assert "PUBLIC\n    ${CMAKE_CURRENT_SOURCE_DIR}/include" in cmake
    assert "PRIVATE\n    ${CMAKE_SOURCE_DIR}/app/include" in cmake
    assert "PUBLIC\n    ${CMAKE_SOURCE_DIR}/app/include" not in cmake
    assert '#include "ep_event.h"' in source
    assert "return ep_event_init();" in source
    assert "${CMAKE_SOURCE_DIR}/components/event/include" in cmake
```

- [ ] **Step 2: 运行测试，确认因为尚未接入 event 而失败**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py::test_framework_bootstrap_symbols_exist -v
```

Expected:

```text
FAILED tests/host_unit/test_framework_bootstrap.py::test_framework_bootstrap_symbols_exist
assert '#include "ep_event.h"' in source
```

- [ ] **Step 3: 提交失败测试**

不要单独提交失败测试。失败测试和实现一起提交，保持主线提交可构建。

## Task 2: 实现 framework init 调用 event init

**Files:**
- Modify: `core/src/ep_framework.c`
- Modify: `core/CMakeLists.txt`
- Modify: `tests/host_unit/test_framework_bootstrap.py`

- [ ] **Step 1: 修改 `core/src/ep_framework.c`**

将文件改为：

```c
#include "ep_framework.h"
#include "app_main.h"
#include "ep_event.h"

int ep_framework_init(void)
{
    return ep_event_init();
}

int ep_framework_start(void)
{
    int rc = ep_platform_boot();
    if (rc != 0) {
        return rc;
    }

    rc = ep_framework_init();
    if (rc != 0) {
        return rc;
    }

    return app_main();
}
```

- [ ] **Step 2: 修改 `core/CMakeLists.txt`**

将 `target_include_directories(ep_core ...)` 改为：

```cmake
target_include_directories(ep_core
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/app/include
    ${CMAKE_SOURCE_DIR}/components/event/include
)
```

- [ ] **Step 3: 运行接入测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py::test_framework_bootstrap_symbols_exist -v
```

Expected:

```text
1 passed
```

- [ ] **Step 4: 运行 framework bootstrap 测试文件**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: 提交 framework 接入 event**

Run:

```bash
git add core/src/ep_framework.c core/CMakeLists.txt tests/host_unit/test_framework_bootstrap.py
git commit -m "feat: 接入 framework event 初始化"
```

## Task 3: 完整验证和 PR 前收尾

**Files:**
- Verify only.

- [ ] **Step 1: 运行完整 host 和契约测试**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected:

```text
所有测试通过，0 failed
```

- [ ] **Step 2: 运行 CMake 配置和构建**

Run:

```bash
cmake -S . -B build
cmake --build build
```

Expected:

```text
配置成功，构建成功，输出包含 Built target ep_platform_host_posix
```

- [ ] **Step 3: 运行 host POSIX 程序**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected:

```text
命令退出码为 0
```

- [ ] **Step 4: 检查工作区和提交记录**

Run:

```bash
git status --short --branch
git log --oneline --decorate -5
```

Expected:

```text
工作区干净，最近提交包含 framework event 初始化接入提交
```

- [ ] **Step 5: PR 标题和正文使用中文**

PR 标题：

```text
feat: 接入 framework event 初始化
```

PR 正文：

```markdown
## 变更内容

- 让 `ep_framework_init()` 调用 `ep_event_init()`
- 为 `ep_core` 增加 event 公共头文件 include 路径
- 补充 framework 到 event 的接入契约测试

## 测试

- [ ] `pytest tests/host_unit tests/api_contract -v`
- [ ] `cmake -S . -B build`
- [ ] `cmake --build build`
- [ ] `./build/platforms/host/posix/ep_platform_host_posix`
```

## 自检结果

- 设计文档要求均有对应任务：
  - framework 调用 event init：Task 2。
  - core CMake include 路径：Task 2。
  - host 单元测试覆盖：Task 1 和 Task 2。
  - 完整验证和 PR 中文内容：Task 3。
- 没有引入 timer、log、deinit、初始化表、Luban-Lite 或 RT-Thread 适配。

