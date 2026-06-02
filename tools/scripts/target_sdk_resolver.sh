#!/bin/sh

sdk_resolver_die() {
    printf '%s\n' "$1" >&2
    exit 1
}

sdk_resolve_path() {
    path=$1
    base=$2

    case "$path" in
        /*) printf '%s\n' "$path" ;;
        *)
            if [ -d "$base/$path" ]; then
                CDPATH= cd -- "$base/$path" && pwd
            else
                printf '%s\n' "$base/$path"
            fi
            ;;
    esac
}

sdk_default_root() {
    repo_root=$1
    printf '%s\n' "$(dirname -- "$repo_root")/sdks"
}

sdk_resolve_external_root() {
    repo_root=$1
    sdk_root=$2

    if [ -z "$sdk_root" ]; then
        sdk_root=$(sdk_default_root "$repo_root")
    fi

    sdk_root=$(sdk_resolve_path "$sdk_root" "$repo_root")
    case "$sdk_root" in
        "$repo_root"|"$repo_root"/*)
            sdk_resolver_die "SDK 本地缓存不能放在主工程目录内：$sdk_root"
            ;;
    esac

    printf '%s\n' "$sdk_root"
}

sdk_submodule_dir() {
    repo_root=$1
    sdk_name=$2

    printf '%s\n' "$repo_root/third_party/sdk/$sdk_name"
}

sdk_has_checked_out_submodule() {
    repo_root=$1
    sdk_name=$2
    submodule_dir=$(sdk_submodule_dir "$repo_root" "$sdk_name")

    [ -d "$submodule_dir" ] && [ "$(find "$submodule_dir" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')" != "0" ]
}

sdk_resolve_dir() {
    repo_root=$1
    sdk_name=$2
    sdk_root=$3

    if sdk_has_checked_out_submodule "$repo_root" "$sdk_name"; then
        sdk_submodule_dir "$repo_root" "$sdk_name"
        return 0
    fi

    sdk_root=$(sdk_resolve_external_root "$repo_root" "$sdk_root")
    printf '%s/%s\n' "$sdk_root" "$sdk_name"
}

sdk_resolve_source() {
    repo_root=$1
    sdk_name=$2

    if sdk_has_checked_out_submodule "$repo_root" "$sdk_name"; then
        printf '%s\n' "submodule"
    else
        printf '%s\n' "external"
    fi
}
