#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=
CLEAN=0

print_help() {
    cat <<EOF
用法:
  tools/scripts/export_target.sh --target <名称> [参数]

参数:
  --repo-root <路径>  仓库根目录，默认自动使用当前脚本所在仓库
  --target <名称>     target 名称，对应 targets/<target>.yaml
  --clean            导出前删除已有输出目录
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

read_output_ep_package() {
    file=$1
    awk '
        /^output:/ { in_output = 1; next }
        /^[^[:space:]].*:/ { in_output = 0 }
        in_output && /^[[:space:]]+ep_package:/ {
            sub(/^[[:space:]]+ep_package:[[:space:]]*/, "")
            print
            exit
        }
    ' "$file"
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

ep_package=$(trim "$(read_output_ep_package "$TARGET_FILE")")
[ -n "$ep_package" ] || die "target 描述缺少 output.ep_package：$TARGET_FILE"

output_parent=${ep_package%/*}

if [ "$CLEAN" -eq 1 ]; then
    "$REPO_ROOT/tools/scripts/export_ep_package.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --output-dir "$output_parent" --clean
else
    "$REPO_ROOT/tools/scripts/export_ep_package.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --output-dir "$output_parent"
fi
