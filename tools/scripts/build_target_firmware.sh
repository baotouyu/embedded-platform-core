#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/target_descriptor.sh"
. "$SCRIPT_DIR/target_sdk_resolver.sh"

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
  --sdk-root <路径>   SDK 外部缓存根目录，默认 ../sdks，也可用 EP_SDK_ROOT 指定
                     如果 third_party/sdk/<sdk.name> 已检出，会优先复用子模块
  --clean            导出和构建前删除已有输出目录
  -h, --help         显示帮助
EOF
}

die() {
    printf '%s\n' "$1" >&2
    exit 1
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

td_validate_declared_target "$TARGET_FILE" "$TARGET"

sdk_name=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "name")")
toolchain_source=$(td_trim "$(td_read_section_value "$TARGET_FILE" "toolchain" "source")")
ep_package=$(td_trim "$(td_read_section_value "$TARGET_FILE" "output" "ep_package")")
firmware_output=$(td_trim "$(td_read_section_value "$TARGET_FILE" "output" "firmware")")

td_require_value "$sdk_name" "target 描述缺少 sdk.name：$TARGET_FILE"
td_require_value "$toolchain_source" "target 描述缺少 toolchain.source：$TARGET_FILE"
td_require_value "$ep_package" "target 描述缺少 output.ep_package：$TARGET_FILE"
td_require_value "$firmware_output" "target 描述缺少 output.firmware：$TARGET_FILE"

SDK_DIR=$(sdk_resolve_dir "$REPO_ROOT" "$sdk_name" "$SDK_ROOT")
EP_PACKAGE_DIR=$(sdk_resolve_path "$ep_package" "$REPO_ROOT")
FIRMWARE_DIR=$(sdk_resolve_path "$firmware_output" "$REPO_ROOT")

check_result=0
"$REPO_ROOT/tools/scripts/check_target_env.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --sdk-root "$SDK_ROOT" || check_result=$?
if [ "$check_result" -ne 0 ]; then
    printf '\n环境检查失败（exit=%s）。请先运行 install-env 安装依赖。\n' "$check_result" >&2
    printf '  ./build.sh install-env %s\n' "$TARGET" >&2
    exit "$check_result"
fi

if [ "$toolchain_source" = "sdk" ]; then
    ep_output_parent=${EP_PACKAGE_DIR%/*}
    SDK_EXPORT_SCRIPT=$REPO_ROOT/tools/scripts/export_sdk_ep_package.sh
    [ -x "$SDK_EXPORT_SCRIPT" ] || die "主工程缺少 SDK 目标导出入口：$SDK_EXPORT_SCRIPT"
    if [ "$CLEAN" -eq 1 ]; then
        "$SDK_EXPORT_SCRIPT" --repo-root "$REPO_ROOT" --target "$TARGET" --target-file "$TARGET_FILE" --sdk-dir "$SDK_DIR" --output-dir "$ep_output_parent" --clean
    else
        "$SDK_EXPORT_SCRIPT" --repo-root "$REPO_ROOT" --target "$TARGET" --target-file "$TARGET_FILE" --sdk-dir "$SDK_DIR" --output-dir "$ep_output_parent"
    fi
else
    if [ "$CLEAN" -eq 1 ]; then
        "$REPO_ROOT/tools/scripts/export_target.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --clean
    else
        "$REPO_ROOT/tools/scripts/export_target.sh" --repo-root "$REPO_ROOT" --target "$TARGET"
    fi
fi

"$REPO_ROOT/tools/scripts/validate_ep_package.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --ep-package "$EP_PACKAGE_DIR"

SDK_BUILD_SCRIPT=$SDK_DIR/scripts/build_firmware.sh
[ -x "$SDK_BUILD_SCRIPT" ] || die "SDK 缺少固件构建入口：$SDK_BUILD_SCRIPT"

if [ "$CLEAN" -eq 1 ]; then
    (
        cd "$SDK_DIR"
        "$SDK_BUILD_SCRIPT" --target "$TARGET" --ep-package "$EP_PACKAGE_DIR" --out "$FIRMWARE_DIR" --clean
    )
else
    (
        cd "$SDK_DIR"
        "$SDK_BUILD_SCRIPT" --target "$TARGET" --ep-package "$EP_PACKAGE_DIR" --out "$FIRMWARE_DIR"
    )
fi

printf '固件已生成：%s\n' "$FIRMWARE_DIR"
