#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=host_rtos_demo
OUTPUT_DIR=out/ep
CLEAN=0

print_help() {
    cat <<EOF
用法:
  tools/scripts/export_ep_package.sh [参数]

参数:
  --repo-root <路径>   仓库根目录，默认自动使用当前脚本所在仓库
  --target <名称>      导出目标名称，默认 host_rtos_demo
  --output-dir <路径>  输出父目录，脚本会生成 <路径>/<target>
  --clean             导出前删除已有 target 输出目录
  -h, --help          显示帮助

默认输出:
  out/ep/<target>
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

json_escape() {
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
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
PACKAGE_ROOT=$OUTPUT_DIR/$TARGET
ARCHIVE=$REPO_ROOT/build/libep_app_core_export.a

[ -f "$ARCHIVE" ] || die "缺少静态库产物：${ARCHIVE}，请先执行 ./build.sh build"

HEADER_DIRS="
core/include
app/include
components/log/include
components/config/include
components/event/include
components/timer/include
components/file/include
components/device/include
components/ui/include
osal/include
hal/include
platforms/include
"

missing=""
for dir in $HEADER_DIRS; do
    [ -d "$REPO_ROOT/$dir" ] || missing="${missing}
- $REPO_ROOT/$dir"
done

[ -z "$missing" ] || die "缺少头文件目录：$missing"

if [ "$CLEAN" -eq 1 ]; then
    rm -rf "$PACKAGE_ROOT"
fi

mkdir -p "$PACKAGE_ROOT/lib" "$PACKAGE_ROOT/include"
cp -p "$ARCHIVE" "$PACKAGE_ROOT/lib/libep_app_core.a"

for dir in $HEADER_DIRS; do
    find "$REPO_ROOT/$dir" -type f -name '*.h' -print | while IFS= read -r header; do
        cp -p "$header" "$PACKAGE_ROOT/include/$(basename -- "$header")"
    done
done

MANIFEST=$PACKAGE_ROOT/manifest.json
{
    printf '{\n'
    printf '  "package": "ep_app_core",\n'
    printf '  "target": "%s",\n' "$(json_escape "$TARGET")"
    printf '  "format": "static-library",\n'
    printf '  "library": "lib/libep_app_core.a",\n'
    printf '  "headers": [\n'

    first=1
    find "$PACKAGE_ROOT/include" -type f -name '*.h' -print | sort | while IFS= read -r header; do
        relative=${header#"$PACKAGE_ROOT"/}
        if [ "$first" -eq 1 ]; then
            first=0
        else
            printf ',\n'
        fi
        printf '    "%s"' "$(json_escape "$relative")"
    done

    printf '\n  ]\n'
    printf '}\n'
} > "$MANIFEST"

file_count=$(find "$PACKAGE_ROOT" -type f | wc -l | tr -d ' ')

printf 'EP 静态库导出包已生成：%s\n' "$PACKAGE_ROOT"
printf '文件数量：%s\n' "$file_count"
printf '清单文件：%s\n' "$MANIFEST"
