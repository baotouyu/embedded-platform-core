#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/target_descriptor.sh"

REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
VERBOSE=0

print_help() {
    cat <<EOF
用法:
  tools/scripts/select_target.sh [参数]

参数:
  --repo-root <路径>  仓库根目录，默认自动使用当前脚本所在仓库
  --verbose          显示自动选中的层级
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
        --verbose)
            VERBOSE=1
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
TARGET_DIR=$REPO_ROOT/targets
[ -d "$TARGET_DIR" ] || die "缺少 targets 目录：$TARGET_DIR"

WORK_DIR=$(mktemp -d "${TMPDIR:-/tmp}/ep-target-select.XXXXXX")
trap 'rm -rf "$WORK_DIR"' EXIT HUP INT TERM

TARGETS_FILE=$WORK_DIR/targets.tsv
FILTERED_FILE=$WORK_DIR/filtered.tsv

for target_file in "$TARGET_DIR"/*.yaml; do
    [ -e "$target_file" ] || die "没有 target 描述文件：$TARGET_DIR/*.yaml"
    target_name=$(basename "$target_file" .yaml)
    td_validate_declared_target "$target_file" "$target_name"
    family=$(td_trim "$(td_read_section_value "$target_file" "platform" "family")")
    vendor=$(td_trim "$(td_read_section_value "$target_file" "platform" "vendor")")
    sdk_family=$(td_trim "$(td_read_section_value "$target_file" "platform" "sdk_family")")
    chip=$(td_trim "$(td_read_section_value "$target_file" "platform" "chip")")
    board=$(td_trim "$(td_read_section_value "$target_file" "platform" "board")")
    kernel=$(td_trim "$(td_read_section_value "$target_file" "platform" "kernel")")

    td_require_value "$family" "target 描述缺少 platform.family：$target_file"
    td_require_value "$vendor" "target 描述缺少 platform.vendor：$target_file"
    td_require_value "$sdk_family" "target 描述缺少 platform.sdk_family：$target_file"
    td_require_value "$chip" "target 描述缺少 platform.chip：$target_file"
    td_require_value "$board" "target 描述缺少 platform.board：$target_file"
    td_require_value "$kernel" "target 描述缺少 platform.kernel：$target_file"

    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$target_name" "$family" "$vendor" "$sdk_family" "$chip" "$board" "$kernel" >> "$TARGETS_FILE"
done

cp "$TARGETS_FILE" "$FILTERED_FILE"

field_index() {
    case "$1" in
        family) printf '2\n' ;;
        vendor) printf '3\n' ;;
        sdk_family) printf '4\n' ;;
        chip) printf '5\n' ;;
        board) printf '6\n' ;;
        kernel) printf '7\n' ;;
        *) die "未知字段：$1" ;;
    esac
}

label_for() {
    case "$1" in
        family) printf '平台类型\n' ;;
        vendor) printf '厂商\n' ;;
        sdk_family) printf 'SDK\n' ;;
        chip) printf '芯片\n' ;;
        board) printf '板级方案\n' ;;
        kernel) printf '内核\n' ;;
        action) printf '动作\n' ;;
        *) die "未知标签：$1" ;;
    esac
}

list_values() {
    field=$1
    field_no=$(field_index "$field")
    awk -F '\t' -v field_no="$field_no" '{ print $field_no }' "$FILTERED_FILE" | sort -u
}

value_count() {
    list_values "$1" | awk 'NF { count += 1 } END { print count + 0 }'
}

first_value() {
    list_values "$1" | sed -n '1p'
}

choose_from_file() {
    title=$1
    values_file=$2
    count=$(awk 'NF { count += 1 } END { print count + 0 }' "$values_file")

    [ "$count" -gt 0 ] || die "没有可选${title}"

    if [ "$count" -eq 1 ]; then
        sed -n '1p' "$values_file"
        return 0
    fi

    printf '选择%s:\n' "$title" >&2
    nl -w1 -s ') ' "$values_file" >&2

    while :; do
        printf '> ' >&2
        if ! IFS= read -r choice; then
            die "读取选择失败"
        fi
        case "$choice" in
            ''|*[!0-9]*)
                printf '请输入 1-%s 的数字\n' "$count" >&2
                ;;
            *)
                if [ "$choice" -ge 1 ] && [ "$choice" -le "$count" ]; then
                    sed -n "${choice}p" "$values_file"
                    return 0
                fi
                printf '请输入 1-%s 的数字\n' "$count" >&2
                ;;
        esac
    done
}

apply_filter() {
    field=$1
    value=$2
    field_no=$(field_index "$field")
    next_file=$WORK_DIR/filtered.next.tsv
    awk -F '\t' -v OFS='\t' -v field_no="$field_no" -v value="$value" '$field_no == value { print }' \
        "$FILTERED_FILE" > "$next_file"
    mv "$next_file" "$FILTERED_FILE"
}

choose_filter() {
    field=$1
    count=$(value_count "$field")
    [ "$count" -gt 0 ] || die "没有匹配的 target"

    if [ "$count" -eq 1 ]; then
        value=$(first_value "$field")
    else
        values_file=$WORK_DIR/$field.values
        list_values "$field" > "$values_file"
        value=$(choose_from_file "$(label_for "$field")" "$values_file")
    fi

    apply_filter "$field" "$value"

    if [ "$VERBOSE" -eq 1 ]; then
        printf '已选%s：%s\n' "$(label_for "$field")" "$value" >&2
    fi
}

target_count() {
    awk 'NF { count += 1 } END { print count + 0 }' "$FILTERED_FILE"
}

choose_target() {
    count=$(target_count)
    [ "$count" -gt 0 ] || die "没有匹配的 target"

    if [ "$count" -eq 1 ]; then
        awk -F '\t' 'NR == 1 { print $1 }' "$FILTERED_FILE"
        return 0
    fi

    values_file=$WORK_DIR/target.values
    awk -F '\t' '{ print $1 }' "$FILTERED_FILE" | sort -u > "$values_file"
    choose_from_file "target" "$values_file"
}

choose_action() {
    actions_file=$WORK_DIR/actions.values
    cat > "$actions_file" <<EOF
show-target - 只显示选择结果
check-env - 检查 SDK 环境
install-env - 安装/修复 SDK 环境
prepare-sdk - 准备外部SDK
export-target - 导出EP静态库包
build-firmware - 准备SDK、检查环境并编译固件
full - 准备SDK、检查环境、导出EP包并编译固件
EOF
    action_label=$(choose_from_file "$(label_for action)" "$actions_file")
    printf '%s\n' "${action_label%% - *}"
}

for field in family vendor sdk_family chip board kernel; do
    choose_filter "$field"
done

target=$(choose_target)
action=$(choose_action)

printf 'target=%s\n' "$target"
printf 'action=%s\n' "$action"
