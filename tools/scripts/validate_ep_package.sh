#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/target_descriptor.sh"

REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=
EP_PACKAGE=

print_help() {
    cat <<EOF
用法:
  tools/scripts/validate_ep_package.sh --target <名称> [参数]

参数:
  --repo-root <路径>   仓库根目录，默认自动使用当前脚本所在仓库
  --target <名称>      target 名称，对应 targets/<target>.yaml
  --ep-package <路径>  EP 导出包目录，默认读取 target 描述的 output.ep_package
  -h, --help           显示帮助
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

manifest_read() {
    section=$1
    key=$2

    if [ "$section" = "." ]; then
        awk -v key="$key" '
            $0 ~ "^[[:space:]]*\"" key "\"[[:space:]]*:" {
                sub("^[[:space:]]*\"" key "\"[[:space:]]*:[[:space:]]*\"", "")
                sub("\"[[:space:]]*,?[[:space:]]*$", "")
                print
                exit
            }
        ' "$MANIFEST"
        return
    fi

    awk -v section="$section" -v key="$key" '
        $0 ~ "^[[:space:]]*\"" section "\"[[:space:]]*:" { in_section = 1; next }
        in_section && /^[[:space:]]*}/ { in_section = 0 }
        in_section && $0 ~ "^[[:space:]]*\"" key "\"[[:space:]]*:" {
            sub("^[[:space:]]*\"" key "\"[[:space:]]*:[[:space:]]*\"", "")
            sub("\"[[:space:]]*,?[[:space:]]*$", "")
            print
            exit
        }
    ' "$MANIFEST"
}

target_value() {
    section=$1
    key=$2
    td_trim "$(td_read_section_value "$TARGET_FILE" "$section" "$key")"
}

require_match() {
    label=$1
    manifest_value=$2
    expected_value=$3

    [ -n "$manifest_value" ] || die "EP 导出包校验失败：manifest 缺少 ${label}：${MANIFEST}"
    [ "$manifest_value" = "$expected_value" ] || die "EP 导出包校验失败：manifest ${label} 为 ${manifest_value}，target 描述为 ${expected_value}"
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
        --ep-package)
            [ "$#" -ge 2 ] || die "缺少 --ep-package 参数值"
            EP_PACKAGE=$2
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

if [ -z "$EP_PACKAGE" ]; then
    EP_PACKAGE=$(td_trim "$(td_read_section_value "$TARGET_FILE" "output" "ep_package")")
    td_require_value "$EP_PACKAGE" "target 描述缺少 output.ep_package：$TARGET_FILE"
fi

EP_PACKAGE=$(resolve_path "$EP_PACKAGE" "$REPO_ROOT")
MANIFEST=$EP_PACKAGE/manifest.json

[ -d "$EP_PACKAGE" ] || die "缺少 EP 导出包目录：$EP_PACKAGE"
[ -f "$MANIFEST" ] || die "缺少 EP 导出包 manifest：$MANIFEST"

manifest_target=$(td_trim "$(manifest_read "." "target")")
require_match "target" "$manifest_target" "$TARGET"

for key in family vendor sdk_family chip board kernel; do
    require_match "platform.$key" \
        "$(td_trim "$(manifest_read "platform" "$key")")" \
        "$(target_value "platform" "$key")"
done

for key in name repo ref; do
    require_match "sdk.$key" \
        "$(td_trim "$(manifest_read "sdk" "$key")")" \
        "$(target_value "sdk" "$key")"
done

require_match "toolchain.source" \
    "$(td_trim "$(manifest_read "toolchain" "source")")" \
    "$(target_value "toolchain" "source")"

printf 'EP 导出包校验通过：%s\n' "$EP_PACKAGE"
