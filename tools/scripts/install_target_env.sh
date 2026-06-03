#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/target_descriptor.sh"
. "$SCRIPT_DIR/target_sdk_resolver.sh"

REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=
SDK_ROOT=${EP_SDK_ROOT:-}
YES=0
DRY_RUN=0

print_help() {
    cat <<EOF
用法:
  tools/scripts/install_target_env.sh --target <名称> [参数]

参数:
  --repo-root <路径>  仓库根目录，默认自动使用当前脚本所在仓库
  --target <名称>     target 名称，对应 targets/<target>.yaml
  --sdk-root <路径>   SDK 外部缓存根目录，默认 ../sdks，也可用 EP_SDK_ROOT 指定
                     如果 third_party/sdk/<sdk.name> 已检出，会优先复用子模块
  --yes              跳过交互确认
  --dry-run          只打印命令，不执行
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
        --yes)
            YES=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
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

platform_family=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "family")")

if [ "$platform_family" != "rtos" ]; then
    printf 'target %s 平台类型为 %s，无需 RTOS SDK 环境安装。\n' "$TARGET" "$platform_family"
    exit 0
fi

sdk_name=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "name")")
td_require_value "$sdk_name" "target 描述缺少 sdk.name：$TARGET_FILE"

SDK_DIR=$(sdk_resolve_dir "$REPO_ROOT" "$sdk_name" "$SDK_ROOT")

INSTALL_ENV_SCRIPT=$SDK_DIR/scripts/install_env.sh
[ -x "$INSTALL_ENV_SCRIPT" ] || die "SDK 缺少环境安装入口：$INSTALL_ENV_SCRIPT"

extra_args=""
[ "$YES" -eq 1 ] && extra_args="$extra_args --yes"
[ "$DRY_RUN" -eq 1 ] && extra_args="$extra_args --dry-run"

(
    cd "$SDK_DIR"
    # shellcheck disable=SC2086
    "$INSTALL_ENV_SCRIPT" --target "$TARGET" --sdk-root "$SDK_DIR" $extra_args
)
