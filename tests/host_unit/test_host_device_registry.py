import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_device_component_is_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    device_cmake_path = REPO_ROOT / "components/device/CMakeLists.txt"

    assert "add_subdirectory(components/device)" in root_cmake
    assert device_cmake_path.exists()

    device_cmake = device_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_device STATIC" in device_cmake
    assert "src/ep_device.c" in device_cmake
    assert "ep_platform_api" in device_cmake


def test_device_component_cmake_target_builds(tmp_path):
    build_dir = tmp_path / "device-build"

    configure = subprocess.run(
        ["cmake", "-S", str(REPO_ROOT), "-B", str(build_dir)],
        capture_output=True,
        text=True,
    )
    assert configure.returncode == 0, (
        f"configure failed\nstdout:\n{configure.stdout}\nstderr:\n{configure.stderr}"
    )

    build = subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "ep_components_device"],
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (
        f"build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )


def test_host_device_registry_registers_and_finds_devices(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_device_registry_smoke.c"
    executable = tmp_path / "host_device_registry_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_device.h"
            #include "ep_osal_err.h"

            #include <stdio.h>
            #include <string.h>

            int main(void)
            {
                ep_device_desc_t display_desc;
                ep_device_desc_t touch_desc;
                ep_device_t *display = 0;
                ep_device_t *touch = 0;
                ep_device_t *found = 0;
                int i;
                char names[9][16];

                display_desc.name = "display0";
                display_desc.type = EP_DEVICE_TYPE_DISPLAY;
                display_desc.state = EP_DEVICE_STATE_ONLINE;
                display_desc.capability = EP_PLATFORM_CAPABILITY_DISPLAY;
                display_desc.context = (void *)0x1234;

                if (ep_device_register(&display_desc, &display) != EP_ERR_UNSUPPORTED) {
                    return 1;
                }

                if (ep_device_init() != EP_OK) {
                    return 2;
                }

                if (ep_device_init() != EP_OK) {
                    return 3;
                }

                if (ep_device_register(&display_desc, &display) != EP_OK) {
                    return 4;
                }

                if (display == 0) {
                    return 5;
                }

                touch_desc.name = "touch0";
                touch_desc.type = EP_DEVICE_TYPE_TOUCH;
                touch_desc.state = EP_DEVICE_STATE_OFFLINE;
                touch_desc.capability = EP_PLATFORM_CAPABILITY_TOUCH;
                touch_desc.context = 0;

                if (ep_device_register(&touch_desc, &touch) != EP_OK) {
                    return 6;
                }

                found = ep_device_find("display0");
                if (found != display) {
                    return 7;
                }

                if (strcmp(ep_device_name(found), "display0") != 0) {
                    return 8;
                }

                if (ep_device_type(found) != EP_DEVICE_TYPE_DISPLAY) {
                    return 9;
                }

                if (ep_device_state(found) != EP_DEVICE_STATE_ONLINE) {
                    return 10;
                }

                if (ep_device_capability(found) != EP_PLATFORM_CAPABILITY_DISPLAY) {
                    return 11;
                }

                if (ep_device_context(found) != (void *)0x1234) {
                    return 12;
                }

                if (ep_device_find_by_type(EP_DEVICE_TYPE_TOUCH, 0) != touch) {
                    return 13;
                }

                if (ep_device_find_by_type(EP_DEVICE_TYPE_TOUCH, 1) != 0) {
                    return 14;
                }

                if (ep_device_register(&display_desc, 0) != EP_ERR_BUSY) {
                    return 15;
                }

                if (ep_device_register(0, &found) != EP_ERR_INVAL) {
                    return 16;
                }

                display_desc.name = "";
                if (ep_device_register(&display_desc, &found) != EP_ERR_INVAL) {
                    return 17;
                }

                display_desc.name = "bad";
                display_desc.type = EP_DEVICE_TYPE_COUNT;
                if (ep_device_register(&display_desc, &found) != EP_ERR_INVAL) {
                    return 18;
                }

                display_desc.type = EP_DEVICE_TYPE_DISPLAY;
                display_desc.state = EP_DEVICE_STATE_COUNT;
                if (ep_device_register(&display_desc, &found) != EP_ERR_INVAL) {
                    return 19;
                }

                for (i = 0; i < 9; ++i) {
                    ep_device_desc_t desc;
                    (void)snprintf(names[i], sizeof(names[i]), "other%d", i);
                    desc.name = names[i];
                    desc.type = EP_DEVICE_TYPE_OTHER;
                    desc.state = EP_DEVICE_STATE_ONLINE;
                    desc.capability = EP_PLATFORM_CAPABILITY_COUNT;
                    desc.context = 0;

                    if (i < 6) {
                        if (ep_device_register(&desc, &found) != EP_OK) {
                            return 30 + i;
                        }
                    } else if (ep_device_register(&desc, &found) != EP_ERR_BUSY) {
                        return 40 + i;
                    }
                }

                return 0;
            }
            """
        ).strip()
        + "\n"
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(REPO_ROOT / "components/device/include"),
            "-I",
            str(REPO_ROOT / "platforms/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/device/src/ep_device.c"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert compile_result.returncode == 0, (
        f"stdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
    )

    run_result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert run_result.returncode == 0, (
        f"stdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
