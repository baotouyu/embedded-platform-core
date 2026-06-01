#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=
SDK_ROOT=${EP_SDK_ROOT:-}
CLEAN=0

print_help() {
    cat <<EOF
用法:
  tools/scripts/build_target_firmware.sh --target <名称> [参数]

参数:
  --repo-root <路径>  仓库根目录，默认自动使用当前脚本所在仓库
  --target <名称>     target 名称，对应 targets/<target>.yaml
  --sdk-root <路径>   SDK 本地缓存根目录，默认 ../sdks，也可用 EP_SDK_ROOT 指定
  --clean            导出和构建前删除已有输出目录
  -h, --help         显示帮助
EOF
}

die() {
    printf '%s\n' "$1" >&2
    exit 1
}

trim() {
    printf '%s' "$1" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
}

read_top_level_value() {
    file=$1
    key=$2
    sed -n "s/^${key}:[[:space:]]*//p" "$file" | head -n 1
}

read_section_value() {
    file=$1
    section=$2
    key=$3
    awk -v section="$section" -v key="$key" '
        $0 ~ "^" section ":" { in_section = 1; next }
        /^[^[:space:]].*:/ { in_section = 0 }
        in_section && $0 ~ "^[[:space:]]+" key ":" {
            sub("^[[:space:]]+" key ":[[:space:]]*", "")
            print
            exit
        }
    ' "$file"
}

resolve_path() {
    path=$1
    base=$2

    case "$path" in
        /*) printf '%s\n' "$path" ;;
        *) printf '%s\n' "$base/$path" ;;
    esac
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
        --sdk-root)
            [ "$#" -ge 2 ] || die "缺少 --sdk-root 参数值"
            SDK_ROOT=$2
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

REPO_ROOT=$(CDPATH= cd -- "$REPO_ROOT" && pwd)
TARGET_FILE=$REPO_ROOT/targets/$TARGET.yaml

[ -f "$TARGET_FILE" ] || die "缺少 target 描述文件：$TARGET_FILE"

declared_target=$(trim "$(read_top_level_value "$TARGET_FILE" "target")")
[ "$declared_target" = "$TARGET" ] || die "target 描述不匹配：文件内 target 为 ${declared_target}，命令参数为 ${TARGET}"

sdk_name=$(trim "$(read_section_value "$TARGET_FILE" "sdk" "name")")
ep_package=$(trim "$(read_section_value "$TARGET_FILE" "output" "ep_package")")
firmware_output=$(trim "$(read_section_value "$TARGET_FILE" "output" "firmware")")

[ -n "$sdk_name" ] || die "target 描述缺少 sdk.name：$TARGET_FILE"
[ -n "$ep_package" ] || die "target 描述缺少 output.ep_package：$TARGET_FILE"
[ -n "$firmware_output" ] || die "target 描述缺少 output.firmware：$TARGET_FILE"

if [ -z "$SDK_ROOT" ]; then
    SDK_ROOT=$(dirname -- "$REPO_ROOT")/sdks
fi

SDK_ROOT=$(resolve_path "$SDK_ROOT" "$REPO_ROOT")
case "$SDK_ROOT" in
    "$REPO_ROOT"|"$REPO_ROOT"/*)
        die "SDK 本地缓存不能放在主工程目录内：$SDK_ROOT"
        ;;
esac

SDK_DIR=$SDK_ROOT/$sdk_name
EP_PACKAGE_DIR=$(resolve_path "$ep_package" "$REPO_ROOT")
FIRMWARE_DIR=$(resolve_path "$firmware_output" "$REPO_ROOT")

"$REPO_ROOT/tools/scripts/prepare_target_sdk.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --sdk-root "$SDK_ROOT"

if [ "$CLEAN" -eq 1 ]; then
    "$REPO_ROOT/tools/scripts/export_target.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --clean
else
    "$REPO_ROOT/tools/scripts/export_target.sh" --repo-root "$REPO_ROOT" --target "$TARGET"
fi

SDK_BUILD_SCRIPT=$SDK_DIR/scripts/build_firmware.sh
[ -x "$SDK_BUILD_SCRIPT" ] || die "SDK 缺少固件构建入口：$SDK_BUILD_SCRIPT"

if [ "$CLEAN" -eq 1 ]; then
    "$SDK_BUILD_SCRIPT" --target "$TARGET" --ep-package "$EP_PACKAGE_DIR" --out "$FIRMWARE_DIR" --clean
else
    "$SDK_BUILD_SCRIPT" --target "$TARGET" --ep-package "$EP_PACKAGE_DIR" --out "$FIRMWARE_DIR"
fi

printf '固件已生成：%s\n' "$FIRMWARE_DIR"
