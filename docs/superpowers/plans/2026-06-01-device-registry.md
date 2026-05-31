# Device Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增加第一版设备管理组件，用静态容量注册表描述系统里有哪些设备、设备类型、状态和关联平台能力。

**Architecture:** 组件放在 `components/device/`，公共头文件保持平台无关，只依赖 `ep_platform_capability.h` 的能力枚举。第一版不做真实驱动、不做 open/read/write/ioctl、不使用动态内存。

**Tech Stack:** C11、CMake、pytest、host/macOS smoke test。

---

### Task 1: 公共头文件和组件行为

**Files:**
- Create: `components/device/include/ep_device.h`
- Create: `components/device/src/ep_device.c`
- Create: `components/device/CMakeLists.txt`
- Modify: `CMakeLists.txt`
- Test: `tests/api_contract/test_device_headers.py`
- Test: `tests/host_unit/test_host_device_registry.py`

- [ ] **Step 1: 写设备头文件契约测试**

验证 `ep_device.h` 存在、可重复 include、能引用设备类型、状态、描述结构和函数指针。

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/api_contract/test_device_headers.py -v`

Expected: FAIL，因为头文件还不存在。

- [ ] **Step 3: 写设备注册表行为测试**

验证初始化前返回 `EP_ERR_UNSUPPORTED`，初始化后可以注册设备、按名字查找、按类型和索引查找、读取状态、处理重复名字和容量上限。

- [ ] **Step 4: 运行测试确认失败**

Run: `pytest tests/host_unit/test_host_device_registry.py -v`

Expected: FAIL，因为组件实现还不存在。

- [ ] **Step 5: 实现最小设备注册表**

实现固定容量数组、参数校验、设备复制存储、查找和状态查询。

- [ ] **Step 6: 接入 CMake**

新增 `ep_components_device`，顶层 `CMakeLists.txt` 加入 `add_subdirectory(components/device)`，组件链接 `ep_platform_api`。

- [ ] **Step 7: 运行相关测试**

Run: `pytest tests/api_contract/test_device_headers.py tests/host_unit/test_host_device_registry.py tests/host_unit/test_cmake_layout.py -v`

Expected: PASS。

### Task 2: 文档和 Wiki

**Files:**
- Modify: `docs/architecture/project-overview.md`
- Modify: `docs/development/roadmap.md`
- Modify: `docs/architecture/repository-layout.md`
- Modify: Wiki `组件说明.md`
- Modify: Wiki `当前进度.md`

- [ ] **Step 1: 更新主仓库中文文档**

说明设备管理组件第一版已完成，下一步转向平台配置和资源管理。

- [ ] **Step 2: 更新 Wiki 草稿**

同步组件说明和当前进度。

- [ ] **Step 3: 运行文档相关测试**

Run: `pytest tests/host_unit/test_repository_layout.py -v`

Expected: PASS。
