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

require_section_value() {
    target_file=$1
    section=$2
    key=$3
    value=$(td_trim "$(td_read_section_value "$target_file" "$section" "$key")")
    td_require_value "$value" "target 描述缺少 ${section}.${key}：$target_file"
    printf '%s\n' "$value"
}

require_pinned_sdk_ref() {
    target_file=$1
    sdk_ref=$2

    case "$sdk_ref" in
        main|master|develop|HEAD)
            td_die "target 描述不能使用浮动 sdk.ref：$target_file"
            ;;
    esac
}

validate_submodule_head() {
    target_file=$1
    sdk_name=$2
    sdk_ref=$3
    submodule_dir=$REPO_ROOT/third_party/sdk/$sdk_name

    [ -d "$submodule_dir" ] || return 0

    if ! submodule_head=$(git -C "$submodule_dir" rev-parse HEAD 2>/dev/null); then
        td_die "SDK 子模块无法读取 HEAD：$submodule_dir"
    fi

    if [ "$submodule_head" != "$sdk_ref" ]; then
        td_die "SDK 子模块 HEAD 与 target sdk.ref 不一致：$target_file"
    fi
}

[ -d "$TARGET_DIR" ] || td_die "缺少 targets 目录：$TARGET_DIR"

count=0
for target_file in "$TARGET_DIR"/*.yaml; do
    [ -e "$target_file" ] || td_die "没有 target 描述文件：$TARGET_DIR/*.yaml"
    count=$((count + 1))

    target_name=$(basename "$target_file" .yaml)
    td_validate_declared_target "$target_file" "$target_name"

    for old_key in os vendor sdk_family chip board kernel; do
        if grep -q "^${old_key}:" "$target_file"; then
            td_die "target 描述禁止使用旧顶层字段 ${old_key}：$target_file"
        fi
    done

    if grep -q '\.sdk\|/Users/\|/opt/' "$target_file"; then
        td_die "target 描述不能写本地 SDK 路径：$target_file"
    fi

    platform_family=$(require_section_value "$target_file" "platform" "family")
    require_section_value "$target_file" "platform" "vendor" >/dev/null
    require_section_value "$target_file" "platform" "sdk_family" >/dev/null
    require_section_value "$target_file" "platform" "chip" >/dev/null
    require_section_value "$target_file" "platform" "board" >/dev/null
    require_section_value "$target_file" "platform" "kernel" >/dev/null
    require_section_value "$target_file" "toolchain" "source" >/dev/null
    require_section_value "$target_file" "output" "ep_package" >/dev/null

    if [ "$platform_family" = "rtos" ]; then
        sdk_name=$(require_section_value "$target_file" "sdk" "name")
        require_section_value "$target_file" "sdk" "repo" >/dev/null
        sdk_ref=$(require_section_value "$target_file" "sdk" "ref")
        require_pinned_sdk_ref "$target_file" "$sdk_ref"
        validate_submodule_head "$target_file" "$sdk_name" "$sdk_ref"
        require_section_value "$target_file" "output" "firmware" >/dev/null
    fi
done

printf 'target 校验通过：%s\n' "$count"
