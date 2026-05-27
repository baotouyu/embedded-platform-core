import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HAL_INCLUDE = REPO_ROOT / "hal" / "include"
OSAL_INCLUDE = REPO_ROOT / "osal" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")

HEADER_SNIPPETS = {
    "ep_hal_types.h": """
        ep_gpio_t *gpio = 0;
        ep_uart_t *uart = 0;
        ep_i2c_t *i2c = 0;
        ep_spi_t *spi = 0;
        ep_pwm_t *pwm = 0;
        ep_adc_t *adc = 0;
        return (gpio == 0 && uart == 0 && i2c == 0 && spi == 0 && pwm == 0 && adc == 0) ? 0 : 1;
    """,
    "ep_hal_err.h": """
        ep_err_e err = EP_OK;
        err = EP_ERR_UNSUPPORTED;
        return err == EP_ERR_UNSUPPORTED ? 0 : 1;
    """,
    "ep_hal_gpio.h": """
        ep_gpio_t *gpio = 0;
        ep_gpio_dir_e dir = EP_GPIO_OUTPUT;
        int (*request_fn)(ep_gpio_t **, const char *) = ep_gpio_request;
        int (*set_direction_fn)(ep_gpio_t *, ep_gpio_dir_e) = ep_gpio_set_direction;
        int (*write_fn)(ep_gpio_t *, int) = ep_gpio_write;
        int (*read_fn)(ep_gpio_t *, int *) = ep_gpio_read;
        return (gpio == 0 && dir == EP_GPIO_OUTPUT && request_fn && set_direction_fn && write_fn && read_fn) ? 0 : 1;
    """,
    "ep_hal_uart.h": """
        ep_uart_t *uart = 0;
        int (*open_fn)(ep_uart_t **, const char *) = ep_uart_open;
        int (*write_fn)(ep_uart_t *, const void *, size_t) = ep_uart_write;
        int (*read_fn)(ep_uart_t *, void *, size_t, unsigned int) = ep_uart_read;
        int (*close_fn)(ep_uart_t *) = ep_uart_close;
        return (uart == 0 && open_fn && write_fn && read_fn && close_fn) ? 0 : 1;
    """,
    "ep_hal_i2c.h": """
        ep_i2c_t *bus = 0;
        int (*open_fn)(ep_i2c_t **, const char *) = ep_i2c_open;
        int (*write_fn)(ep_i2c_t *, uint16_t, const void *, size_t) = ep_i2c_write;
        int (*read_fn)(ep_i2c_t *, uint16_t, void *, size_t) = ep_i2c_read;
        return (bus == 0 && open_fn && write_fn && read_fn) ? 0 : 1;
    """,
    "ep_hal_spi.h": """
        ep_spi_t *bus = 0;
        int (*open_fn)(ep_spi_t **, const char *) = ep_spi_open;
        int (*transfer_fn)(ep_spi_t *, const void *, void *, size_t) = ep_spi_transfer;
        return (bus == 0 && open_fn && transfer_fn) ? 0 : 1;
    """,
    "ep_hal_pwm.h": """
        ep_pwm_t *pwm = 0;
        int (*open_fn)(ep_pwm_t **, const char *) = ep_pwm_open;
        int (*set_fn)(ep_pwm_t *, unsigned int, unsigned int) = ep_pwm_set;
        return (pwm == 0 && open_fn && set_fn) ? 0 : 1;
    """,
    "ep_hal_adc.h": """
        ep_adc_t *adc = 0;
        int (*open_fn)(ep_adc_t **, const char *) = ep_adc_open;
        int (*read_fn)(ep_adc_t *, uint32_t *) = ep_adc_read;
        return (adc == 0 && open_fn && read_fn) ? 0 : 1;
    """,
}


def _compile_header_standalone(tmp_path: Path, header_name: str, body: str) -> subprocess.CompletedProcess[str]:
    source = tmp_path / f"{header_name}.c"
    obj = tmp_path / f"{header_name}.o"
    source.write_text(
        textwrap.dedent(
            f"""
            #include "{header_name}"
            #include "{header_name}"

            int main(void) {{
            {textwrap.indent(textwrap.dedent(body).strip(), "    ")}
            }}
            """
        ).strip()
        + "\n"
    )

    return subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(HAL_INCLUDE),
            "-I",
            str(OSAL_INCLUDE),
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


def test_hal_headers_exist():
    for header_name in HEADER_SNIPPETS:
        assert (HAL_INCLUDE / header_name).is_file(), f"Missing HAL public header: {header_name}"


def test_hal_headers_compile_standalone(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    failures = []
    for header_name, body in HEADER_SNIPPETS.items():
        result = _compile_header_standalone(tmp_path, header_name, body)
        if result.returncode != 0:
            failures.append(f"{header_name}: {result.stderr}")

    assert not failures, "\n".join(failures)
