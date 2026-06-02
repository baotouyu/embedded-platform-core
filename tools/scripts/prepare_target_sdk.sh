#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/target_descriptor.sh"

REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=
SDK_ROOT=${EP_SDK_ROOT:-}

print_help() {
    cat <<EOF
用法:
  tools/scripts/prepare_target_sdk.sh --target <名称> [参数]

参数:
  --repo-root <路径>  仓库根目录，默认自动使用当前脚本所在仓库
  --target <名称>     target 名称，对应 targets/<target>.yaml
  --sdk-root <路径>   SDK 本地缓存根目录，默认 ../sdks，也可用 EP_SDK_ROOT 指定
  -h, --help         显示帮助
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

sdk_repo=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "repo")")
sdk_ref=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "ref")")
sdk_name=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "name")")

td_require_value "$sdk_name" "target 描述缺少 sdk.name：$TARGET_FILE"
td_require_value "$sdk_repo" "target 描述缺少 sdk.repo：$TARGET_FILE"
td_require_value "$sdk_ref" "target 描述缺少 sdk.ref：$TARGET_FILE"

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

if [ -d "$SDK_DIR" ]; then
    printf 'SDK 已存在：%s\n' "$SDK_DIR"
    exit 0
fi

mkdir -p "$(dirname -- "$SDK_DIR")"
git clone "$sdk_repo" "$SDK_DIR"

(
    cd "$SDK_DIR"
    git checkout "$sdk_ref"
)

printf 'SDK 已准备：%s\n' "$SDK_DIR"
