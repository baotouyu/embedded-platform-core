import shutil
import subprocess
import textwrap
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[2]
HAL_INCLUDE = REPO_ROOT / "hal" / "include"
OSAL_INCLUDE = REPO_ROOT / "osal" / "include"

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
        err = EP_ERR_INVAL;
        err = EP_ERR_TIMEOUT;
        err = EP_ERR_BUSY;
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
        int (*enable_fn)(ep_pwm_t *) = ep_pwm_enable;
        int (*disable_fn)(ep_pwm_t *) = ep_pwm_disable;
        int (*close_fn)(ep_pwm_t *) = ep_pwm_close;
        return (pwm == 0 && open_fn && set_fn && enable_fn && disable_fn && close_fn) ? 0 : 1;
    """,
    "ep_hal_adc.h": """
        ep_adc_t *adc = 0;
        int (*open_fn)(ep_adc_t **, const char *) = ep_adc_open;
        int (*read_fn)(ep_adc_t *, uint32_t *) = ep_adc_read;
        return (adc == 0 && open_fn && read_fn) ? 0 : 1;
    """,
}


def _require_compiler() -> str:
    compiler = shutil.which("clang") or shutil.which("cc")
    assert compiler, "Expected clang or cc to be available for compile smoke test"
    return compiler


def _compile_header_standalone(tmp_path: Path, header_name: str, body: str) -> subprocess.CompletedProcess[str]:
    compiler = _require_compiler()
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
            compiler,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
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


def _format_compile_failure(header_name: str, result: subprocess.CompletedProcess[str]) -> str:
    return f"{header_name}: stdout:\n{result.stdout}\nstderr:\n{result.stderr}"


def test_hal_headers_exist():
    for header_name in HEADER_SNIPPETS:
        assert (HAL_INCLUDE / header_name).is_file(), f"Missing HAL public header: {header_name}"


def test_require_compiler_prefers_clang_then_cc(monkeypatch):
    def fake_which(name):
        return {"clang": None, "cc": "/usr/bin/cc"}.get(name)

    monkeypatch.setattr(shutil, "which", fake_which)

    assert _require_compiler() == "/usr/bin/cc"


def test_ep_hal_err_snippet_covers_full_public_error_surface():
    snippet = HEADER_SNIPPETS["ep_hal_err.h"]

    assert "EP_OK" in snippet
    assert "EP_ERR_INVAL" in snippet
    assert "EP_ERR_TIMEOUT" in snippet
    assert "EP_ERR_BUSY" in snippet
    assert "EP_ERR_UNSUPPORTED" in snippet


def test_compile_header_standalone_uses_werror(monkeypatch, tmp_path):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    _compile_header_standalone(tmp_path, "ep_hal_types.h", HEADER_SNIPPETS["ep_hal_types.h"])

    assert "-Werror" in captured["cmd"]


def test_format_compile_failure_reports_stdout_and_stderr():
    result = SimpleNamespace(returncode=1, stdout="stdout text", stderr="stderr text")

    failure = _format_compile_failure("ep_hal_types.h", result)

    assert "stdout text" in failure
    assert "stderr text" in failure


def test_hal_headers_compile_standalone(tmp_path):
    failures = []
    for header_name, body in HEADER_SNIPPETS.items():
        result = _compile_header_standalone(tmp_path, header_name, body)
        if result.returncode != 0:
            failures.append(_format_compile_failure(header_name, result))

    assert not failures, "\n".join(failures)
