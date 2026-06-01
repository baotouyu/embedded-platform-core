#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$SCRIPT_DIR
BUILD_DIR=$REPO_ROOT/build

print_help() {
    cat <<EOF
用法:
  ./build.sh <命令> [参数]

命令:
  help          显示帮助
  configure    生成 CMake 构建目录
  build        编译当前构建目录
  test         运行 host 单元测试和 API 契约测试
  package-host 生成 host/macOS 发布目录包
  export-ep    生成主工程静态库导出包 out/ep/<target>
  export-target 通过 targets/<target>.yaml 导出主工程静态库包
  prepare-sdk  通过 targets/<target>.yaml 准备工程外本地 SDK，默认 ../sdks
  build-firmware 通过 SDK 标准入口生成固件 out/firmware/<target>
  clean        清理 build 和 host/macOS 发布包
  all          依次执行 configure、build、test、package-host --clean

示例:
  ./build.sh help
  ./build.sh configure
  ./build.sh build
  ./build.sh test
  ./build.sh package-host --clean
  ./build.sh export-ep --clean
  ./build.sh export-target host_rtos_demo
  ./build.sh prepare-sdk host_rtos_demo
  EP_SDK_ROOT=/opt/ep-sdks ./build.sh prepare-sdk host_rtos_demo
  ./build.sh build-firmware host_rtos_demo --clean
  ./build.sh all
EOF
}

run_configure() {
    cmake -S "$REPO_ROOT" -B "$BUILD_DIR"
}

run_build() {
    cmake --build "$BUILD_DIR"
}

run_test() {
    cd "$REPO_ROOT"
    pytest tests/host_unit tests/api_contract -v
}

run_package_host() {
    "$REPO_ROOT/tools/scripts/package_host.sh" "$@"
}

run_export_ep() {
    "$REPO_ROOT/tools/scripts/export_ep_package.sh" "$@"
}

run_export_target() {
    target=${1:-}
    if [ -z "$target" ]; then
        printf '缺少 target 名称\n' >&2
        exit 2
    fi
    shift
    "$REPO_ROOT/tools/scripts/export_target.sh" --target "$target" "$@"
}

run_prepare_sdk() {
    target=${1:-}
    if [ -z "$target" ]; then
        printf '缺少 target 名称\n' >&2
        exit 2
    fi
    shift
    "$REPO_ROOT/tools/scripts/prepare_target_sdk.sh" --target "$target" "$@"
}

run_build_firmware() {
    target=${1:-}
    if [ -z "$target" ]; then
        printf '缺少 target 名称\n' >&2
        exit 2
    fi
    shift
    "$REPO_ROOT/tools/scripts/build_target_firmware.sh" --target "$target" "$@"
}

run_clean() {
    rm -rf "$BUILD_DIR" "$REPO_ROOT/out/packages/host_macos"
    printf '%s\n' "已清理 build 和 out/packages/host_macos"
}

command=${1:-help}
if [ "$#" -gt 0 ]; then
    shift
fi

case "$command" in
    help|-h|--help)
        print_help
        ;;
    configure)
        run_configure
        ;;
    build)
        run_build
        ;;
    test)
        run_test
        ;;
    package-host)
        run_package_host "$@"
        ;;
    export-ep)
        run_export_ep "$@"
        ;;
    export-target)
        run_export_target "$@"
        ;;
    prepare-sdk)
        run_prepare_sdk "$@"
        ;;
    build-firmware)
        run_build_firmware "$@"
        ;;
    clean)
        run_clean
        ;;
    all)
        run_configure
        run_build
        run_test
        run_package_host --clean "$@"
        ;;
    *)
        printf '未知命令：%s\n\n' "$command" >&2
        print_help >&2
        exit 2
        ;;
esac
