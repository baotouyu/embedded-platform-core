# Framework 启动加载配置 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `ep_framework_init()` 在初始化 config 后尝试加载默认配置文件 `config/profiles/host.cfg`。

**Architecture:** framework 不新增公共 API，只在 `core/src/ep_framework.c` 内部增加默认路径宏和静态加载函数。默认配置缺失时继续启动，配置文件存在但内容错误时返回错误码。默认配置文件作为 host profile 示例提交到 `config/profiles/host.cfg`。

**Tech Stack:** C11、CMake、pytest、现有 `ep_config_load_file()`、现有 `EP_OK/EP_ERR_*` 错误码。

---

## 参考文档

- 设计文档：`docs/superpowers/specs/2026-05-31-framework-config-load-design.md`
- config 文件加载设计：`docs/superpowers/specs/2026-05-31-config-file-load-design.md`
- framework config 初始化设计：`docs/superpowers/specs/2026-05-31-framework-config-init-design.md`

## 文件结构

- Create: `config/profiles/host.cfg`
  - host/Mac/Ubuntu 默认配置文件示例。

- Modify: `tests/host_unit/test_repository_layout.py`
  - 增加 `config/profiles/host.cfg` 存在性检查。

- Modify: `tests/host_unit/test_framework_bootstrap.py`
  - 检查 framework 源码包含默认配置加载调用。
  - 检查加载顺序在 `ep_config_init()` 后、`ep_event_init()` 前。
  - 增加 host smoke 测试，验证 `ep_framework_init()` 会加载配置。
  - 增加缺失默认配置文件不失败的测试。
  - 增加坏默认配置文件会失败的测试。

- Modify: `core/src/ep_framework.c`
  - 增加 `EP_FRAMEWORK_DEFAULT_CONFIG_PATH`。
  - 增加静态函数 `ep_framework_load_default_config()`。
  - 在 `ep_config_init()` 后调用默认配置加载。

- Modify: `core/CMakeLists.txt`
  - 私有包含 `osal/include`，因为 framework 需要判断 `EP_ERR_UNSUPPORTED`。

---

## Task 1: 默认 host 配置文件

**Files:**
- Modify: `tests/host_unit/test_repository_layout.py`
- Create: `config/profiles/host.cfg`

- [ ] **Step 1: 写失败测试，要求默认 host 配置文件存在**

修改 `tests/host_unit/test_repository_layout.py`，在 `test_repository_layout_matches_task_requirements()` 后新增：

```python
def test_default_host_config_profile_exists():
    repo_root = Path(__file__).resolve().parents[2]
    host_config = repo_root / "config/profiles/host.cfg"

    assert host_config.is_file()

    content = host_config.read_text(encoding="utf-8")
    assert "int log.level=3" in content
    assert "bool feature.enabled=true" in content
    assert "string device.name=host" in content
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/host_unit/test_repository_layout.py::test_default_host_config_profile_exists -v
```

Expected:

```text
FAILED ... assert False
```

- [ ] **Step 3: 创建默认 host 配置文件**

创建 `config/profiles/host.cfg`：

```text
int log.level=3
bool feature.enabled=true
string device.name=host
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
pytest tests/host_unit/test_repository_layout.py::test_default_host_config_profile_exists -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交默认配置文件**

```bash
git add tests/host_unit/test_repository_layout.py config/profiles/host.cfg
git commit -m "test: 增加 host 默认配置文件"
```

---

## Task 2: framework 默认加载调用和基础行为

**Files:**
- Modify: `tests/host_unit/test_framework_bootstrap.py`
- Modify: `core/src/ep_framework.c`
- Modify: `core/CMakeLists.txt`

- [ ] **Step 1: 写失败测试，要求 framework 源码和启动行为都接入默认配置**

修改 `tests/host_unit/test_framework_bootstrap.py` 文件顶部，增加编译器探测：

```python
import shutil
import subprocess
from pathlib import Path


COMPILER = shutil.which("clang") or shutil.which("cc")
```

修改 `tests/host_unit/test_framework_bootstrap.py` 的 `test_framework_bootstrap_symbols_exist()`，在 config 相关断言附近新增：

```python
    assert '#include "ep_osal_err.h"' in source
    assert "EP_FRAMEWORK_DEFAULT_CONFIG_PATH" in source
    assert '"config/profiles/host.cfg"' in source
    assert "static int ep_framework_load_default_config(void)" in source
    assert "ep_config_load_file(EP_FRAMEWORK_DEFAULT_CONFIG_PATH)" in source
    assert "rc = ep_framework_load_default_config();" in source
    assert "if (rc == EP_ERR_UNSUPPORTED)" in source
    assert "${CMAKE_SOURCE_DIR}/osal/include" in cmake
```

同时补顺序断言：

```python
    assert source.index("ep_config_init()") < source.index("ep_framework_load_default_config()")
    assert source.index("ep_framework_load_default_config()") < source.index("ep_event_init()")
```

继续在 `tests/host_unit/test_framework_bootstrap.py` 末尾新增：

```python
def test_framework_init_loads_default_host_config(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    repo_root = Path(__file__).resolve().parents[2]
    source = tmp_path / "framework_config_load_smoke.c"
    executable = tmp_path / "framework_config_load_smoke"

    source.write_text(
        """
        #include "ep_framework.h"
        #include "ep_config.h"
        #include "ep_osal_err.h"

        #include <string.h>

        int app_main(void)
        {
            return 0;
        }

        int ep_platform_boot(void)
        {
            return 0;
        }

        int main(void)
        {
            const char *device_name;

            if (ep_framework_init() != EP_OK) {
                return 1;
            }

            if (ep_config_get_int("log.level", 0) != 3) {
                return 2;
            }

            if (ep_config_get_bool("feature.enabled", 0) != 1) {
                return 3;
            }

            device_name = ep_config_get_string("device.name", "missing");
            if (device_name == 0 || strcmp(device_name, "host") != 0) {
                return 4;
            }

            return 0;
        }
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(repo_root / "core/include"),
            "-I",
            str(repo_root / "app/include"),
            "-I",
            str(repo_root / "osal/include"),
            "-I",
            str(repo_root / "components/log/include"),
            "-I",
            str(repo_root / "components/config/include"),
            "-I",
            str(repo_root / "components/event/include"),
            "-I",
            str(repo_root / "components/timer/include"),
            "-I",
            str(repo_root / "components/file/include"),
            "-I",
            str(repo_root / "third_party/external/EasyLogger/easylogger/inc"),
            str(source),
            str(repo_root / "core/src/ep_framework.c"),
            str(repo_root / "components/log/src/ep_log.c"),
            str(repo_root / "components/config/src/ep_config.c"),
            str(repo_root / "components/event/src/ep_event.c"),
            str(repo_root / "components/timer/src/ep_timer.c"),
            str(repo_root / "components/file/src/ep_file.c"),
            str(repo_root / "third_party/external/EasyLogger/easylogger/src/elog.c"),
            str(repo_root / "third_party/external/EasyLogger/easylogger/src/elog_utils.c"),
            str(repo_root / "third_party/external/EasyLogger/easylogger/port/elog_port.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_time.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
            "-pthread",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    )

    assert compile_result.returncode == 0, compile_result.stderr

    run_result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    )

    assert run_result.returncode == 0, (
        f"framework config load smoke failed with {run_result.returncode}\n"
        f"stdout:\n{run_result.stdout}\n"
        f"stderr:\n{run_result.stderr}"
    )
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py::test_framework_bootstrap_symbols_exist tests/host_unit/test_framework_bootstrap.py::test_framework_init_loads_default_host_config -v
```

Expected:

```text
FAILED ... AssertionError
FAILED ... framework config load smoke failed with 2
```

- [ ] **Step 3: 修改 core CMake，加入 osal include**

修改 `core/CMakeLists.txt`：

```cmake
target_include_directories(ep_core
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/app/include
    ${CMAKE_SOURCE_DIR}/osal/include
    ${CMAKE_SOURCE_DIR}/components/log/include
    ${CMAKE_SOURCE_DIR}/components/config/include
    ${CMAKE_SOURCE_DIR}/components/event/include
    ${CMAKE_SOURCE_DIR}/components/timer/include
)
```

- [ ] **Step 4: 修改 framework 源码，加入默认加载函数**

将 `core/src/ep_framework.c` 改为：

```c
#include "ep_framework.h"
#include "app_main.h"
#include "ep_log.h"
#include "ep_config.h"
#include "ep_event.h"
#include "ep_timer.h"
#include "ep_osal_err.h"

#define EP_FRAMEWORK_DEFAULT_CONFIG_PATH "config/profiles/host.cfg"

static int ep_framework_load_default_config(void)
{
    int rc = ep_config_load_file(EP_FRAMEWORK_DEFAULT_CONFIG_PATH);

    if (rc == EP_ERR_UNSUPPORTED) {
        return EP_OK;
    }

    return rc;
}

int ep_framework_init(void)
{
    int rc = ep_log_init();
    if (rc != 0) {
        return rc;
    }

    rc = ep_config_init();
    if (rc != 0) {
        return rc;
    }

    rc = ep_framework_load_default_config();
    if (rc != 0) {
        return rc;
    }

    rc = ep_event_init();
    if (rc != 0) {
        return rc;
    }

    return ep_timer_init();
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

- [ ] **Step 5: 运行源码结构和启动行为测试确认通过**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py::test_framework_bootstrap_symbols_exist tests/host_unit/test_framework_bootstrap.py::test_framework_init_loads_default_host_config -v
```

Expected:

```text
2 passed
```

- [ ] **Step 6: 提交 framework 默认加载调用**

```bash
git add tests/host_unit/test_framework_bootstrap.py core/src/ep_framework.c core/CMakeLists.txt
git commit -m "feat: 接入 framework 默认配置加载"
```

---

## Task 3: framework 启动加载边界行为测试

**Files:**
- Modify: `tests/host_unit/test_framework_bootstrap.py`

- [ ] **Step 1: 写缺失默认配置文件不失败测试**

继续在 `tests/host_unit/test_framework_bootstrap.py` 末尾新增：

```python
def test_framework_init_ignores_missing_default_config(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    repo_root = Path(__file__).resolve().parents[2]
    source = tmp_path / "framework_missing_config_smoke.c"
    executable = tmp_path / "framework_missing_config_smoke"

    source.write_text(
        """
        #include "ep_framework.h"
        #include "ep_osal_err.h"

        int app_main(void)
        {
            return 0;
        }

        int ep_platform_boot(void)
        {
            return 0;
        }

        int main(void)
        {
            return ep_framework_init() == EP_OK ? 0 : 1;
        }
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(repo_root / "core/include"),
            "-I",
            str(repo_root / "app/include"),
            "-I",
            str(repo_root / "osal/include"),
            "-I",
            str(repo_root / "components/log/include"),
            "-I",
            str(repo_root / "components/config/include"),
            "-I",
            str(repo_root / "components/event/include"),
            "-I",
            str(repo_root / "components/timer/include"),
            "-I",
            str(repo_root / "components/file/include"),
            "-I",
            str(repo_root / "third_party/external/EasyLogger/easylogger/inc"),
            str(source),
            str(repo_root / "core/src/ep_framework.c"),
            str(repo_root / "components/log/src/ep_log.c"),
            str(repo_root / "components/config/src/ep_config.c"),
            str(repo_root / "components/event/src/ep_event.c"),
            str(repo_root / "components/timer/src/ep_timer.c"),
            str(repo_root / "components/file/src/ep_file.c"),
            str(repo_root / "third_party/external/EasyLogger/easylogger/src/elog.c"),
            str(repo_root / "third_party/external/EasyLogger/easylogger/src/elog_utils.c"),
            str(repo_root / "third_party/external/EasyLogger/easylogger/port/elog_port.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_time.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
            "-pthread",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    )

    assert compile_result.returncode == 0, compile_result.stderr

    run_result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )

    assert run_result.returncode == 0, (
        f"framework missing config smoke failed with {run_result.returncode}\n"
        f"stdout:\n{run_result.stdout}\n"
        f"stderr:\n{run_result.stderr}"
    )
```

- [ ] **Step 2: 运行缺失配置测试确认通过**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py::test_framework_init_ignores_missing_default_config -v
```

Expected:

```text
1 passed
```

- [ ] **Step 3: 写坏配置文件会失败测试**

继续在 `tests/host_unit/test_framework_bootstrap.py` 末尾新增：

```python
def test_framework_init_fails_on_invalid_default_config(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    repo_root = Path(__file__).resolve().parents[2]
    source = tmp_path / "framework_bad_config_smoke.c"
    executable = tmp_path / "framework_bad_config_smoke"
    config_dir = tmp_path / "config/profiles"

    config_dir.mkdir(parents=True)
    (config_dir / "host.cfg").write_text("bad config\n", encoding="utf-8")

    source.write_text(
        """
        #include "ep_framework.h"
        #include "ep_osal_err.h"

        int app_main(void)
        {
            return 0;
        }

        int ep_platform_boot(void)
        {
            return 0;
        }

        int main(void)
        {
            return ep_framework_init() == EP_ERR_INVAL ? 0 : 1;
        }
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(repo_root / "core/include"),
            "-I",
            str(repo_root / "app/include"),
            "-I",
            str(repo_root / "osal/include"),
            "-I",
            str(repo_root / "components/log/include"),
            "-I",
            str(repo_root / "components/config/include"),
            "-I",
            str(repo_root / "components/event/include"),
            "-I",
            str(repo_root / "components/timer/include"),
            "-I",
            str(repo_root / "components/file/include"),
            "-I",
            str(repo_root / "third_party/external/EasyLogger/easylogger/inc"),
            str(source),
            str(repo_root / "core/src/ep_framework.c"),
            str(repo_root / "components/log/src/ep_log.c"),
            str(repo_root / "components/config/src/ep_config.c"),
            str(repo_root / "components/event/src/ep_event.c"),
            str(repo_root / "components/timer/src/ep_timer.c"),
            str(repo_root / "components/file/src/ep_file.c"),
            str(repo_root / "third_party/external/EasyLogger/easylogger/src/elog.c"),
            str(repo_root / "third_party/external/EasyLogger/easylogger/src/elog_utils.c"),
            str(repo_root / "third_party/external/EasyLogger/easylogger/port/elog_port.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_time.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
            "-pthread",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    )

    assert compile_result.returncode == 0, compile_result.stderr

    run_result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )

    assert run_result.returncode == 0, (
        f"framework bad config smoke failed with {run_result.returncode}\n"
        f"stdout:\n{run_result.stdout}\n"
        f"stderr:\n{run_result.stderr}"
    )
```

- [ ] **Step 4: 运行坏配置测试确认通过**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py::test_framework_init_fails_on_invalid_default_config -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 运行 framework 相关测试**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py tests/host_unit/test_repository_layout.py -v
```

Expected:

```text
7 passed
```

- [ ] **Step 6: 提交 framework 行为测试**

```bash
git add tests/host_unit/test_framework_bootstrap.py
git commit -m "test: 覆盖 framework 默认配置加载"
```

---

## Task 4: 全量验证、PR、合并和清理

**Files:**
- No source changes expected

- [ ] **Step 1: 运行全量测试**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected:

```text
62 passed
```

实际数量可能随测试变化略有不同，要求是全部通过、0 failures。

- [ ] **Step 2: 运行 CMake 配置和构建**

Run:

```bash
cmake -S . -B build
cmake --build build
```

Expected:

```text
-- Configuring done
-- Generating done
Built target ep_core
Built target ep_components_config
Built target ep_platform_host_posix
```

- [ ] **Step 3: 运行 host 可执行文件**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected: exit code 0.

- [ ] **Step 4: 运行 diff 空白检查**

Run:

```bash
git diff --check
```

Expected: no output, exit code 0.

- [ ] **Step 5: 检查工作区和提交范围**

Run:

```bash
git status --short --branch
git log --oneline --decorate --graph --max-count=8
git diff --stat origin/main..HEAD
```

Expected:

```text
## feature/framework-config-load
```

Diff 应只包含：

```text
config/profiles/host.cfg
core/CMakeLists.txt
core/src/ep_framework.c
tests/host_unit/test_framework_bootstrap.py
tests/host_unit/test_repository_layout.py
```

- [ ] **Step 6: 推送实现分支**

```bash
git push -u origin feature/framework-config-load
```

- [ ] **Step 7: 创建 PR**

```bash
gh pr create --base main --head feature/framework-config-load --title "feat: 接入 framework 默认配置加载" --body "$(cat <<'EOF'
## Summary
- 新增 `config/profiles/host.cfg` 默认 host 配置文件
- framework 初始化时在 config init 后尝试加载默认配置
- 补充默认配置加载、缺失配置忽略和坏配置失败测试

## Validation
- [x] `pytest tests/host_unit tests/api_contract -v`
- [x] `cmake -S . -B build`
- [x] `cmake --build build`
- [x] `./build/platforms/host/posix/ep_platform_host_posix`
- [x] `git diff --check`

## Notes
- 本 PR 不新增 framework 公共 API
- 本 PR 不修改 app/main 接口
- 本 PR 不接 Luban-Lite、RT-Thread 或真实 flash/NVRAM
EOF
)"
```

- [ ] **Step 8: 等待 GitHub 检查通过**

Run:

```bash
PR_NUMBER=$(gh pr view --json number --jq '.number')
gh pr checks "$PR_NUMBER" --watch --interval 5
```

Expected:

```text
host-tests pass
```

- [ ] **Step 9: squash merge**

```bash
PR_NUMBER=$(gh pr view --json number --jq '.number')
gh pr merge "$PR_NUMBER" --squash --delete-branch --subject "feat: 接入 framework 默认配置加载" --body $'接入 framework 默认配置加载：\n\n- 新增 config/profiles/host.cfg 默认 host 配置文件\n- framework 初始化时尝试加载默认配置\n- 补充默认配置加载、缺失配置忽略和坏配置失败测试'
```

如果出现：

```text
failed to run git: fatal: 'main' is already used by worktree
```

先确认远程 PR 是否已经合并：

```bash
gh pr view "$PR_NUMBER" --json number,state,mergedAt,mergeCommit,url
```

如果 `state` 是 `MERGED`，继续执行本地清理。

- [ ] **Step 10: 同步 main 并清理本地分支**

在主工作区 `/Users/yuwei/Documents/KitchenIdea/项目/C08/embedded-platform-core` 执行：

```bash
git pull --ff-only
git worktree remove .worktrees/feature-framework-config-load
git branch -d feature/framework-config-load
git push origin --delete feature/framework-config-load
```

如果远程分支已经被 GitHub 删除，`git push origin --delete` 可能提示 remote ref 不存在；这种情况下确认远程只剩 `origin/main` 即可。

- [ ] **Step 11: 最终状态确认**

Run:

```bash
git status --short --branch
git branch -vv
git branch -r
git worktree list
gh pr view "$PR_NUMBER" --json number,state,mergedAt,mergeCommit,url,title
```

Expected:

```text
## main...origin/main
* main ... [origin/main] feat: 接入 framework 默认配置加载
origin/HEAD -> origin/main
origin/main
```

并且没有 `feature/framework-config-load` 本地或远程分支。
