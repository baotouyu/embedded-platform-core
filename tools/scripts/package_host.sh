#!/bin/sh

set -eu

PACKAGE_NAME=host_macos
HOST_EXECUTABLES="ep_platform_host_posix ep_host_app ep_host_resource_smoke ep_host_lvgl_demo ep_host_lvgl_widgets_demo"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
OUTPUT_DIR="out/packages"
CLEAN=0

print_help() {
    cat <<EOF
用法:
  tools/scripts/package_host.sh [参数]

参数:
  --repo-root <路径>   仓库根目录，默认自动使用当前脚本所在仓库
  --output-dir <路径>  输出父目录，脚本会生成 <路径>/host_macos
  --clean             打包前删除已有 host_macos 输出目录
  -h, --help          显示帮助

示例:
  ./build.sh package-host --clean
  tools/scripts/package_host.sh --clean

默认输出:
  out/packages/host_macos
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
        --output-dir)
            [ "$#" -ge 2 ] || die "缺少 --output-dir 参数值"
            OUTPUT_DIR=$2
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

REPO_ROOT=$(CDPATH= cd -- "$REPO_ROOT" && pwd)
OUTPUT_DIR=$(resolve_path "$OUTPUT_DIR" "$REPO_ROOT")
PACKAGE_ROOT=$OUTPUT_DIR/$PACKAGE_NAME
BUILD_OUTPUT_DIR=$REPO_ROOT/build/platforms/host/posix

missing=""
for executable in $HOST_EXECUTABLES; do
    path=$BUILD_OUTPUT_DIR/$executable
    if [ ! -e "$path" ]; then
        missing="${missing}
- $path"
    fi
done

for path in \
    "$REPO_ROOT/config/profiles/host.cfg" \
    "$REPO_ROOT/resources/host" \
    "$REPO_ROOT/resources/common"
do
    if [ ! -e "$path" ]; then
        missing="${missing}
- $path"
    fi
done

if [ -n "$missing" ]; then
    printf '缺少必需产物：%s\n' "$missing" >&2
    exit 1
fi

copy_file() {
    src=$1
    dst=$2

    mkdir -p "$(dirname -- "$dst")"
    cp -p "$src" "$dst"
}

copy_tree_without_gitkeep() {
    src=$1
    dst=$2

    rm -rf "$dst"
    mkdir -p "$dst"

    (
        cd "$src"
        find . -type d -print | while IFS= read -r dir; do
            mkdir -p "$dst/$dir"
        done
        find . -type f ! -name .gitkeep -print | while IFS= read -r file; do
            mkdir -p "$(dirname -- "$dst/$file")"
            cp -p "$src/$file" "$dst/$file"
        done
    )
}

write_manifest() {
    manifest=$PACKAGE_ROOT/manifest.txt

    {
        printf 'package=%s\n' "$PACKAGE_NAME"
        printf 'format=directory\n'
        printf 'platform=host/macOS\n'
        printf '\n'
        printf '[files]\n'
        for executable in $HOST_EXECUTABLES; do
            printf 'bin/%s\n' "$executable"
        done
        printf 'config/profiles/host.cfg\n'
        find "$PACKAGE_ROOT/resources/host" "$PACKAGE_ROOT/resources/common" -type f -print | sort | while IFS= read -r file; do
            relative=${file#"$PACKAGE_ROOT"/}
            printf '%s\n' "$relative"
        done
    } > "$manifest"
}

if [ "$CLEAN" -eq 1 ]; then
    rm -rf "$PACKAGE_ROOT"
fi

mkdir -p "$PACKAGE_ROOT/bin" "$PACKAGE_ROOT/config/profiles"

for executable in $HOST_EXECUTABLES; do
    copy_file "$BUILD_OUTPUT_DIR/$executable" "$PACKAGE_ROOT/bin/$executable"
done

copy_file "$REPO_ROOT/config/profiles/host.cfg" "$PACKAGE_ROOT/config/profiles/host.cfg"
copy_tree_without_gitkeep "$REPO_ROOT/resources/host" "$PACKAGE_ROOT/resources/host"
copy_tree_without_gitkeep "$REPO_ROOT/resources/common" "$PACKAGE_ROOT/resources/common"
write_manifest

file_count=$(find "$PACKAGE_ROOT" -type f | wc -l | tr -d ' ')

printf 'host/macOS 发布包已生成：%s\n' "$PACKAGE_ROOT"
printf '文件数量：%s\n' "$file_count"
printf '清单文件：%s\n' "$PACKAGE_ROOT/manifest.txt"
