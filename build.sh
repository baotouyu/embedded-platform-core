#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$SCRIPT_DIR
BUILD_DIR=$REPO_ROOT/build

print_help() {
    cat <<EOF
用法:
  ./build.sh [命令] [参数]

命令:
  help          显示帮助
  interactive   交互选择 target 和动作
  configure    生成 CMake 构建目录
  build        编译当前构建目录
  test         运行 host 单元测试和 API 契约测试
  package-host 生成 host/macOS 发布目录包
  export-ep    生成主工程静态库导出包 out/ep/<target>
  export-target 通过 targets/<target>.yaml 导出主工程静态库包
  prepare-sdk  通过 targets/<target>.yaml 准备 SDK，优先 third_party/sdk/<sdk.name>，否则默认 ../sdks
  build-firmware 通过 SDK 标准入口生成固件 out/firmware/<target>
  check-env   检查 SDK 环境是否就绪
  install-env 安装/修复 SDK 环境依赖
  validate-targets 校验 targets/*.yaml 描述文件
  validate-ep-package 校验 EP 导出包 manifest 是否匹配 target
  clean        清理 build 和 host/macOS 发布包
  all          依次执行 configure、build、test、package-host --clean

示例:
  ./build.sh
  ./build.sh help
  ./build.sh interactive
  ./build.sh configure
  ./build.sh build
  ./build.sh test
  ./build.sh package-host --clean
  ./build.sh export-ep --clean
  ./build.sh export-target host_rtos_demo
  ./build.sh prepare-sdk host_rtos_demo
  EP_SDK_ROOT=/opt/ep-sdks ./build.sh prepare-sdk host_rtos_demo
  ./build.sh check-env host_rtos_demo
  ./build.sh install-env host_rtos_demo
  ./build.sh build-firmware host_rtos_demo --clean
  ./build.sh validate-targets
  ./build.sh validate-ep-package host_rtos_demo
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

run_check_env() {
    target=${1:-}
    if [ -z "$target" ]; then
        printf '缺少 target 名称\n' >&2
        exit 2
    fi
    shift
    "$REPO_ROOT/tools/scripts/check_target_env.sh" --target "$target" "$@"
}

run_install_env() {
    target=${1:-}
    if [ -z "$target" ]; then
        printf '缺少 target 名称\n' >&2
        exit 2
    fi
    shift
    "$REPO_ROOT/tools/scripts/install_target_env.sh" --target "$target" "$@"
}

run_validate_targets() {
    "$REPO_ROOT/tools/scripts/validate_targets.sh" "$@"
}

run_validate_ep_package() {
    target=${1:-}
    if [ -z "$target" ]; then
        printf '缺少 target 名称\n' >&2
        exit 2
    fi
    shift
    "$REPO_ROOT/tools/scripts/validate_ep_package.sh" --target "$target" "$@"
}

run_interactive() {
    selection=$("$REPO_ROOT/tools/scripts/select_target.sh" --verbose)
    target=$(printf '%s\n' "$selection" | sed -n 's/^target=//p')
    action=$(printf '%s\n' "$selection" | sed -n 's/^action=//p')

    if [ -z "$target" ] || [ -z "$action" ]; then
        printf '交互选择结果无效\n' >&2
        exit 1
    fi

    case "$action" in
        show-target)
            printf '已选择 target：%s\n' "$target"
            printf '已选择动作：%s\n' "$action"
            ;;
        prepare-sdk)
            run_prepare_sdk "$target"
            ;;
        export-target)
            run_export_target "$target"
            ;;
        build-firmware)
            run_build_firmware "$target"
            ;;
        check-env)
            run_check_env "$target"
            ;;
        install-env)
            run_install_env "$target"
            ;;
        full)
            run_prepare_sdk "$target"
            run_check_env "$target"
            run_export_target "$target"
            run_build_firmware "$target"
            ;;
        *)
            printf '未知交互动作：%s\n' "$action" >&2
            exit 2
            ;;
    esac
}

run_clean() {
    rm -rf "$BUILD_DIR" "$REPO_ROOT/out/packages/host_macos"
    printf '%s\n' "已清理 build 和 out/packages/host_macos"
}

command=${1:-interactive}
if [ "$#" -gt 0 ]; then
    shift
fi

case "$command" in
    help|-h|--help)
        print_help
        ;;
    interactive)
        run_interactive
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
    check-env)
        run_check_env "$@"
        ;;
    install-env)
        run_install_env "$@"
        ;;
    validate-targets)
        run_validate_targets "$@"
        ;;
    validate-ep-package)
        run_validate_ep_package "$@"
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
