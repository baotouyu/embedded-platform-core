import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_rtos_default_devices_are_wired_into_platform_target():
    cmake = (REPO_ROOT / "platforms/rtos/demo_family/CMakeLists.txt").read_text(encoding="utf-8")
    export_cmake = (REPO_ROOT / "cmake/modules/ep_export_targets.cmake").read_text(encoding="utf-8")
    export_script = (REPO_ROOT / "tools/scripts/export_sdk_ep_package.sh").read_text(encoding="utf-8")

    assert "component_port/ep_rtos_default_devices.c" in cmake
    assert "ep_components_device" in cmake
    assert "platforms/rtos/demo_family/component_port/ep_rtos_default_devices.c" in export_cmake
    assert "components/device/src/ep_device.c" in export_script
    assert "platforms/rtos/demo_family/component_port/ep_rtos_default_devices.c" in export_script


def test_rtos_default_devices_register_ki_logical_devices(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "rtos_default_devices_smoke.c"
    executable = tmp_path / "rtos_default_devices_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_device.h"
            #include "ep_framework.h"
            #include "ep_osal_err.h"

            int main(void)
            {
                ep_device_t *device;

                if (ep_device_init() != EP_OK) {
                    return 1;
                }

                if (ep_platform_register_default_devices() != EP_OK) {
                    return 2;
                }

                if (ep_platform_register_default_devices() != EP_OK) {
                    return 3;
                }

                device = ep_device_find("console_uart");
                if (device == 0 ||
                    ep_device_type(device) != EP_DEVICE_TYPE_UART ||
                    ep_device_capability(device) != EP_PLATFORM_CAPABILITY_UART ||
                    ep_device_state(device) != EP_DEVICE_STATE_ONLINE) {
                    return 4;
                }

                device = ep_device_find("power_uart");
                if (device == 0 ||
                    ep_device_type(device) != EP_DEVICE_TYPE_UART ||
                    ep_device_capability(device) != EP_PLATFORM_CAPABILITY_UART ||
                    ep_device_state(device) != EP_DEVICE_STATE_ONLINE) {
                    return 5;
                }

                device = ep_device_find("beep_pwm");
                if (device == 0 ||
                    ep_device_type(device) != EP_DEVICE_TYPE_OTHER ||
                    ep_device_capability(device) != EP_PLATFORM_CAPABILITY_PWM ||
                    ep_device_state(device) != EP_DEVICE_STATE_ONLINE) {
                    return 6;
                }

                device = ep_device_find("rtc_bus");
                if (device == 0 ||
                    ep_device_type(device) != EP_DEVICE_TYPE_I2C ||
                    ep_device_capability(device) != EP_PLATFORM_CAPABILITY_I2C ||
                    ep_device_state(device) != EP_DEVICE_STATE_ONLINE) {
                    return 7;
                }

                device = ep_device_find("lcd_sleep_gpio");
                if (device == 0 ||
                    ep_device_type(device) != EP_DEVICE_TYPE_GPIO ||
                    ep_device_capability(device) != EP_PLATFORM_CAPABILITY_GPIO ||
                    ep_device_state(device) != EP_DEVICE_STATE_ONLINE) {
                    return 8;
                }

                device = ep_device_find("panel_enable_gpio");
                if (device == 0 ||
                    ep_device_type(device) != EP_DEVICE_TYPE_GPIO ||
                    ep_device_capability(device) != EP_PLATFORM_CAPABILITY_GPIO ||
                    ep_device_state(device) != EP_DEVICE_STATE_ONLINE) {
                    return 9;
                }

                if (ep_device_find_by_type(EP_DEVICE_TYPE_UART, 0) == 0 ||
                    ep_device_find_by_type(EP_DEVICE_TYPE_UART, 1) == 0 ||
                    ep_device_find_by_type(EP_DEVICE_TYPE_UART, 2) != 0) {
                    return 10;
                }

                if (ep_device_find_by_type(EP_DEVICE_TYPE_GPIO, 0) == 0 ||
                    ep_device_find_by_type(EP_DEVICE_TYPE_GPIO, 1) == 0 ||
                    ep_device_find_by_type(EP_DEVICE_TYPE_GPIO, 2) != 0) {
                    return 11;
                }

                return 0;
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(REPO_ROOT / "core/include"),
            "-I",
            str(REPO_ROOT / "components/device/include"),
            "-I",
            str(REPO_ROOT / "platforms/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/device/src/ep_device.c"),
            str(REPO_ROOT / "platforms/rtos/demo_family/component_port/ep_rtos_default_devices.c"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert compile_result.returncode == 0, (
        f"compile failed\nstdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
    )

    run_result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert run_result.returncode == 0, (
        f"run failed with {run_result.returncode}\nstdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )


def test_framework_links_rtos_default_devices_as_required_platform_symbol(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "framework_rtos_default_devices_link_smoke.c"
    executable = tmp_path / "framework_rtos_default_devices_link_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_device.h"
            #include "ep_framework.h"
            #include "ep_osal_err.h"

            int app_main(void)
            {
                return 0;
            }

            int ep_platform_boot(void)
            {
                return 0;
            }

            int main(void)
            {
                if (ep_framework_init() != EP_OK) {
                    return 1;
                }

                return ep_device_find("console_uart") != 0 ? 0 : 2;
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(REPO_ROOT / "core/include"),
            "-I",
            str(REPO_ROOT / "app/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            "-I",
            str(REPO_ROOT / "platforms/include"),
            "-I",
            str(REPO_ROOT / "components/device/include"),
            "-I",
            str(REPO_ROOT / "components/log/include"),
            "-I",
            str(REPO_ROOT / "components/config/include"),
            "-I",
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "components/timer/include"),
            "-I",
            str(REPO_ROOT / "components/file/include"),
            "-I",
            str(REPO_ROOT / "third_party/external/EasyLogger/easylogger/inc"),
            str(source),
            str(REPO_ROOT / "core/src/ep_framework.c"),
            str(REPO_ROOT / "components/device/src/ep_device.c"),
            str(REPO_ROOT / "platforms/rtos/demo_family/component_port/ep_rtos_default_devices.c"),
            str(REPO_ROOT / "components/log/src/ep_log.c"),
            str(REPO_ROOT / "components/config/src/ep_config.c"),
            str(REPO_ROOT / "components/event/src/ep_event.c"),
            str(REPO_ROOT / "components/timer/src/ep_timer.c"),
            str(REPO_ROOT / "components/file/src/ep_file.c"),
            str(REPO_ROOT / "third_party/external/EasyLogger/easylogger/src/elog.c"),
            str(REPO_ROOT / "third_party/external/EasyLogger/easylogger/src/elog_utils.c"),
            str(REPO_ROOT / "third_party/external/EasyLogger/easylogger/port/elog_port.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_time.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
            "-pthread",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert compile_result.returncode == 0, (
        f"compile failed\nstdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
    )

    run_result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert run_result.returncode == 0, (
        f"run failed with {run_result.returncode}\nstdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
