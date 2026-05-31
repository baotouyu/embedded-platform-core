# host 资源使用冒烟示例实现计划

> 执行说明：按任务逐步实现，每一步用复选框记录状态。

**目标：** 增加一个 host/macOS 资源冒烟程序，验证平台路径接口可以拿到图片、字体、主题资源路径，并通过现有文件组件读取到实际文件。

**架构：** 冒烟程序作为 `platforms/host/posix` 下的独立可执行目标，不接入 LVGL 和 SDL2。程序调用 `ep_platform_*_path()` 拼出路径，再调用 `ep_file_open()` 和 `ep_file_read()` 读取三个占位资源。

**技术栈：** C11、CMake、pytest、host/macOS POSIX 平台。

---

## 文件结构

- 新增 `tests/host_unit/test_host_resource_smoke.py`：验证 CMake 接入、资源文件、demo 源码和可执行程序运行。
- 新增 `platforms/host/posix/demos/resource_smoke_main.c`：host 资源冒烟程序入口。
- 修改 `platforms/host/posix/CMakeLists.txt`：增加 `ep_host_resource_smoke` 目标。
- 新增 `resources/host/images/smoke.txt`：图片目录冒烟占位资源。
- 新增 `resources/host/fonts/smoke.txt`：字体目录冒烟占位资源。
- 新增 `resources/host/themes/smoke.txt`：主题目录冒烟占位资源。
- 修改 `docs/architecture/project-overview.md`：同步说明 host 资源冒烟示例。
- 修改 `docs/development/roadmap.md`：把当前下一步从资源冒烟改成后续真实资源加载或工具脚本。

---

### 任务 1：写 host 资源冒烟测试

**文件：**
- 新增：`tests/host_unit/test_host_resource_smoke.py`

- [x] **步骤 1：写失败测试**

写入以下测试代码：

```python
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_host_resource_smoke_files_and_cmake_are_declared():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )
    source = REPO_ROOT / "platforms/host/posix/demos/resource_smoke_main.c"

    assert source.is_file()
    content = source.read_text(encoding="utf-8")
    assert "ep_platform_image_path" in content
    assert "ep_platform_font_path" in content
    assert "ep_platform_theme_path" in content
    assert "ep_file_open" in content
    assert "ep_file_read" in content

    assert "add_executable(ep_host_resource_smoke" in cmake
    assert "demos/resource_smoke_main.c" in cmake
    assert "paths/ep_host_platform_paths.c" in cmake
    assert "ep_components_file" in cmake
    assert "ep_platform_api" in cmake


def test_host_resource_smoke_assets_exist_and_are_not_empty():
    for relative_path in [
        "resources/host/images/smoke.txt",
        "resources/host/fonts/smoke.txt",
        "resources/host/themes/smoke.txt",
    ]:
        resource = REPO_ROOT / relative_path
        assert resource.is_file()
        assert resource.read_text(encoding="utf-8").strip()


def test_host_resource_smoke_builds_and_runs():
    build_dir = REPO_ROOT / "build"

    configure_result = subprocess.run(
        ["cmake", "-S", ".", "-B", str(build_dir)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert configure_result.returncode == 0, (
        f"stdout:\n{configure_result.stdout}\nstderr:\n{configure_result.stderr}"
    )

    build_result = subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "ep_host_resource_smoke"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert build_result.returncode == 0, (
        f"stdout:\n{build_result.stdout}\nstderr:\n{build_result.stderr}"
    )

    executable = build_dir / "platforms/host/posix/ep_host_resource_smoke"
    run_result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert run_result.returncode == 0, (
        f"stdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
```

- [x] **步骤 2：运行测试确认失败**

运行：

```bash
pytest tests/host_unit/test_host_resource_smoke.py -v
```

预期：失败，因为 demo 源文件、CMake 目标和占位资源还不存在。

---

### 任务 2：实现 host 资源冒烟程序

**文件：**
- 新增：`platforms/host/posix/demos/resource_smoke_main.c`
- 修改：`platforms/host/posix/CMakeLists.txt`
- 新增：`resources/host/images/smoke.txt`
- 新增：`resources/host/fonts/smoke.txt`
- 新增：`resources/host/themes/smoke.txt`
- 测试：`tests/host_unit/test_host_resource_smoke.py`

- [x] **步骤 1：新增占位资源**

新增三个文本资源：

```text
resources/host/images/smoke.txt
resources/host/fonts/smoke.txt
resources/host/themes/smoke.txt
```

文件内容分别为：

```text
host image smoke resource
```

```text
host font smoke resource
```

```text
host theme smoke resource
```

- [x] **步骤 2：新增 demo 源码**

写入 `platforms/host/posix/demos/resource_smoke_main.c`：

```c
#include "ep_file.h"
#include "ep_osal_err.h"
#include "ep_platform_paths.h"

#include <stddef.h>

#define EP_HOST_RESOURCE_SMOKE_PATH_SIZE 128u
#define EP_HOST_RESOURCE_SMOKE_READ_SIZE 32u

typedef int (*ep_host_resource_path_fn_t)(const char *name, char *buffer, size_t buffer_size);

static int ep_host_resource_smoke_read_file(const char *path)
{
    ep_file_t *file = 0;
    char buffer[EP_HOST_RESOURCE_SMOKE_READ_SIZE];
    size_t bytes_read = 0u;
    int rc;

    rc = ep_file_open(&file, path, EP_FILE_MODE_READ);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_file_read(file, buffer, sizeof(buffer), &bytes_read);
    if (rc != EP_OK) {
        (void)ep_file_close(file);
        return rc;
    }

    rc = ep_file_close(file);
    if (rc != EP_OK) {
        return rc;
    }

    return (bytes_read > 0u) ? EP_OK : EP_ERR_UNSUPPORTED;
}

static int ep_host_resource_smoke_check(
    ep_host_resource_path_fn_t path_fn,
    const char *name)
{
    char path[EP_HOST_RESOURCE_SMOKE_PATH_SIZE];
    int rc = path_fn(name, path, sizeof(path));

    if (rc != EP_OK) {
        return rc;
    }

    return ep_host_resource_smoke_read_file(path);
}

int main(void)
{
    int rc = ep_host_resource_smoke_check(ep_platform_image_path, "smoke.txt");
    if (rc != EP_OK) {
        return 1;
    }

    rc = ep_host_resource_smoke_check(ep_platform_font_path, "smoke.txt");
    if (rc != EP_OK) {
        return 2;
    }

    rc = ep_host_resource_smoke_check(ep_platform_theme_path, "smoke.txt");
    if (rc != EP_OK) {
        return 3;
    }

    return 0;
}
```

- [x] **步骤 3：接入 CMake**

在 `platforms/host/posix/CMakeLists.txt` 中新增目标：

```cmake
add_executable(ep_host_resource_smoke
  demos/resource_smoke_main.c
  paths/ep_host_platform_paths.c
)

target_include_directories(ep_host_resource_smoke
  PRIVATE
    ${CMAKE_SOURCE_DIR}/components/file/include
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_host_resource_smoke
  PRIVATE
    ep_components_file
    ep_platform_api
)
```

- [x] **步骤 4：运行资源冒烟测试**

运行：

```bash
pytest tests/host_unit/test_host_resource_smoke.py -v
```

预期：通过。

---

### 任务 3：同步中文文档

**文件：**
- 修改：`docs/architecture/project-overview.md`
- 修改：`docs/development/roadmap.md`
- 测试：`tests/host_unit/test_repository_layout.py`

- [x] **步骤 1：更新项目总览**

在 `docs/architecture/project-overview.md` 的 host/macOS 平台已完成内容中补充：

```text
- host 资源冒烟示例。
```

在平台路径接口说明中补充：

```text
host/macOS 已经有独立的 `ep_host_resource_smoke` 冒烟程序，用来验证图片、字体、主题路径可以被程序打开并读取。
```

- [x] **步骤 2：更新路线图**

在 `docs/development/roadmap.md` 的阶段 4 已完成内容中补充：

```text
- host 资源使用冒烟示例。
```

把“当前下一步”调整为：

```text
真实资源加载示例或资源工具脚本
```

说明下一步可以继续选择：

```text
如果要推进 UI，可以在 LVGL demo 里加载真实图片或字体；如果要推进工程化，可以做资源检查、拷贝或打包脚本。
```

- [x] **步骤 3：运行文档测试**

运行：

```bash
pytest tests/host_unit/test_repository_layout.py -v
```

预期：通过。

---

### 任务 4：最终验证和提交

**文件：**
- 全部本次改动文件

- [x] **步骤 1：运行相关测试**

运行：

```bash
pytest tests/host_unit/test_host_resource_smoke.py tests/host_unit/test_repository_layout.py -v
```

预期：全部通过。

- [x] **步骤 2：运行全量 host/API 测试**

运行：

```bash
pytest tests/host_unit tests/api_contract -v
```

预期：全部通过。

- [x] **步骤 3：运行 CMake 构建和冒烟程序**

运行：

```bash
cmake -S . -B build
cmake --build build --target ep_host_resource_smoke
./build/platforms/host/posix/ep_host_resource_smoke
```

预期：配置成功、构建成功、程序返回 `0`。

- [ ] **步骤 4：提交功能实现**

运行：

```bash
git add docs/architecture/project-overview.md docs/development/roadmap.md platforms/host/posix/CMakeLists.txt platforms/host/posix/demos/resource_smoke_main.c resources/host/images/smoke.txt resources/host/fonts/smoke.txt resources/host/themes/smoke.txt tests/host_unit/test_host_resource_smoke.py
git commit -m "feat: 增加host资源冒烟示例"
```

预期：生成一个中文提交。
