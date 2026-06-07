import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def _compile_and_run(tmp_path, name, main_source, repo_source):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / f"{name}.c"
    executable = tmp_path / name
    source.write_text(textwrap.dedent(main_source).strip() + "\n", encoding="utf-8")

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c99",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(REPO_ROOT / "hal/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / repo_source),
            "-o",
            str(executable),
        ],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert compile_result.returncode == 0, compile_result.stderr

    run_result = subprocess.run(
        [str(executable)],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert run_result.returncode == 0, run_result.stdout + run_result.stderr


def _gpio_stub_smoke_source(anchor_name):
    return f"""
    #include "ep_hal_err.h"
    #include "ep_hal_gpio.h"

    int {anchor_name}(void);

    int main(void)
    {{
        ep_gpio_t *gpio = 0;

        if ({anchor_name}() != 0) {{
            return 1;
        }}

        if (ep_gpio_request(0, "lcd_sleep_gpio") != EP_ERR_INVAL) {{
            return 2;
        }}

        if (ep_gpio_request(&gpio, 0) != EP_ERR_INVAL) {{
            return 3;
        }}

        if (ep_gpio_request(&gpio, "missing_gpio") != EP_ERR_UNSUPPORTED) {{
            return 4;
        }}

        if (gpio != 0) {{
            return 5;
        }}

        if (ep_gpio_request(&gpio, "lcd_sleep_gpio") != EP_OK) {{
            return 6;
        }}

        if (gpio == 0) {{
            return 7;
        }}

        if (ep_gpio_set_direction(gpio, EP_GPIO_OUTPUT) != EP_OK) {{
            return 8;
        }}

        if (ep_gpio_write(gpio, 1) != EP_ERR_UNSUPPORTED) {{
            return 9;
        }}

        return 0;
    }}
    """


def test_host_hal_stub_rejects_unknown_gpio_names(tmp_path):
    _compile_and_run(
        tmp_path,
        "host_hal_stub_gpio_smoke",
        _gpio_stub_smoke_source("ep_host_hal_stub_link_anchor"),
        "platforms/host/posix/hal_port/ep_host_hal_stub.c",
    )


def test_linux_hal_stub_rejects_unknown_gpio_names(tmp_path):
    _compile_and_run(
        tmp_path,
        "linux_hal_stub_gpio_smoke",
        _gpio_stub_smoke_source("ep_linux_hal_stub"),
        "platforms/linux/demo_family/hal_port/ep_linux_hal_stub.c",
    )
