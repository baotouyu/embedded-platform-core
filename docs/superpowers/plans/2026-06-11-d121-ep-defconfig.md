# D121 EP Defconfig Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the KI-141103-480p D121 target boot the EP home UI without enabling Luban-Lite's LVGL demo or startup UI.

**Architecture:** Keep the vendor `helloworld` defconfig unchanged and add an EP-specific defconfig for this board. The target descriptor and SDK target environment point at the EP defconfig, while the existing bridge still calls `ep_lubanlite_app_main()`.

**Tech Stack:** Luban-Lite RT-Thread defconfig, target YAML descriptors, SDK target env files, pytest host-unit checks.

---

### Task 1: Add Regression Tests

**Files:**
- Modify: `tests/host_unit/test_target_validation.py`

- [ ] **Step 1: Write the failing tests**

Add checks that the KI-141103-480p target uses `d12x_KI-141103-480p_rt-thread_ep_app_defconfig`, that the SDK env file points at the same defconfig, and that this defconfig does not contain enabled Luban-Lite demo/startup UI symbols.

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/host_unit/test_target_validation.py -q`

Expected: failure because the target still references `d12x_KI-141103-480p_rt-thread_helloworld_defconfig` and the EP defconfig does not exist yet.

### Task 2: Add EP Defconfig And Switch Target

**Files:**
- Create: `third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/target/configs/d12x_KI-141103-480p_rt-thread_ep_app_defconfig`
- Modify: `targets/artinchip_d12x_lubanlite_ki_141103_480p.yaml`
- Modify: `third_party/sdk/sdk-artinchip-luban-lite/targets/artinchip_d12x_lubanlite_ki_141103_480p.env`

- [ ] **Step 1: Create the EP defconfig**

Copy the board's existing `helloworld` defconfig, change `CONFIG_PRJ_DEFCONFIG_FILENAME`, remove enabled `CONFIG_AIC_LVGL_DEMO`, `CONFIG_AIC_LVGL_DEMO_HUB_DEMO`, and `CONFIG_AIC_STARTUP_UI_SHOW`, and explicitly keep `CONFIG_LPKG_USING_LVGL=y` plus the existing LVGL v9/display/touch/filesystem settings.

- [ ] **Step 2: Switch target descriptors**

Set both `sdk_config.defconfig` in the YAML and `DEFCONFIG` in the SDK env file to `d12x_KI-141103-480p_rt-thread_ep_app_defconfig`.

- [ ] **Step 3: Run tests to verify pass**

Run: `pytest tests/host_unit/test_target_validation.py -q`

Expected: pass.

### Task 3: Verify Export And Firmware Path

**Files:**
- No source edits.

- [ ] **Step 1: Run focused tests**

Run: `pytest tests/host_unit/test_target_validation.py tests/host_unit/test_target_firmware_build.py -q`

Expected: pass.

- [ ] **Step 2: Run script syntax checks**

Run: `sh -n tools/scripts/export_sdk_ep_package.sh tools/scripts/export_ep_package.sh third_party/sdk/sdk-artinchip-luban-lite/scripts/build_firmware.sh`

Expected: exit 0.

- [ ] **Step 3: Export package and build firmware**

Run the existing package export and SDK build for `artinchip_d12x_lubanlite_ki_141103_480p`.

Expected: build output uses `d12x_KI-141103-480p_rt-thread_ep_app_defconfig`, installs EP resources under `/rodata/ep/resources/images` and `/data/ep/resources/recipe`, and does not install `demo_hub` assets.
