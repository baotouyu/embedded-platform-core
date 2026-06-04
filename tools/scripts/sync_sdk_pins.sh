#!/bin/sh
set -eu

# sync_sdk_pins.sh - 同步 SDK submodule 指针和 targets/*.yaml 中的 sdk.ref
#
# 只同步本地当前已检出的 HEAD，不执行 git fetch/pull/checkout/submodule update --remote。

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PY_YAML_HELPER="$SCRIPT_DIR/_sync_sdk_pins_update_yaml.py"

print_usage() {
    cat <<EOF
用法:
  sync-sdk-pins <sdk-name> --check
  sync-sdk-pins <sdk-name> --commit
  sync-sdk-pins <sdk-name> --repo-root <path> --check

参数:
  --check     只检查，不修改文件。发现不一致时返回非零。
  --commit    执行同步、提交 SDK 适配仓库、提交主工程。
  --repo-root 指定主工程根目录，默认自动定位。
EOF
}

# --- 解析参数 ---
SDK_NAME=""
ACTION=""
REPO_ROOT=""

while [ $# -gt 0 ]; do
    case "$1" in
        --check) ACTION="check"; shift ;;
        --commit) ACTION="commit"; shift ;;
        --repo-root)
            if [ $# -lt 2 ]; then
                printf '缺少 --repo-root 参数\n' >&2; exit 2
            fi
            REPO_ROOT="$2"; shift 2 ;;
        -*)
            printf '未知参数：%s\n' "$1" >&2
            print_usage >&2; exit 2 ;;
        *)
            if [ -z "$SDK_NAME" ]; then
                SDK_NAME="$1"; shift
            else
                printf '未知参数：%s\n' "$1" >&2
                print_usage >&2; exit 2
            fi ;;
    esac
done

if [ -z "$SDK_NAME" ]; then
    printf '缺少 SDK 名称\n' >&2; print_usage >&2; exit 2
fi
if [ -z "$ACTION" ]; then
    printf '需要指定 --check 或 --commit\n' >&2; print_usage >&2; exit 2
fi

# --- 定位并验证路径 ---
if [ -z "$REPO_ROOT" ]; then
    REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
fi

SDK_DIR="$REPO_ROOT/third_party/sdk/$SDK_NAME"
SDK_YAML="$SDK_DIR/sdk.yaml"
UPSTREAM_DIR="$SDK_DIR/upstream/luban-lite"
TARGETS_DIR="$REPO_ROOT/targets"

for d in "$SDK_DIR" "$UPSTREAM_DIR" "$TARGETS_DIR"; do
    if [ ! -d "$d" ]; then
        printf '目录不存在：%s\n' "$d" >&2; exit 1
    fi
done

if [ ! -f "$SDK_YAML" ]; then
    printf 'sdk.yaml 不存在：%s\n' "$SDK_YAML" >&2; exit 1
fi

for repo in "$REPO_ROOT" "$SDK_DIR" "$UPSTREAM_DIR"; do
    if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        printf '不是 Git 仓库：%s\n' "$repo" >&2; exit 1
    fi
done

# --- 读取各层 HEAD ---
UPSTREAM_HEAD=$(git -C "$UPSTREAM_DIR" rev-parse HEAD)
SDK_HEAD=$(git -C "$SDK_DIR" rev-parse HEAD)
SDK_YAML_UPSTREAM_REF=$(python3 "$PY_YAML_HELPER" read-sdk-upstream-ref "$SDK_YAML")
SDK_GITLINK=$(git -C "$REPO_ROOT" ls-tree HEAD "third_party/sdk/$SDK_NAME" 2>/dev/null | awk '{print $3}' || printf '')
UPSTREAM_GITLINK=$(git -C "$SDK_DIR" ls-tree HEAD "upstream/luban-lite" 2>/dev/null | awk '{print $3}' || printf '')

# --- 读取匹配 SDK 的 target YAML（不经吞错，原样传播） ---
# 此变量在 do_check / do_commit 中通过函数获取，避免同一行出现 2>/dev/null
read_target_refs_or_die() {
    python3 "$PY_YAML_HELPER" read-target-refs "$TARGETS_DIR" "$SDK_NAME"
}

# --- helper: 检查是否在正常分支上（非 detached HEAD）---
check_not_detached() {
    _desc="$1"
    _repo="$2"
    if ! git -C "$_repo" symbolic-ref --short HEAD >/dev/null 2>&1; then
        printf '%s处于分离头指针（detached HEAD）状态，无法提交。\n' "$_desc" >&2
        printf '请先切换到正常分支后再执行 --commit。\n' >&2
        return 1
    fi
}

# --- helper: 脏文件白名单检查 ---
# check_dirty_allowlist <repo> <description> <allow_patterns...>
check_dirty_allowlist() {
    _repo="$1"
    _desc="$2"
    shift 2
    dirty=$(git -C "$_repo" status --porcelain)
    if [ -z "$dirty" ]; then
        return 0
    fi
    _tmp=$(mktemp)
    printf '%s\n' "$dirty" > "$_tmp"
    _has=0
    while IFS= read -r line; do
        file=$(printf '%s\n' "$line" | sed 's/^...//')
        _allowed=0
        for _pat in "$@"; do
            case "$file" in
                $_pat) _allowed=1; break ;;
            esac
        done
        if [ "$_allowed" -eq 0 ]; then
            printf '%s存在不相关未提交变更：%s\n' "$_desc" "$file" >&2
            _has=1
        fi
    done < "$_tmp"
    rm -f "$_tmp"
    return "$_has"
}

# --- 一致性检查 (--check 模式) ---

do_check() {
    errors=0

    if [ "$SDK_YAML_UPSTREAM_REF" != "$UPSTREAM_HEAD" ]; then
        printf 'sdk.yaml upstream.ref 与 upstream/luban-lite HEAD 不一致\n' >&2
        printf '  sdk.yaml upstream.ref: %s\n' "$SDK_YAML_UPSTREAM_REF" >&2
        printf '  upstream/luban-lite HEAD: %s\n' "$UPSTREAM_HEAD" >&2
        errors=$((errors + 1))
    fi
    if [ -n "$UPSTREAM_GITLINK" ] && [ "$UPSTREAM_GITLINK" != "$UPSTREAM_HEAD" ]; then
        printf 'SDK 适配仓库记录的 upstream gitlink 与 upstream/luban-lite HEAD 不一致\n' >&2
        printf '  gitlink: %s\n' "$UPSTREAM_GITLINK" >&2
        printf '  HEAD:    %s\n' "$UPSTREAM_HEAD" >&2
        errors=$((errors + 1))
    fi

    # read-target-refs 失败时立即退出（如 target 缺少 sdk.ref）
    if ! target_refs=$(read_target_refs_or_die 2>"$_err_tmp"); then
        cat "$_err_tmp" >&2
        exit 1
    fi
    target_count=0
    if [ -n "$target_refs" ]; then
        printf '%s\n' "$target_refs" > "$_tmp"
        while IFS=: read -r tf tr; do
            target_count=$((target_count + 1))
            if [ "$tr" != "$SDK_HEAD" ]; then
                printf '%s 的 sdk.ref 与 SDK HEAD 不一致\n' "$tf" >&2
                printf '  sdk.ref: %s\n' "$tr" >&2
                printf '  SDK HEAD: %s\n' "$SDK_HEAD" >&2
                errors=$((errors + 1))
            fi
        done < "$_tmp"
    fi

    if [ -n "$SDK_GITLINK" ] && [ "$SDK_GITLINK" != "$SDK_HEAD" ]; then
        printf '主工程记录的 SDK gitlink 与 SDK HEAD 不一致\n' >&2
        printf '  gitlink: %s\n' "$SDK_GITLINK" >&2
        printf '  HEAD:    %s\n' "$SDK_HEAD" >&2
        errors=$((errors + 1))
    fi

    if [ "$errors" -eq 0 ]; then
        printf 'SDK：%s\n' "$SDK_NAME"
        printf 'upstream/luban-lite HEAD：%s\n' "$UPSTREAM_HEAD"
        printf 'SDK adapter HEAD：%s\n' "$SDK_HEAD"
        printf '已更新 target 数量：%s\n' "$target_count"
        printf '检查结果：指针一致\n'
        return 0
    else
        printf '检查结果：发现 %d 处不一致\n' "$errors" >&2
        return 1
    fi
}

# --- 安全预检 (--commit 模式) ---

do_preflight() {
    # upstream 必须干净
    up_dirty=$(git -C "$UPSTREAM_DIR" status --porcelain)
    if [ -n "$up_dirty" ]; then
        printf 'upstream/luban-lite 工作区存在未提交变更，无法执行同步：\n' >&2
        printf '%s\n' "$up_dirty" >&2
        printf '请先在 upstream/luban-lite 中提交或清理变更。\n' >&2
        return 1
    fi

    # SDK 适配仓库只允许 upstream/luban-lite 和 sdk.yaml 有变更
    if ! check_dirty_allowlist "$SDK_DIR" "SDK 适配仓库" "upstream/luban-lite" "sdk.yaml"; then
        return 1
    fi

    # 主工程只允许 third_party/sdk/<sdk-name> 和 targets/*.yaml 有变更
    sdk_sub="third_party/sdk/$SDK_NAME"
    if ! check_dirty_allowlist "$REPO_ROOT" "主工程" "$sdk_sub" "targets/*"; then
        return 1
    fi

    # 预检 detached HEAD
    if ! check_not_detached "SDK 适配仓库" "$SDK_DIR"; then return 1; fi
    if ! check_not_detached "主工程" "$REPO_ROOT"; then return 1; fi

    # 预检 target YAML 可解析、匹配 target 都有 sdk.ref
    # 放在所有写操作之前，防止 SDK 适配仓库提交后主工程失败造成半同步
    if ! read_target_refs_or_die >/dev/null 2>"$_err_tmp"; then
        cat "$_err_tmp" >&2
        return 1
    fi

    return 0
}

# --- 提交模式 ---

do_commit() {
    printf '正在执行安全预检...\n'
    if ! do_preflight; then
        exit 1
    fi
    printf '安全预检通过\n'

    # --- 第一步：更新并提交 SDK 适配仓库 ---
    sdk_changed=0

    if [ "$SDK_YAML_UPSTREAM_REF" != "$UPSTREAM_HEAD" ]; then
        python3 "$PY_YAML_HELPER" update-sdk-upstream-ref "$SDK_YAML" "$UPSTREAM_HEAD"
        python3 "$PY_YAML_HELPER" update-sdk-notes "$SDK_YAML" "$SDK_YAML_UPSTREAM_REF" "$UPSTREAM_HEAD"
        sdk_changed=1
    fi

    git -C "$SDK_DIR" add upstream/luban-lite 2>/dev/null || true

    if [ "$sdk_changed" -eq 1 ] || ! git -C "$SDK_DIR" diff --cached --quiet; then
        git -C "$SDK_DIR" add sdk.yaml upstream/luban-lite
        if ! git -C "$SDK_DIR" diff --cached --quiet; then
            git -C "$SDK_DIR" commit -m 'chore: 同步 Luban-Lite upstream 指针'
            printf 'SDK 适配仓库已提交：同步 Luban-Lite upstream 指针\n'
        fi
    else
        printf 'SDK 适配仓库指针已一致，无需提交\n'
    fi

    # --- 第二步：更新并提交主工程 ---
    NEW_SDK_HEAD=$(git -C "$SDK_DIR" rev-parse HEAD)

    # 读取匹配 target，失败时退出
    if ! target_refs=$(read_target_refs_or_die 2>"$_err_tmp"); then
        cat "$_err_tmp" >&2
        exit 1
    fi
    needs_update=0
    target_count=0
    if [ -n "$target_refs" ]; then
        printf '%s\n' "$target_refs" > "$_tmp"
        while IFS=: read -r tf tr; do
            target_count=$((target_count + 1))
            if [ "$tr" != "$NEW_SDK_HEAD" ]; then
                needs_update=1
            fi
        done < "$_tmp"
    fi

    if [ "$needs_update" -eq 1 ]; then
        python3 "$PY_YAML_HELPER" update-target-refs "$TARGETS_DIR" "$SDK_NAME" "$NEW_SDK_HEAD"
    fi

    git -C "$REPO_ROOT" add "third_party/sdk/$SDK_NAME" 2>/dev/null || true
    git -C "$REPO_ROOT" add targets/*.yaml 2>/dev/null || true

    if ! git -C "$REPO_ROOT" diff --cached --quiet; then
        git -C "$REPO_ROOT" commit -m 'chore: 同步 Luban-Lite SDK 指针'
        printf '主工程已提交：同步 Luban-Lite SDK 指针\n'
    else
        printf '主工程指针已一致，无需提交\n'
    fi

    # --- 最终报告 ---
    printf '\n========== 同步结果 ==========\n'
    printf 'SDK：%s\n' "$SDK_NAME"
    printf 'upstream/luban-lite HEAD：%s\n' "$(git -C "$UPSTREAM_DIR" rev-parse HEAD)"
    printf 'SDK adapter HEAD：%s\n' "$(git -C "$SDK_DIR" rev-parse HEAD)"
    printf '已更新 target 数量（匹配 SDK=%s）：%s\n' "$SDK_NAME" "$target_count"
    printf '检查结果：指针一致\n'
}

# --- 执行 ---
_tmp=$(mktemp)
_err_tmp=$(mktemp)
# shellcheck disable=SC2064
trap "rm -f $_tmp $_err_tmp" EXIT

if [ "$ACTION" = "check" ]; then
    do_check || exit 1
elif [ "$ACTION" = "commit" ]; then
    do_commit
fi
