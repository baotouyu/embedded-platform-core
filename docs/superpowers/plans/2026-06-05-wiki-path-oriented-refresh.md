# Wiki Path Oriented Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按真实代码路径重整平台适配文档和 Wiki，让读者能从项目结构、Luban-Lite 接入、OSAL/HAL/device API、板级验证一路读下来。

**Architecture:** 主仓库 `docs/porting/` 作为详细源头，GitHub Wiki 作为阅读入口和阶段总结。源头文档写清接口、路径和边界；Wiki 按阅读顺序组织同一批信息，并明确当前平台适配已经进入业务开发阶段。

**Tech Stack:** Markdown、GitHub Wiki、GitHub PR、现有 `docs/porting/` 文档体系。

---

### Task 1: Refresh Porting Source Docs

**Files:**
- Modify: `docs/porting/README.md`
- Modify: `docs/porting/platform-bringup-checklist.md`
- Modify: `docs/porting/luban-lite-build-and-link.md`
- Modify: `docs/porting/luban-lite-compatibility-overview.md`
- Modify: `docs/porting/device-compatibility-reference.md`
- Modify: `docs/porting/ki-141103-480p-smoke-test.md`

- [x] **Step 1: Align source docs with current platform state**

Update old “next SPI/ADC/SD” wording to the current decision:

```text
平台基础适配已经完成，可以进入业务应用开发。
SPI/ADC 当前不用，按需再补。
SD 卡文件系统使用 SDK 已提供的 open/read/write 路线。
display/touch 由各芯片 LVGL port 管理。
电源板 UART2 协议后续按业务协议单独实现。
```

- [x] **Step 2: Add concrete repository paths**

Each core concept must mention the exact path, including:

```text
app/main.c
app/include/app_main.h
core/src/ep_framework.c
osal/include/
hal/include/
components/device/include/ep_device.h
platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c
platforms/rtos/demo_family/hal_port/
platforms/rtos/demo_family/component_port/ep_rtos_default_devices.c
targets/artinchip_d12x_lubanlite_ki_141103_480p.yaml
third_party/sdk/sdk-artinchip-luban-lite/targets/artinchip_d12x_lubanlite_ki_141103_480p.env
third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/application/rt-thread/ep_app/
out/firmware/artinchip_d12x_lubanlite_ki_141103_480p/
```

- [x] **Step 3: Verify Markdown**

Run:

```bash
git diff --check
```

Expected: no whitespace errors.

### Task 2: Refresh Wiki Pages

**Files:**
- Modify: `/tmp/embedded-platform-core.wiki/Home.md`
- Modify: `/tmp/embedded-platform-core.wiki/项目框架.md`
- Modify: `/tmp/embedded-platform-core.wiki/平台适配计划.md`
- Modify: `/tmp/embedded-platform-core.wiki/Luban-Lite接入总览.md`
- Modify: `/tmp/embedded-platform-core.wiki/Luban-Lite兼容层.md`
- Modify: `/tmp/embedded-platform-core.wiki/设备兼容层API参考.md`
- Modify: `/tmp/embedded-platform-core.wiki/KI-141103-480p冒烟测试.md`
- Modify: `/tmp/embedded-platform-core.wiki/当前进度.md`

- [x] **Step 1: Rewrite Home as a reading map**

Make `Home.md` the entry point:

```text
先看结论
阅读顺序
按任务查页面
当前能做什么
哪些能力暂不做
```

- [x] **Step 2: Sync detailed pages**

Sync path-oriented source content into Wiki, while keeping Wiki pages easier to scan.

- [x] **Step 3: Verify Wiki Markdown**

Run:

```bash
git -C /tmp/embedded-platform-core.wiki diff --check
```

Expected: no whitespace errors.

### Task 3: Commit, PR, and Wiki Push

**Files:**
- Main repo docs commit on branch `docs/wiki-path-oriented-refresh`
- Wiki commit on `/tmp/embedded-platform-core.wiki`

- [x] **Step 1: Validate target metadata**

Run:

```bash
./build.sh validate-targets
```

Expected: target validation succeeds.

- [x] **Step 2: Commit main docs**

Run:

```bash
git add docs/porting docs/superpowers/plans/2026-06-05-wiki-path-oriented-refresh.md
git commit -m "docs: 重整平台适配文档阅读顺序"
```

- [x] **Step 3: Push branch and create Chinese PR**

Run:

```bash
git push -u origin docs/wiki-path-oriented-refresh
gh pr create --title "docs: 重整平台适配文档阅读顺序" --body-file /tmp/wiki-path-oriented-refresh-pr.md
```

- [x] **Step 4: Commit and push Wiki**

Run:

```bash
git -C /tmp/embedded-platform-core.wiki add .
git -C /tmp/embedded-platform-core.wiki commit -m "docs: 重整 Wiki 阅读顺序和平台状态"
git -C /tmp/embedded-platform-core.wiki push
```
