# 平台路径实现计划

> 执行说明：按任务逐步实现，每一步用复选框记录状态。

**目标：** 增加第一版平台路径接口和资源目录规范，让配置文件、资源根目录、图片、字体、主题路径有统一入口。

**架构：** 公共接口放在 `platforms/include/ep_platform_paths.h`，host 实现放在 `platforms/host/posix/paths/ep_host_platform_paths.c`。第一版只做路径返回和路径拼接，不改 LVGL 加载逻辑、不做资源扫描、不做打包。

**技术栈：** C11、CMake、pytest、host/macOS POSIX 平台。

---

### Task 1: 公共路径 API 和 host 实现

**文件：**
- 新增：`platforms/include/ep_platform_paths.h`
- 新增：`platforms/host/posix/paths/ep_host_platform_paths.c`
- 修改：`platforms/host/posix/CMakeLists.txt`
- 测试：`tests/api_contract/test_platform_paths_headers.py`
- 测试：`tests/host_unit/test_host_platform_paths.py`

- [x] **步骤 1：写公共头文件契约测试**

验证 `ep_platform_paths.h` 存在、可重复 include、能引用配置路径、资源根路径和资源拼接函数。

- [x] **步骤 2：运行测试确认失败**

运行：`pytest tests/api_contract/test_platform_paths_headers.py -v`

预期：失败，因为头文件还不存在。

- [x] **步骤 3：写 host 路径行为测试**

验证 host 默认配置路径为 `config/profiles/host.cfg`，资源根目录为 `resources/host`，并能拼接图片、字体、主题路径。

- [x] **步骤 4：运行测试确认失败**

运行：`pytest tests/host_unit/test_host_platform_paths.py -v`

预期：失败，因为 host 实现还不存在。

- [x] **步骤 5：实现最小路径 API**

实现固定字符串返回和安全路径拼接，参数非法或缓冲区不足时返回 `EP_ERR_INVAL`。

- [x] **步骤 6：接入 host CMake**

把 host 路径实现加入 `ep_platform_host_posix`，并链接已有 `ep_platform_api`。

- [x] **步骤 7：运行相关测试**

运行：`pytest tests/api_contract/test_platform_paths_headers.py tests/host_unit/test_host_platform_paths.py tests/api_contract/test_platform_bootstrap.py -v`

预期：通过。

### Task 2: 资源目录和文档

**文件：**
- 新增：`resources/common/images/.gitkeep`
- 新增：`resources/common/fonts/.gitkeep`
- 新增：`resources/common/themes/.gitkeep`
- 新增：`resources/host/images/.gitkeep`
- 新增：`resources/host/fonts/.gitkeep`
- 新增：`resources/host/themes/.gitkeep`
- 修改：`docs/architecture/repository-layout.md`
- 修改：`docs/development/roadmap.md`
- 合并后同步 Wiki：`平台适配计划.md`
- 合并后同步 Wiki：`当前进度.md`

- [x] **步骤 1：新增资源目录**

建立 common 和 host 的 images/fonts/themes 目录。

- [x] **步骤 2：更新中文文档**

说明资源目录职责和下一步建议。Wiki 在 PR 合并后同步，避免 Wiki 先于主仓库描述未合并内容。

- [x] **步骤 3：运行文档相关测试**

运行：`pytest tests/host_unit/test_repository_layout.py -v`

预期：通过。
