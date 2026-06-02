#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/target_descriptor.sh"

REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)

print_help() {
    cat <<EOF
用法:
  tools/scripts/validate_targets.sh [参数]

参数:
  --repo-root <路径>  仓库根目录，默认自动使用当前脚本所在仓库
  -h, --help         显示帮助
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --repo-root)
            [ "$#" -ge 2 ] || td_die "缺少 --repo-root 参数值"
            REPO_ROOT=$2
            shift 2
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            td_die "未知参数：$1"
            ;;
    esac
done

REPO_ROOT=$(CDPATH= cd -- "$REPO_ROOT" && pwd)
TARGET_DIR=$REPO_ROOT/targets

[ -d "$TARGET_DIR" ] || td_die "缺少 targets 目录：$TARGET_DIR"

count=0
for target_file in "$TARGET_DIR"/*.yaml; do
    [ -e "$target_file" ] || td_die "没有 target 描述文件：$TARGET_DIR/*.yaml"
    count=$((count + 1))

    target_name=$(basename "$target_file" .yaml)
    td_validate_declared_target "$target_file" "$target_name"
    td_read_section_value "$target_file" "platform" "family" >/dev/null
done

printf 'target 校验通过：%s\n' "$count"
