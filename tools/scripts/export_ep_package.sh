#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/target_descriptor.sh"

REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=host_rtos_demo
TARGET_FILE=
OUTPUT_DIR=out/ep
CLEAN=0

print_help() {
    cat <<EOF
用法:
  tools/scripts/export_ep_package.sh [参数]

参数:
  --repo-root <路径>   仓库根目录，默认自动使用当前脚本所在仓库
  --target <名称>      导出目标名称，默认 host_rtos_demo
  --target-file <路径> target 描述文件，存在时写入 platform/sdk/toolchain 元数据
  --output-dir <路径>  输出父目录，脚本会生成 <路径>/<target>
  --clean             导出前删除已有 target 输出目录
  -h, --help          显示帮助

默认输出:
  out/ep/<target>
EOF
}

die() {
    printf '%s\n' "$1" >&2
    exit 1
}

resolve_path() {
    path=$1
    base=$2

    case "$path" in
        /*) printf '%s\n' "$path" ;;
        *) printf '%s\n' "$base/$path" ;;
    esac
}

json_escape() {
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
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

REPO_ROOT=$(CDPATH= cd -- "$REPO_ROOT" && pwd)
if [ -n "$TARGET_FILE" ]; then
    TARGET_FILE=$(resolve_path "$TARGET_FILE" "$REPO_ROOT")
    [ -f "$TARGET_FILE" ] || die "缺少 target 描述文件：$TARGET_FILE"
fi
OUTPUT_DIR=$(resolve_path "$OUTPUT_DIR" "$REPO_ROOT")
PACKAGE_ROOT=$OUTPUT_DIR/$TARGET
ARCHIVE=$REPO_ROOT/build/libep_app_core_export.a

[ -f "$ARCHIVE" ] || die "缺少静态库产物：${ARCHIVE}，请先执行 ./build.sh build"

HEADER_DIRS="
core/include
app/include
app/selftest
app/services
app/ui
components/log/include
components/config/include
components/event/include
components/timer/include
components/file/include
components/device/include
components/ui/include
osal/include
hal/include
platforms/include
"

missing=""
for dir in $HEADER_DIRS; do
    [ -d "$REPO_ROOT/$dir" ] || missing="${missing}
- $REPO_ROOT/$dir"
done

[ -z "$missing" ] || die "缺少头文件目录：$missing"

if [ "$CLEAN" -eq 1 ]; then
    rm -rf "$PACKAGE_ROOT"
fi

mkdir -p "$PACKAGE_ROOT/lib" "$PACKAGE_ROOT/include"
cp -p "$ARCHIVE" "$PACKAGE_ROOT/lib/libep_app_core.a"
copy_resources "$REPO_ROOT" "$PACKAGE_ROOT"

for dir in $HEADER_DIRS; do
    find "$REPO_ROOT/$dir" -type f -name '*.h' -print | while IFS= read -r header; do
        cp -p "$header" "$PACKAGE_ROOT/include/$(basename -- "$header")"
    done
done

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

if [ -n "$TARGET_FILE" ]; then
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
fi

MANIFEST=$PACKAGE_ROOT/manifest.json
{
    printf '{\n'
    printf '  "package": "ep_app_core",\n'
    printf '  "target": "%s",\n' "$(json_escape "$TARGET")"
    printf '  "format": "static-library",\n'
    printf '  "library": "lib/libep_app_core.a",\n'
    if [ -n "$TARGET_FILE" ]; then
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
    fi
    printf '  "headers": [\n'

    first=1
    find "$PACKAGE_ROOT/include" -type f -name '*.h' -print | sort | while IFS= read -r header; do
        relative=${header#"$PACKAGE_ROOT"/}
        if [ "$first" -eq 1 ]; then
            first=0
        else
            printf ',\n'
        fi
        printf '    "%s"' "$(json_escape "$relative")"
    done

    printf '\n  ]\n'
    printf '}\n'
} > "$MANIFEST"

file_count=$(find "$PACKAGE_ROOT" -type f | wc -l | tr -d ' ')

printf 'EP 静态库导出包已生成：%s\n' "$PACKAGE_ROOT"
printf '文件数量：%s\n' "$file_count"
printf '清单文件：%s\n' "$MANIFEST"
