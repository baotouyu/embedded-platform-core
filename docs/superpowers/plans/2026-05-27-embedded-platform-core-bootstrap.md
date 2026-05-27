# Embedded Platform Core Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the initial repository skeleton, unified bootstrap flow, and public OSAL/HAL API surface for an RTOS/Linux portable embedded platform framework.

**Architecture:** The work establishes a top-level repository structure with strict layer boundaries, introduces a `core/` bootstrap layer, defines public OSAL/HAL headers, and adds one RTOS skeleton and one Linux skeleton that both flow through `ep_platform_boot() -> ep_framework_init() -> app_main()`. Existing local assets are preserved and reorganized into the new structure without introducing platform leakage into application or component layers.

**Tech Stack:** C, CMake, Git, GitHub, RTOS vendor SDK integration model, Linux user-space APIs

---

## File Structure Map

- `CMakeLists.txt`
  Top-level build entry that selects platform families and includes core layers.
- `.gitignore`
  Ignore OS metadata, build outputs, and `.superpowers/`.
- `README.md`
  Repository introduction, scope, and quick-start notes.
- `cmake/modules/`
  Shared CMake helper modules.
- `cmake/toolchains/`
  Toolchain files for RTOS and Linux targets.
- `docs/architecture/`
  Long-lived architecture notes beyond the initial spec.
- `docs/porting/`
  Porting guidance for future platform additions.
- `docs/testing/`
  Testing strategy and execution docs.
- `docs/decisions/`
  Design decision records.
- `app/include/app_main.h`
  Public app entry declaration.
- `app/src/app_main.c`
  Minimal platform-neutral application entry.
- `app/gui/`
  Preserved application GUI area.
- `core/include/ep_framework.h`
  Framework lifecycle declarations.
- `core/src/ep_framework.c`
  `ep_framework_init()` implementation and bootstrap sequence.
- `components/`
  Platform-neutral framework and business components.
- `osal/include/*.h`
  Public OSAL headers.
- `hal/include/*.h`
  Public HAL headers.
- `platforms/rtos/common/`
  Shared RTOS-side adaptation helpers.
- `platforms/rtos/demo_family/startup/app_start.c`
  RTOS bootstrap bridge into the framework.
- `platforms/rtos/demo_family/osal_port/`
  RTOS OSAL adaptation stubs.
- `platforms/rtos/demo_family/hal_port/`
  RTOS HAL adaptation stubs.
- `platforms/linux/common/`
  Shared Linux-side adaptation helpers.
- `platforms/linux/demo_family/startup/main.c`
  Linux user-space bootstrap entry.
- `platforms/linux/demo_family/osal_port/`
  Linux OSAL adaptation stubs.
- `platforms/linux/demo_family/hal_port/`
  Linux HAL adaptation stubs.
- `vendor/rtos/`
  Reserved location for RTOS vendor SDK drop-ins and patches.
- `third_party/external/EasyLogger/`
  Preserved third-party logger dependency location.
- `third_party/external/lvgl/`
  Preserved third-party GUI dependency location.
- `config/common/`
  Cross-platform defaults.
- `config/feature/`
  Feature toggles.
- `config/profiles/`
  Product build profiles.
- `tests/host_unit/`
  Host-side unit tests.
- `tests/api_contract/`
  Public API contract tests.
- `tests/integration/`
  Integration-level tests.
- `tests/target_smoke/`
  Target smoke test assets.
- `tools/scripts/`
  Repository setup and developer scripts.
- `tools/ci/`
  CI helper scripts.

### Task 1: Restructure the Repository Skeleton

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `LICENSE`
- Create: `cmake/modules/.gitkeep`
- Create: `cmake/toolchains/.gitkeep`
- Create: `cmake/presets/.gitkeep`
- Create: `docs/architecture/.gitkeep`
- Create: `docs/porting/.gitkeep`
- Create: `docs/testing/.gitkeep`
- Create: `docs/decisions/.gitkeep`
- Create: `core/include/.gitkeep`
- Create: `core/src/.gitkeep`
- Create: `components/log/.gitkeep`
- Create: `components/event/.gitkeep`
- Create: `components/timer/.gitkeep`
- Create: `components/config/.gitkeep`
- Create: `components/device/.gitkeep`
- Create: `components/file/.gitkeep`
- Create: `components/net/.gitkeep`
- Create: `platforms/rtos/common/.gitkeep`
- Create: `platforms/linux/common/.gitkeep`
- Create: `vendor/rtos/.gitkeep`
- Create: `config/common/.gitkeep`
- Create: `config/feature/.gitkeep`
- Create: `config/profiles/.gitkeep`
- Create: `tests/host_unit/.gitkeep`
- Create: `tests/api_contract/.gitkeep`
- Create: `tests/integration/.gitkeep`
- Create: `tests/target_smoke/.gitkeep`
- Create: `tools/scripts/.gitkeep`
- Create: `tools/ci/.gitkeep`
- Create: `examples/.gitkeep`
- Modify: `third_party/`

- [ ] **Step 1: Write the failing structure test**

Create `tests/host_unit/test_repository_layout.py` with:

```python
from pathlib import Path


def test_expected_directories_exist():
    root = Path(__file__).resolve().parents[2]
    expected = [
        "cmake/modules",
        "cmake/toolchains",
        "cmake/presets",
        "docs/architecture",
        "docs/porting",
        "docs/testing",
        "docs/decisions",
        "core/include",
        "core/src",
        "components/log",
        "components/event",
        "components/timer",
        "components/config",
        "components/device",
        "components/file",
        "components/net",
        "platforms/rtos/common",
        "platforms/linux/common",
        "vendor/rtos",
        "config/common",
        "config/feature",
        "config/profiles",
        "tests/host_unit",
        "tests/api_contract",
        "tests/integration",
        "tests/target_smoke",
        "tools/scripts",
        "tools/ci",
        "examples",
    ]

    missing = [path for path in expected if not (root / path).exists()]
    assert not missing, f"Missing directories: {missing}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/host_unit/test_repository_layout.py -v`
Expected: FAIL with missing directory assertions or file-not-found because the test file does not exist yet.

- [ ] **Step 3: Create the repository skeleton**

Create the directories and placeholder files listed above. Add `.gitignore` with:

```gitignore
.DS_Store
build/
out/
.superpowers/
*.o
*.a
*.so
*.dSYM/
```

Add `README.md` with:

```markdown
# embedded-platform-core

A portable embedded platform framework for RTOS and Linux, with unified OS, driver, and component abstractions.
```

Add `LICENSE` with:

```text
Placeholder license file. Replace with the selected project license before public release.
```

Move third-party dependencies into:

```text
third_party/external/EasyLogger/
third_party/external/lvgl/
```

Keep existing application and component assets intact while adding the new directories.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/host_unit/test_repository_layout.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .gitignore README.md LICENSE cmake docs core components platforms vendor config tests tools examples third_party
git commit -m "chore: create repository skeleton"
```

### Task 2: Define the Top-Level Build Graph

**Files:**
- Modify: `CMakeLists.txt`
- Create: `cmake/modules/ep_options.cmake`
- Create: `cmake/modules/ep_sources.cmake`
- Create: `cmake/toolchains/linux-gcc.cmake`
- Create: `cmake/toolchains/rtos-gcc.cmake`
- Test: `tests/host_unit/test_cmake_layout.py`

- [ ] **Step 1: Write the failing build-configuration test**

Create `tests/host_unit/test_cmake_layout.py` with:

```python
from pathlib import Path


def test_top_level_cmake_mentions_core_layers():
    cmake = Path("CMakeLists.txt").read_text()
    assert "project(embedded-platform-core" in cmake
    assert "add_subdirectory(core)" in cmake
    assert "add_subdirectory(app)" in cmake
    assert "EP_PLATFORM_FAMILY" in cmake
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/host_unit/test_cmake_layout.py -v`
Expected: FAIL because `CMakeLists.txt` is empty.

- [ ] **Step 3: Write the minimal build files**

Set `CMakeLists.txt` to:

```cmake
cmake_minimum_required(VERSION 3.20)

project(embedded-platform-core C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/modules")

include(ep_options)

add_subdirectory(core)
add_subdirectory(app)
```

Create `cmake/modules/ep_options.cmake` with:

```cmake
set(EP_PLATFORM_FAMILY "linux" CACHE STRING "Target platform family")
set_property(CACHE EP_PLATFORM_FAMILY PROPERTY STRINGS linux rtos)

set(EP_PLATFORM_NAME "demo_family" CACHE STRING "Target platform package")
set(EP_BOARD_NAME "demo_board" CACHE STRING "Target board profile")
```

Create `cmake/modules/ep_sources.cmake` with:

```cmake
function(ep_collect_stub out_var)
  set(${out_var} ${ARGN} PARENT_SCOPE)
endfunction()
```

Create `cmake/toolchains/linux-gcc.cmake` with:

```cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_C_COMPILER gcc)
```

Create `cmake/toolchains/rtos-gcc.cmake` with:

```cmake
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_C_COMPILER gcc)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/host_unit/test_cmake_layout.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add CMakeLists.txt cmake/modules/ep_options.cmake cmake/modules/ep_sources.cmake cmake/toolchains/linux-gcc.cmake cmake/toolchains/rtos-gcc.cmake tests/host_unit/test_cmake_layout.py
git commit -m "build: add top-level cmake bootstrap"
```

### Task 3: Add the Core Bootstrap Layer

**Files:**
- Create: `core/CMakeLists.txt`
- Create: `core/include/ep_framework.h`
- Create: `core/src/ep_framework.c`
- Create: `app/CMakeLists.txt`
- Create: `app/include/app_main.h`
- Modify: `app/main.c`
- Create: `tests/host_unit/test_framework_bootstrap.py`

- [ ] **Step 1: Write the failing bootstrap test**

Create `tests/host_unit/test_framework_bootstrap.py` with:

```python
from pathlib import Path


def test_framework_bootstrap_symbols_exist():
    header = Path("core/include/ep_framework.h").read_text()
    app_header = Path("app/include/app_main.h").read_text()
    source = Path("core/src/ep_framework.c").read_text()
    assert "int ep_platform_boot(void);" in header
    assert "int ep_framework_init(void);" in header
    assert "int app_main(void);" in app_header
    assert "int ep_framework_init(void)" in source
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/host_unit/test_framework_bootstrap.py -v`
Expected: FAIL because the files do not exist.

- [ ] **Step 3: Write the bootstrap layer**

Create `core/CMakeLists.txt` with:

```cmake
add_library(ep_core STATIC
  src/ep_framework.c
)

target_include_directories(ep_core
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/app/include
)
```

Create `core/include/ep_framework.h` with:

```c
#ifndef EP_FRAMEWORK_H
#define EP_FRAMEWORK_H

int ep_platform_boot(void);
int ep_framework_init(void);
int ep_framework_start(void);

#endif
```

Create `core/src/ep_framework.c` with:

```c
#include "ep_framework.h"
#include "app_main.h"

int ep_framework_init(void)
{
    return 0;
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

Create `app/CMakeLists.txt` with:

```cmake
add_library(ep_app STATIC
  main.c
)

target_include_directories(ep_app
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
```

Create `app/include/app_main.h` with:

```c
#ifndef APP_MAIN_H
#define APP_MAIN_H

int app_main(void);

#endif
```

Replace `app/main.c` with:

```c
#include "app_main.h"

int app_main(void)
{
    return 0;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/host_unit/test_framework_bootstrap.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/CMakeLists.txt core/include/ep_framework.h core/src/ep_framework.c app/CMakeLists.txt app/include/app_main.h app/main.c tests/host_unit/test_framework_bootstrap.py
git commit -m "feat: add framework bootstrap core"
```

### Task 4: Define Public OSAL Headers

**Files:**
- Create: `osal/CMakeLists.txt`
- Create: `osal/include/ep_osal_types.h`
- Create: `osal/include/ep_osal_err.h`
- Create: `osal/include/ep_osal_thread.h`
- Create: `osal/include/ep_osal_mutex.h`
- Create: `osal/include/ep_osal_sem.h`
- Create: `osal/include/ep_osal_queue.h`
- Create: `osal/include/ep_osal_time.h`
- Create: `osal/include/ep_osal_mem.h`
- Create: `tests/api_contract/test_osal_headers.py`

- [ ] **Step 1: Write the failing OSAL header contract test**

Create `tests/api_contract/test_osal_headers.py` with:

```python
from pathlib import Path


def test_osal_headers_use_ep_prefix():
    root = Path("osal/include")
    headers = [
        "ep_osal_types.h",
        "ep_osal_err.h",
        "ep_osal_thread.h",
        "ep_osal_mutex.h",
        "ep_osal_sem.h",
        "ep_osal_queue.h",
        "ep_osal_time.h",
        "ep_osal_mem.h",
    ]
    for name in headers:
        text = (root / name).read_text()
        assert "ep_" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api_contract/test_osal_headers.py -v`
Expected: FAIL because the headers do not exist.

- [ ] **Step 3: Write the public OSAL headers**

Create `osal/CMakeLists.txt` with:

```cmake
add_library(ep_osal INTERFACE)

target_include_directories(ep_osal
  INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
```

Create `osal/include/ep_osal_types.h` with:

```c
#ifndef EP_OSAL_TYPES_H
#define EP_OSAL_TYPES_H

#include <stddef.h>
#include <stdint.h>

typedef struct ep_thread ep_thread_t;
typedef struct ep_mutex ep_mutex_t;
typedef struct ep_sem ep_sem_t;
typedef struct ep_queue ep_queue_t;

#endif
```

Create `osal/include/ep_osal_err.h` with:

```c
#ifndef EP_OSAL_ERR_H
#define EP_OSAL_ERR_H

typedef enum {
    EP_OK = 0,
    EP_ERR_INVAL = -1,
    EP_ERR_TIMEOUT = -2,
    EP_ERR_BUSY = -3,
    EP_ERR_UNSUPPORTED = -4
} ep_err_e;

#endif
```

Create `osal/include/ep_osal_thread.h` with:

```c
#ifndef EP_OSAL_THREAD_H
#define EP_OSAL_THREAD_H

#include "ep_osal_types.h"

typedef void *(*ep_thread_entry_t)(void *arg);

int ep_thread_create(ep_thread_t **thread, const char *name, ep_thread_entry_t entry, void *arg);
int ep_thread_join(ep_thread_t *thread);

#endif
```

Create `osal/include/ep_osal_mutex.h` with:

```c
#ifndef EP_OSAL_MUTEX_H
#define EP_OSAL_MUTEX_H

#include "ep_osal_types.h"

int ep_mutex_create(ep_mutex_t **mutex);
int ep_mutex_lock(ep_mutex_t *mutex);
int ep_mutex_unlock(ep_mutex_t *mutex);

#endif
```

Create `osal/include/ep_osal_sem.h` with:

```c
#ifndef EP_OSAL_SEM_H
#define EP_OSAL_SEM_H

#include "ep_osal_types.h"

int ep_sem_create(ep_sem_t **sem, unsigned int initial_count);
int ep_sem_wait(ep_sem_t *sem, unsigned int timeout_ms);
int ep_sem_post(ep_sem_t *sem);

#endif
```

Create `osal/include/ep_osal_queue.h` with:

```c
#ifndef EP_OSAL_QUEUE_H
#define EP_OSAL_QUEUE_H

#include <stddef.h>
#include "ep_osal_types.h"

int ep_queue_create(ep_queue_t **queue, size_t item_size, size_t depth);
int ep_queue_send(ep_queue_t *queue, const void *item, unsigned int timeout_ms);
int ep_queue_recv(ep_queue_t *queue, void *item, unsigned int timeout_ms);

#endif
```

Create `osal/include/ep_osal_time.h` with:

```c
#ifndef EP_OSAL_TIME_H
#define EP_OSAL_TIME_H

#include <stdint.h>

uint64_t ep_time_now_ms(void);
void ep_sleep_ms(unsigned int timeout_ms);

#endif
```

Create `osal/include/ep_osal_mem.h` with:

```c
#ifndef EP_OSAL_MEM_H
#define EP_OSAL_MEM_H

#include <stddef.h>

void *ep_malloc(size_t size);
void ep_free(void *ptr);

#endif
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api_contract/test_osal_headers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add osal/CMakeLists.txt osal/include tests/api_contract/test_osal_headers.py
git commit -m "feat: define public osal headers"
```

### Task 5: Define Public HAL Headers

**Files:**
- Create: `hal/CMakeLists.txt`
- Create: `hal/include/ep_hal_types.h`
- Create: `hal/include/ep_hal_err.h`
- Create: `hal/include/ep_hal_gpio.h`
- Create: `hal/include/ep_hal_uart.h`
- Create: `hal/include/ep_hal_i2c.h`
- Create: `hal/include/ep_hal_spi.h`
- Create: `hal/include/ep_hal_pwm.h`
- Create: `hal/include/ep_hal_adc.h`
- Create: `tests/api_contract/test_hal_headers.py`

- [ ] **Step 1: Write the failing HAL header contract test**

Create `tests/api_contract/test_hal_headers.py` with:

```python
from pathlib import Path


def test_hal_headers_expose_ep_handle_api():
    uart = Path("hal/include/ep_hal_uart.h").read_text()
    gpio = Path("hal/include/ep_hal_gpio.h").read_text()
    assert "ep_uart_t" in uart
    assert "ep_uart_open" in uart
    assert "ep_gpio_t" in gpio
    assert "ep_gpio_write" in gpio
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api_contract/test_hal_headers.py -v`
Expected: FAIL because the headers do not exist.

- [ ] **Step 3: Write the public HAL headers**

Create `hal/CMakeLists.txt` with:

```cmake
add_library(ep_hal INTERFACE)

target_include_directories(ep_hal
  INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
```

Create `hal/include/ep_hal_types.h` with:

```c
#ifndef EP_HAL_TYPES_H
#define EP_HAL_TYPES_H

typedef struct ep_gpio ep_gpio_t;
typedef struct ep_uart ep_uart_t;
typedef struct ep_i2c ep_i2c_t;
typedef struct ep_spi ep_spi_t;
typedef struct ep_pwm ep_pwm_t;
typedef struct ep_adc ep_adc_t;

#endif
```

Create `hal/include/ep_hal_err.h` with:

```c
#ifndef EP_HAL_ERR_H
#define EP_HAL_ERR_H

#include "ep_osal_err.h"

#endif
```

Create `hal/include/ep_hal_gpio.h` with:

```c
#ifndef EP_HAL_GPIO_H
#define EP_HAL_GPIO_H

#include "ep_hal_types.h"

typedef enum {
    EP_GPIO_INPUT = 0,
    EP_GPIO_OUTPUT = 1
} ep_gpio_dir_e;

int ep_gpio_request(ep_gpio_t **gpio, const char *name);
int ep_gpio_set_direction(ep_gpio_t *gpio, ep_gpio_dir_e dir);
int ep_gpio_write(ep_gpio_t *gpio, int value);
int ep_gpio_read(ep_gpio_t *gpio, int *value);

#endif
```

Create `hal/include/ep_hal_uart.h` with:

```c
#ifndef EP_HAL_UART_H
#define EP_HAL_UART_H

#include <stddef.h>
#include "ep_hal_types.h"

int ep_uart_open(ep_uart_t **uart, const char *name);
int ep_uart_write(ep_uart_t *uart, const void *buf, size_t len);
int ep_uart_read(ep_uart_t *uart, void *buf, size_t len, unsigned int timeout_ms);
int ep_uart_close(ep_uart_t *uart);

#endif
```

Create `hal/include/ep_hal_i2c.h` with:

```c
#ifndef EP_HAL_I2C_H
#define EP_HAL_I2C_H

#include <stddef.h>
#include <stdint.h>
#include "ep_hal_types.h"

int ep_i2c_open(ep_i2c_t **bus, const char *name);
int ep_i2c_write(ep_i2c_t *bus, uint16_t addr, const void *buf, size_t len);
int ep_i2c_read(ep_i2c_t *bus, uint16_t addr, void *buf, size_t len);

#endif
```

Create `hal/include/ep_hal_spi.h` with:

```c
#ifndef EP_HAL_SPI_H
#define EP_HAL_SPI_H

#include <stddef.h>
#include "ep_hal_types.h"

int ep_spi_open(ep_spi_t **bus, const char *name);
int ep_spi_transfer(ep_spi_t *bus, const void *tx_buf, void *rx_buf, size_t len);

#endif
```

Create `hal/include/ep_hal_pwm.h` with:

```c
#ifndef EP_HAL_PWM_H
#define EP_HAL_PWM_H

#include "ep_hal_types.h"

int ep_pwm_open(ep_pwm_t **pwm, const char *name);
int ep_pwm_set(ep_pwm_t *pwm, unsigned int period_ns, unsigned int duty_ns);

#endif
```

Create `hal/include/ep_hal_adc.h` with:

```c
#ifndef EP_HAL_ADC_H
#define EP_HAL_ADC_H

#include <stdint.h>
#include "ep_hal_types.h"

int ep_adc_open(ep_adc_t **adc, const char *name);
int ep_adc_read(ep_adc_t *adc, uint32_t *value);

#endif
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api_contract/test_hal_headers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add hal/CMakeLists.txt hal/include tests/api_contract/test_hal_headers.py
git commit -m "feat: define public hal headers"
```

### Task 6: Add RTOS and Linux Platform Skeletons

**Files:**
- Create: `platforms/rtos/demo_family/CMakeLists.txt`
- Create: `platforms/rtos/demo_family/startup/app_start.c`
- Create: `platforms/rtos/demo_family/osal_port/ep_rtos_osal_stub.c`
- Create: `platforms/rtos/demo_family/hal_port/ep_rtos_hal_stub.c`
- Create: `platforms/rtos/demo_family/component_port/ep_rtos_component_stub.c`
- Create: `platforms/rtos/demo_family/board/demo_board/.gitkeep`
- Create: `platforms/rtos/demo_family/config/demo_board.cmake`
- Create: `platforms/linux/demo_family/CMakeLists.txt`
- Create: `platforms/linux/demo_family/startup/main.c`
- Create: `platforms/linux/demo_family/osal_port/ep_linux_osal_stub.c`
- Create: `platforms/linux/demo_family/hal_port/ep_linux_hal_stub.c`
- Create: `platforms/linux/demo_family/component_port/ep_linux_component_stub.c`
- Create: `platforms/linux/demo_family/board/demo_board/.gitkeep`
- Create: `platforms/linux/demo_family/config/demo_board.cmake`
- Create: `tests/api_contract/test_platform_bootstrap.py`

- [ ] **Step 1: Write the failing platform skeleton test**

Create `tests/api_contract/test_platform_bootstrap.py` with:

```python
from pathlib import Path


def test_both_platform_families_have_bootstrap_entries():
    rtos = Path("platforms/rtos/demo_family/startup/app_start.c").read_text()
    linux = Path("platforms/linux/demo_family/startup/main.c").read_text()
    assert "ep_platform_boot" in rtos
    assert "ep_framework_start" in rtos
    assert "ep_platform_boot" in linux
    assert "ep_framework_start" in linux
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api_contract/test_platform_bootstrap.py -v`
Expected: FAIL because the files do not exist.

- [ ] **Step 3: Write the platform skeletons**

Create `platforms/rtos/demo_family/CMakeLists.txt` with:

```cmake
add_library(ep_platform_rtos_demo STATIC
  startup/app_start.c
  osal_port/ep_rtos_osal_stub.c
  hal_port/ep_rtos_hal_stub.c
  component_port/ep_rtos_component_stub.c
)
```

Create `platforms/rtos/demo_family/startup/app_start.c` with:

```c
#include "ep_framework.h"

int ep_platform_boot(void)
{
    return 0;
}

int vendor_app_start(void)
{
    return ep_framework_start();
}
```

Create `platforms/rtos/demo_family/osal_port/ep_rtos_osal_stub.c` with:

```c
int ep_rtos_osal_stub(void)
{
    return 0;
}
```

Create `platforms/rtos/demo_family/hal_port/ep_rtos_hal_stub.c` with:

```c
int ep_rtos_hal_stub(void)
{
    return 0;
}
```

Create `platforms/rtos/demo_family/component_port/ep_rtos_component_stub.c` with:

```c
int ep_rtos_component_stub(void)
{
    return 0;
}
```

Create `platforms/rtos/demo_family/config/demo_board.cmake` with:

```cmake
set(EP_PLATFORM_FAMILY "rtos")
set(EP_PLATFORM_NAME "demo_family")
set(EP_BOARD_NAME "demo_board")
```

Create `platforms/linux/demo_family/CMakeLists.txt` with:

```cmake
add_executable(ep_platform_linux_demo
  startup/main.c
  osal_port/ep_linux_osal_stub.c
  hal_port/ep_linux_hal_stub.c
  component_port/ep_linux_component_stub.c
)
```

Create `platforms/linux/demo_family/startup/main.c` with:

```c
#include "ep_framework.h"

int ep_platform_boot(void)
{
    return 0;
}

int main(void)
{
    return ep_framework_start();
}
```

Create `platforms/linux/demo_family/osal_port/ep_linux_osal_stub.c` with:

```c
int ep_linux_osal_stub(void)
{
    return 0;
}
```

Create `platforms/linux/demo_family/hal_port/ep_linux_hal_stub.c` with:

```c
int ep_linux_hal_stub(void)
{
    return 0;
}
```

Create `platforms/linux/demo_family/component_port/ep_linux_component_stub.c` with:

```c
int ep_linux_component_stub(void)
{
    return 0;
}
```

Create `platforms/linux/demo_family/config/demo_board.cmake` with:

```cmake
set(EP_PLATFORM_FAMILY "linux")
set(EP_PLATFORM_NAME "demo_family")
set(EP_BOARD_NAME "demo_board")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api_contract/test_platform_bootstrap.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add platforms/rtos/demo_family platforms/linux/demo_family tests/api_contract/test_platform_bootstrap.py
git commit -m "feat: add rtos and linux platform skeletons"
```

### Task 7: Add Repository Workflow Files for GitHub

**Files:**
- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/workflows/ci.yml`
- Create: `CODEOWNERS`
- Create: `tests/host_unit/test_repo_workflow_files.py`

- [ ] **Step 1: Write the failing repository workflow test**

Create `tests/host_unit/test_repo_workflow_files.py` with:

```python
from pathlib import Path


def test_github_workflow_files_exist():
    expected = [
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/workflows/ci.yml",
        "CODEOWNERS",
    ]
    missing = [path for path in expected if not Path(path).exists()]
    assert not missing, f"Missing files: {missing}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/host_unit/test_repo_workflow_files.py -v`
Expected: FAIL because the files do not exist.

- [ ] **Step 3: Write the GitHub workflow files**

Create `CODEOWNERS` with:

```text
* @baotouyu
```

Create `.github/PULL_REQUEST_TEMPLATE.md` with:

```markdown
## Summary

- 

## Validation

- [ ] Unit tests
- [ ] Contract tests
- [ ] Target smoke tests
```

Create `.github/ISSUE_TEMPLATE/feature_request.md` with:

```markdown
---
name: Feature request
about: Propose a framework feature
title: ""
labels: enhancement
assignees: ""
---

## Problem

## Proposed solution

## Platform impact
```

Create `.github/ISSUE_TEMPLATE/bug_report.md` with:

```markdown
---
name: Bug report
about: Report a framework defect
title: ""
labels: bug
assignees: ""
---

## Summary

## Steps to reproduce

## Expected behavior

## Platform impact
```

Create `.github/workflows/ci.yml` with:

```yaml
name: ci

on:
  push:
  pull_request:

jobs:
  host-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install pytest
      - run: pytest tests/host_unit tests/api_contract -v
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/host_unit/test_repo_workflow_files.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .github CODEOWNERS tests/host_unit/test_repo_workflow_files.py
git commit -m "chore: add github workflow templates"
```

### Task 8: Initialize Git and Publish the Repository

**Files:**
- Modify: local git metadata
- Modify: remote `origin`

- [ ] **Step 1: Verify the repository is not already initialized**

Run: `git rev-parse --is-inside-work-tree`
Expected: exit non-zero or no output before initialization.

- [ ] **Step 2: Initialize git on the local repository**

Run:

```bash
git init -b main
```

Expected: `Initialized empty Git repository`

- [ ] **Step 3: Add the GitHub remote**

Run:

```bash
git remote add origin https://github.com/baotouyu/embedded-platform-core.git
git remote -v
```

Expected output includes:

```text
origin  https://github.com/baotouyu/embedded-platform-core.git (fetch)
origin  https://github.com/baotouyu/embedded-platform-core.git (push)
```

- [ ] **Step 4: Verify the branch and remote push**

Run:

```bash
git branch --show-current
git push -u origin main
```

Expected:

- current branch is `main`
- push succeeds and sets upstream

- [ ] **Step 5: Commit**

```bash
git status --short
```

Expected: clean working tree after the final push.

## Self-Review

### Spec coverage

- Repository structure: covered by Task 1.
- Build direction and CMake bootstrap: covered by Task 2.
- Core lifecycle and startup orchestration: covered by Task 3.
- OSAL API surface: covered by Task 4.
- HAL API surface: covered by Task 5.
- RTOS/Linux platform skeletons: covered by Task 6.
- GitHub workflow expectations: covered by Task 7.
- Git initialization and publication: covered by Task 8.

No spec sections are left without a corresponding task in this bootstrap plan.

### Placeholder scan

- The plan contains no `TODO` or `TBD` placeholders.
- Each task names concrete files and concrete commands.
- Each task includes concrete code snippets or expected file contents where code changes are required.

### Type consistency

- The plan consistently uses `ep_framework_init()`, `ep_framework_start()`, `ep_platform_boot()`, and `app_main()`.
- The OSAL and HAL naming remains consistently prefixed with `ep_`.
- Platform family names are consistently `rtos` and `linux`.
