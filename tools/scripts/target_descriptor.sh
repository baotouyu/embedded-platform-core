#!/bin/sh

td_die() {
    printf '%s\n' "$1" >&2
    exit 1
}

td_trim() {
    printf '%s' "$1" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
}

td_read_top_level_value() {
    file=$1
    key=$2
    sed -n "s/^${key}:[[:space:]]*//p" "$file" | head -n 1
}

td_read_section_value() {
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

td_require_value() {
    value=$1
    message=$2
    [ -n "$(td_trim "$value")" ] || td_die "$message"
}

td_validate_declared_target() {
    target_file=$1
    target=$2
    declared_target=$(td_trim "$(td_read_top_level_value "$target_file" "target")")
    [ "$declared_target" = "$target" ] || td_die "target 描述不匹配：文件内 target 为 ${declared_target}，命令参数为 ${target}"
}
