#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/target_descriptor.sh"
. "$SCRIPT_DIR/target_sdk_resolver.sh"

REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=
SDK_ROOT=${EP_SDK_ROOT:-}

print_help() {
    cat <<EOF
用法:
  tools/scripts/check_target_env.sh --target <名称> [参数]

参数:
  --repo-root <路径>  仓库根目录，默认自动使用当前脚本所在仓库
  --target <名称>     target 名称，对应 targets/<target>.yaml
  --sdk-root <路径>   SDK 外部缓存根目录，默认 ../sdks，也可用 EP_SDK_ROOT 指定
                     如果 third_party/sdk/<sdk.name> 已检出，会优先复用子模块
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

platform_family=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "family")")

if [ "$platform_family" != "rtos" ]; then
    printf 'target %s 平台类型为 %s，无需 RTOS SDK 环境检查。\n' "$TARGET" "$platform_family"
    exit 0
fi

sdk_name=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "name")")
td_require_value "$sdk_name" "target 描述缺少 sdk.name：$TARGET_FILE"

"$REPO_ROOT/tools/scripts/prepare_target_sdk.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --sdk-root "$SDK_ROOT"

SDK_DIR=$(sdk_resolve_dir "$REPO_ROOT" "$sdk_name" "$SDK_ROOT")

SDK_PREPARE_SCRIPT=$SDK_DIR/scripts/prepare.sh
[ -x "$SDK_PREPARE_SCRIPT" ] || die "SDK 缺少准备入口：$SDK_PREPARE_SCRIPT"
(
    cd "$SDK_DIR"
    "$SDK_PREPARE_SCRIPT" --target "$TARGET"
)

CHECK_ENV_SCRIPT=$SDK_DIR/scripts/check_env.sh
[ -x "$CHECK_ENV_SCRIPT" ] || die "SDK 缺少环境检测入口：$CHECK_ENV_SCRIPT"

(
    cd "$SDK_DIR"
    "$CHECK_ENV_SCRIPT" --target "$TARGET" --sdk-root "$SDK_DIR"
)
