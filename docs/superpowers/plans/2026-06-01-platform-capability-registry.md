# Platform Capability Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增加第一版平台能力注册表，让每个平台可以声明并查询自己支持的能力。

**Architecture:** 公共接口放在 `platforms/include/ep_platform_capability.h`，平台实现放在各自平台目录。第一版使用静态能力表，不做动态注册，不引入配置文件。

**Tech Stack:** C11、CMake、pytest、host/macOS POSIX 平台。

---

### Task 1: 公共 API 和 host 实现

**Files:**
- Create: `platforms/include/ep_platform_capability.h`
- Create: `platforms/host/posix/capability/ep_host_platform_capability.c`
- Modify: `platforms/host/posix/CMakeLists.txt`
- Test: `tests/api_contract/test_platform_capability_headers.py`
- Test: `tests/host_unit/test_host_platform_capability.py`

- [ ] **Step 1: 写公共头文件契约测试**

新增测试，要求 `ep_platform_capability.h` 存在、可重复 include、能引用能力枚举和查询函数。

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/api_contract/test_platform_capability_headers.py -v`

Expected: FAIL，因为头文件还不存在。

- [ ] **Step 3: 写 host 能力查询测试**

新增 host smoke 测试，编译 `ep_host_platform_capability.c` 并查询 host 支持的能力。

- [ ] **Step 4: 运行测试确认失败**

Run: `pytest tests/host_unit/test_host_platform_capability.py -v`

Expected: FAIL，因为实现文件还不存在。

- [ ] **Step 5: 实现最小 API**

实现 `ep_platform_has_capability()` 和 `ep_platform_capability_name()`。

- [ ] **Step 6: 接入 host CMake**

把 host 能力实现加入 `ep_platform_host_posix`，并把 `platforms/include` 加入 include path。

- [ ] **Step 7: 运行相关测试**

Run: `pytest tests/api_contract/test_platform_capability_headers.py tests/host_unit/test_host_platform_capability.py tests/api_contract/test_platform_bootstrap.py tests/host_unit/test_host_posix_bootstrap.py -v`

Expected: PASS。

### Task 2: 文档和 Wiki

**Files:**
- Modify: `docs/architecture/project-overview.md`
- Modify: `docs/development/roadmap.md`
- Modify: `docs/architecture/repository-layout.md`
- Modify: Wiki `当前进度.md`
- Modify: Wiki `项目框架.md`

- [ ] **Step 1: 更新主仓库中文文档**

说明 `platforms/include` 是平台公共接口目录，并把平台能力注册表从“下一步”改成“已完成第一版”。

- [ ] **Step 2: 更新 Wiki 草稿**

同步 `当前进度` 和 `项目框架`。

- [ ] **Step 3: 运行文档相关测试**

Run: `pytest tests/host_unit/test_repository_layout.py -v`

Expected: PASS。
