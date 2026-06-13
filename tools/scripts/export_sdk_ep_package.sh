#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/target_descriptor.sh"
. "$SCRIPT_DIR/target_sdk_resolver.sh"

REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=
TARGET_FILE=
SDK_DIR=
OUTPUT_DIR=out/ep
CLEAN=0

print_help() {
    cat <<EOF
用法:
  tools/scripts/export_sdk_ep_package.sh --target <名称> --sdk-dir <路径> [参数]

参数:
  --repo-root <路径>   仓库根目录，默认自动使用当前脚本所在仓库
  --target <名称>      target 名称，对应 targets/<target>.yaml
  --target-file <路径> target 描述文件，默认使用 targets/<target>.yaml
  --sdk-dir <路径>     已准备好的 SDK adapter 根目录
  --output-dir <路径>  输出父目录，脚本会生成 <路径>/<target>
  --clean             导出前删除已有 target 输出目录
  -h, --help          显示帮助
EOF
}

die() {
    printf '%s\n' "$1" >&2
    exit 1
}

json_escape() {
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

copy_headers() {
    repo_root=$1
    package_root=$2

    header_dirs="
core/include
app/include
app/selftest
app/services
app/ui
components/log/include
components/recipe_parser/include
components/config/include
components/event/include
components/timer/include
components/file/include
components/device/include
components/ui/include
osal/include
hal/include
platforms/include
third_party/external/cjson
third_party/external/sqlite
"

    missing=""
    for dir in $header_dirs; do
        [ -d "$repo_root/$dir" ] || missing="${missing}
- $repo_root/$dir"
    done

    [ -z "$missing" ] || die "缺少头文件目录：$missing"

    for dir in $header_dirs; do
        find "$repo_root/$dir" -type f -name '*.h' -print | while IFS= read -r header; do
            cp -p "$header" "$package_root/include/$(basename -- "$header")"
        done
    done
}

copy_resources() {
    repo_root=$1
    package_root=$2

    mkdir -p "$package_root/resources/images" "$package_root/resources/recipe"

    if [ -d "$repo_root/resources/host/images" ]; then
        cp -R "$repo_root/resources/host/images/." "$package_root/resources/images/"
    fi

    if [ -d "$repo_root/resources/host/recipe" ]; then
        cp -R "$repo_root/resources/host/recipe/." "$package_root/resources/recipe/"
    fi
}

append_luban_lvgl_include_flags() {
    luban_root=$1

    for dir in \
        "$luban_root/packages/artinchip/lvgl-ui/lvgl_v9" \
        "$luban_root/packages/artinchip/lvgl-ui/lvgl_v9/lvgl" \
        "$luban_root/packages/artinchip/lvgl-ui/lvgl_v8" \
        "$luban_root/packages/artinchip/lvgl-ui/lvgl_v8/lvgl"
    do
        [ -d "$dir" ] || continue
        printf '%s\n' "-I$dir"
    done
}

append_luban_lvgl_custom_include_flags() {
    luban_root=$1
    rtconfig=$2

    [ -f "$rtconfig" ] || return 0

    lvgl_demo_dirs="
AIC_LVGL_BASE_DEMO:aic_demo/base_demo
AIC_LVGL_DM_DAEMON:aic_demo/dm_daemon
AIC_LVGL_METER_DEMO:aic_demo/meter_demo
AIC_LVGL_DEMO_HUB_DEMO:aic_demo/demo_hub
AIC_LVGL_LAUNCHER_DEMO:aic_demo/launcher_demo
AIC_LVGL_DASHBOARD_DEMO:aic_demo/dashboard_demo
AIC_LVGL_SERIAL_DEMO:aic_demo/serial_com_demo
AIC_LVGL_ELEVATOR_DEMO:aic_demo/elevator_demo
AIC_LVGL_SLIDE_DEMO:aic_demo/slide_demo
AIC_LVGL_INPUT_TEST_DEMO:aic_demo/input_test_demo
AIC_LVGL_GIF_DEMO:aic_demo/gif_demo
AIC_LVGL_RTP_RECALIBRATE_DEMO:aic_demo/rtp_recalibrate_demo
AIC_LVGL_USB_OSD_DEMO:aic_demo/usb_osd_demo
AIC_LVGL_IMAGE_DEMO:aic_demo/image_demo
AIC_LVGL_DOUBLE_DISP_DEMO:aic_demo/double_disp_demo
AIC_SPI_SCREEN_DEMO:aic_demo/spi_screen_demo
AIC_LVGL_OTA_DEMO:aic_demo/ota_demo
AIC_LVGL_AI_EYES_DEMO:aic_demo/ai_eyes_demo
AIC_LLM_DEMO:aic_demo/llm_demo
AIC_IMG_ROLLER_DEMO:aic_demo/aic_widget_demo/img_roller_demo
AIC_PLAYER_DEMO:aic_demo/aic_widget_demo/aic_player_demo
AIC_APNG_DEMO:aic_demo/aic_widget_demo/aic_apng_demo
AIC_IMAGE_USAGE_DEMO:aic_demo/aic_widget_demo/img_usage_demo
AIC_SWIPE_V1_DEMO:aic_demo/aic_widget_demo/swipe_v1_demo
"

    printf '%s\n' "$lvgl_demo_dirs" | while IFS=: read -r symbol rel_dir; do
        [ -n "$symbol" ] || continue
        grep -q "^#define $symbol\\b" "$rtconfig" || continue
        dir=$luban_root/packages/artinchip/lvgl-ui/$rel_dir
        [ -d "$dir" ] || continue
        printf '%s\n' "-I$dir"
    done
}

resolve_luban_root() {
    sdk_dir=$1

    if [ -n "${LUBAN_LITE_ROOT:-}" ]; then
        printf '%s\n' "$LUBAN_LITE_ROOT"
        return 0
    fi

    printf '%s\n' "$sdk_dir/upstream/luban-lite"
}

find_tool() {
    luban_root=$1
    tool=$2

    candidate=$luban_root/toolchain/bin/$tool
    [ -x "$candidate" ] || die "缺少 SDK 交叉工具：$candidate"
    printf '%s\n' "$candidate"
}

compile_source() {
    cc=$1
    source=$2
    object=$3
    shift 3

    mkdir -p "$(dirname "$object")"
    "$cc" "$@" -c "$source" -o "$object"
}

extract_rtconfig_cflags() {
    luban_root=$1
    chip=$2
    rtconfig_py=$luban_root/bsp/artinchip/sys/$chip/rtconfig.py

    [ -f "$rtconfig_py" ] || return 0

    python3 - "$rtconfig_py" <<'PY'
import os
import runpy
import sys

path = sys.argv[1]
os.environ.setdefault("PRJ_KERNEL", "rt-thread")
os.environ.setdefault("PRJ_TOOLCHAIN_VER", "V2.6.1")
namespace = runpy.run_path(path)
print(namespace.get("CFLAGS", ""))
PY
}

ensure_luban_configured() {
    luban_root=$1
    target_file=$2
    rtconfig=$3

    defconfig=$(td_trim "$(td_read_section_value "$target_file" "sdk_config" "defconfig")")
    [ -n "$defconfig" ] || return 0
    if [ -f "$rtconfig" ] && grep -q "^#define PRJ_DEFCONFIG_FILENAME \"$defconfig\"$" "$rtconfig"; then
        return 0
    fi
    [ -f "$luban_root/tools/onestep.sh" ] || return 0

    printf '配置 Luban-Lite：%s\n' "$defconfig"
    bash -c 'cd "$0" || exit 1; . tools/onestep.sh; lunch "$1" || exit 1' "$luban_root" "$defconfig"
}

write_manifest() {
    manifest=$1
    package_root=$2

    target_platform_family=
    target_platform_vendor=
    target_platform_sdk_family=
    target_platform_chip=
    target_platform_board=
    target_platform_kernel=
    target_sdk_name=
    target_sdk_repo=
    target_sdk_ref=
    target_toolchain_source=
    target_ui_lvgl_provider=
    target_ui_lvgl_note=

    td_validate_declared_target "$TARGET_FILE" "$TARGET"
    target_platform_family=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "family")")
    target_platform_vendor=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "vendor")")
    target_platform_sdk_family=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "sdk_family")")
    target_platform_chip=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "chip")")
    target_platform_board=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "board")")
    target_platform_kernel=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "kernel")")
    target_sdk_name=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "name")")
    target_sdk_repo=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "repo")")
    target_sdk_ref=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "ref")")
    target_toolchain_source=$(td_trim "$(td_read_section_value "$TARGET_FILE" "toolchain" "source")")
    target_ui_lvgl_provider=$(td_trim "$(td_read_section_value "$TARGET_FILE" "ui" "lvgl_provider")")
    target_ui_lvgl_note=$(td_trim "$(td_read_section_value "$TARGET_FILE" "ui" "lvgl_note")")

    {
        printf '{\n'
        printf '  "package": "ep_app_core",\n'
        printf '  "target": "%s",\n' "$(json_escape "$TARGET")"
        printf '  "format": "static-library",\n'
        printf '  "library": "lib/libep_app_core.a",\n'
        printf '  "platform": {\n'
        printf '    "family": "%s",\n' "$(json_escape "$target_platform_family")"
        printf '    "vendor": "%s",\n' "$(json_escape "$target_platform_vendor")"
        printf '    "sdk_family": "%s",\n' "$(json_escape "$target_platform_sdk_family")"
        printf '    "chip": "%s",\n' "$(json_escape "$target_platform_chip")"
        printf '    "board": "%s",\n' "$(json_escape "$target_platform_board")"
        printf '    "kernel": "%s"\n' "$(json_escape "$target_platform_kernel")"
        printf '  },\n'
        printf '  "sdk": {\n'
        printf '    "name": "%s",\n' "$(json_escape "$target_sdk_name")"
        printf '    "repo": "%s",\n' "$(json_escape "$target_sdk_repo")"
        printf '    "ref": "%s"\n' "$(json_escape "$target_sdk_ref")"
        printf '  },\n'
        printf '  "toolchain": {\n'
        printf '    "source": "%s"\n' "$(json_escape "$target_toolchain_source")"
        printf '  },\n'
        printf '  "ui": {\n'
        printf '    "lvgl_provider": "%s",\n' "$(json_escape "$target_ui_lvgl_provider")"
        printf '    "lvgl_note": "%s"\n' "$(json_escape "$target_ui_lvgl_note")"
        printf '  },\n'
        printf '  "headers": [\n'

        first=1
        find "$package_root/include" -type f -name '*.h' -print | sort | while IFS= read -r header; do
            relative=${header#"$package_root"/}
            if [ "$first" -eq 1 ]; then
                first=0
            else
                printf ',\n'
            fi
            printf '    "%s"' "$(json_escape "$relative")"
        done

        printf '\n  ]\n'
        printf '}\n'
    } > "$manifest"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --repo-root)
            [ "$#" -ge 2 ] || die "缺少 --repo-root 参数值"
            REPO_ROOT=$2
            shift 2
            ;;
        --target)
            [ "$#" -ge 2 ] || die "缺少 --target 参数值"
            TARGET=$2
            shift 2
            ;;
        --target-file)
            [ "$#" -ge 2 ] || die "缺少 --target-file 参数值"
            TARGET_FILE=$2
            shift 2
            ;;
        --sdk-dir)
            [ "$#" -ge 2 ] || die "缺少 --sdk-dir 参数值"
            SDK_DIR=$2
            shift 2
            ;;
        --output-dir)
            [ "$#" -ge 2 ] || die "缺少 --output-dir 参数值"
            OUTPUT_DIR=$2
            shift 2
            ;;
        --clean)
            CLEAN=1
            shift
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            die "未知参数：$1"
            ;;
    esac
done

[ -n "$TARGET" ] || die "缺少 --target 参数"
[ -n "$SDK_DIR" ] || die "缺少 --sdk-dir 参数"

REPO_ROOT=$(CDPATH= cd -- "$REPO_ROOT" && pwd)
SDK_DIR=$(sdk_resolve_path "$SDK_DIR" "$REPO_ROOT")
OUTPUT_DIR=$(sdk_resolve_path "$OUTPUT_DIR" "$REPO_ROOT")

if [ -z "$TARGET_FILE" ]; then
    TARGET_FILE=$REPO_ROOT/targets/$TARGET.yaml
else
    TARGET_FILE=$(sdk_resolve_path "$TARGET_FILE" "$REPO_ROOT")
fi

[ -f "$TARGET_FILE" ] || die "缺少 target 描述文件：$TARGET_FILE"
[ -d "$SDK_DIR" ] || die "缺少 SDK 目录：$SDK_DIR"

PACKAGE_ROOT=$OUTPUT_DIR/$TARGET
BUILD_ROOT=$REPO_ROOT/build/sdk-ep/$TARGET
OBJECT_ROOT=$BUILD_ROOT/obj
ARCHIVE=$PACKAGE_ROOT/lib/libep_app_core.a
LUBAN_ROOT=$(resolve_luban_root "$SDK_DIR")
CC=$(find_tool "$LUBAN_ROOT" riscv64-unknown-elf-gcc)
AR=$(find_tool "$LUBAN_ROOT" riscv64-unknown-elf-ar)
RTCONFIG=$LUBAN_ROOT/rtconfig.h
TARGET_CHIP=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "chip")")

ensure_luban_configured "$LUBAN_ROOT" "$TARGET_FILE" "$RTCONFIG"

if [ "$CLEAN" -eq 1 ]; then
    rm -rf "$PACKAGE_ROOT" "$BUILD_ROOT"
fi

mkdir -p "$PACKAGE_ROOT/lib" "$PACKAGE_ROOT/include" "$OBJECT_ROOT"
copy_headers "$REPO_ROOT" "$PACKAGE_ROOT"
copy_resources "$REPO_ROOT" "$PACKAGE_ROOT"

include_flags="
-I$REPO_ROOT/core/include
-I$REPO_ROOT/app/include
-I$REPO_ROOT/app/selftest
-I$REPO_ROOT/app/services
-I$REPO_ROOT/app/ui
-I$REPO_ROOT/app/ui/pages
-I$REPO_ROOT/components/config/include
-I$REPO_ROOT/components/device/include
-I$REPO_ROOT/components/event/include
-I$REPO_ROOT/components/file/include
-I$REPO_ROOT/components/log/include
-I$REPO_ROOT/components/recipe_parser/include
-I$REPO_ROOT/components/timer/include
-I$REPO_ROOT/osal/include
-I$REPO_ROOT/hal/include
-I$REPO_ROOT/platforms/include
-I$REPO_ROOT/third_party/external/EasyLogger/easylogger/inc
-I$REPO_ROOT/third_party/external/cjson
-I$REPO_ROOT/third_party/external/sqlite
-I$LUBAN_ROOT
-I$LUBAN_ROOT/kernel/rt-thread/include
-I$LUBAN_ROOT/kernel/rt-thread/components/legacy
-I$LUBAN_ROOT/kernel/rt-thread/components/drivers/include
-I$LUBAN_ROOT/kernel/rt-thread/components/finsh
"
include_flags="$include_flags
$(append_luban_lvgl_include_flags "$LUBAN_ROOT")"
include_flags="$include_flags
$(append_luban_lvgl_custom_include_flags "$LUBAN_ROOT" "$RTCONFIG")"

common_flags="
-std=c11
-include
$RTCONFIG
"

rtconfig_cflags=$(extract_rtconfig_cflags "$LUBAN_ROOT" "$TARGET_CHIP")
[ -n "$rtconfig_cflags" ] || rtconfig_cflags="-Os -ffunction-sections -fdata-sections -Wall -Wextra"
sqlite_flags="-DSQLITE_OS_OTHER=1 -DSQLITE_THREADSAFE=0 -DSQLITE_OMIT_LOAD_EXTENSION -DSQLITE_OMIT_WAL"

sources="
core/src/ep_framework.c
app/app_core.c
app/main.c
app/selftest/app_selftest.c
app/ui/app_ui.c
app/ui/page_manager.c
app/ui/pages/home_page.c
app/ui/pages/running_page.c
app/ui/pages/settings_page.c
app/services/beep_service.c
app/services/lcd_sleep_service.c
app/services/power_board_service.c
app/services/rtc_service.c
components/config/src/ep_config.c
components/device/src/ep_device.c
components/file/src/ep_file.c
components/event/src/ep_event.c
components/timer/src/ep_timer.c
components/log/src/ep_log.c
components/recipe_parser/src/ep_simple_recipe.c
platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c
platforms/rtos/demo_family/startup/app_start.c
platforms/rtos/demo_family/paths/ep_rtos_platform_paths.c
platforms/rtos/demo_family/storage/ep_rtos_sqlite_vfs.c
platforms/rtos/demo_family/storage/ep_rtos_sqlite3.c
platforms/rtos/demo_family/hal_port/ep_rtos_hal_gpio_rtthread.c
platforms/rtos/demo_family/hal_port/ep_rtos_hal_i2c_rtthread.c
platforms/rtos/demo_family/hal_port/ep_rtos_hal_rtthread.c
platforms/rtos/demo_family/hal_port/ep_rtos_hal_pwm_rtthread.c
platforms/rtos/demo_family/hal_port/ep_rtos_hal_rtc_pcf8563.c
platforms/rtos/demo_family/component_port/ep_rtos_default_devices.c
platforms/rtos/demo_family/component_port/ep_rtos_component_stub.c
third_party/external/EasyLogger/easylogger/src/elog.c
third_party/external/EasyLogger/easylogger/src/elog_utils.c
third_party/external/EasyLogger/easylogger/port/elog_port.c
third_party/external/cjson/cJSON.c
"

objects=""
for rel in $sources; do
    src=$REPO_ROOT/$rel
    [ -f "$src" ] || die "缺少 EP 源文件：$src"
    obj=$OBJECT_ROOT/${rel##*/}.o
    extra_flags=
    case "$rel" in
        platforms/rtos/demo_family/storage/ep_rtos_sqlite3.c)
            extra_flags=$sqlite_flags
            ;;
    esac
    compile_source "$CC" "$src" "$obj" $common_flags $rtconfig_cflags $include_flags $extra_flags
    objects="$objects $obj"
done

rm -f "$ARCHIVE"
# shellcheck disable=SC2086
"$AR" rcs "$ARCHIVE" $objects

write_manifest "$PACKAGE_ROOT/manifest.json" "$PACKAGE_ROOT"

file_count=$(find "$PACKAGE_ROOT" -type f | wc -l | tr -d ' ')

printf 'SDK 目标 EP 静态库导出包已生成：%s\n' "$PACKAGE_ROOT"
printf '文件数量：%s\n' "$file_count"
printf '清单文件：%s\n' "$PACKAGE_ROOT/manifest.json"
