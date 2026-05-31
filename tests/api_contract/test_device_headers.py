import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEVICE_INCLUDE = REPO_ROOT / "components" / "device" / "include"
PLATFORM_INCLUDE = REPO_ROOT / "platforms" / "include"


def _require_compiler() -> str:
    compiler = shutil.which("clang") or shutil.which("cc")
    assert compiler, "Expected clang or cc to be available for compile smoke test"
    return compiler


def test_device_header_is_platform_neutral():
    header = DEVICE_INCLUDE / "ep_device.h"

    assert header.exists(), "Expected components/device/include/ep_device.h to exist"

    content = header.read_text(encoding="utf-8")
    forbidden = [
        "pthread.h",
        "rtthread.h",
        "unistd.h",
        "fcntl.h",
        "sys/",
        "third_party/",
        "lvgl.h",
    ]
    found = [name for name in forbidden if name in content]

    assert not found, f"ep_device.h must stay platform-neutral, found: {found}"


def test_device_header_compiles_standalone(tmp_path):
    compiler = _require_compiler()
    source = tmp_path / "device_header_smoke.c"
    obj = tmp_path / "device_header_smoke.o"

    source.write_text(
        textwrap.dedent(
            """
            #include "ep_device.h"
            #include "ep_device.h"

            int main(void)
            {
                ep_device_desc_t desc;
                ep_device_t *device = 0;
                ep_device_type_e type = EP_DEVICE_TYPE_DISPLAY;
                ep_device_state_e state = EP_DEVICE_STATE_ONLINE;
                ep_platform_capability_e capability = EP_PLATFORM_CAPABILITY_DISPLAY;

                int (*init_fn)(void) = ep_device_init;
                int (*register_fn)(const ep_device_desc_t *, ep_device_t **) = ep_device_register;
                ep_device_t *(*find_fn)(const char *) = ep_device_find;
                ep_device_t *(*find_by_type_fn)(ep_device_type_e, unsigned int) = ep_device_find_by_type;
                const char *(*name_fn)(const ep_device_t *) = ep_device_name;
                ep_device_type_e (*type_fn)(const ep_device_t *) = ep_device_type;
                ep_device_state_e (*state_fn)(const ep_device_t *) = ep_device_state;
                ep_platform_capability_e (*capability_fn)(const ep_device_t *) = ep_device_capability;

                desc.name = "display0";
                desc.type = type;
                desc.state = state;
                desc.capability = capability;
                desc.context = 0;

                return (device == 0 && init_fn && register_fn && find_fn &&
                        find_by_type_fn && name_fn && type_fn && state_fn &&
                        capability_fn && desc.name != 0) ? 0 : 1;
            }
            """
        ).strip()
        + "\n"
    )

    result = subprocess.run(
        [
            compiler,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(DEVICE_INCLUDE),
            "-I",
            str(PLATFORM_INCLUDE),
            "-c",
            str(source),
            "-o",
            str(obj),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, (
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
