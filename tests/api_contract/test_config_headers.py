import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_INCLUDE = REPO_ROOT / "components" / "config" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_config_header_is_platform_neutral():
    header = CONFIG_INCLUDE / "ep_config.h"

    assert header.exists(), "Expected components/config/include/ep_config.h to exist"

    content = header.read_text(encoding="utf-8")
    forbidden = [
        "pthread.h",
        "rtthread.h",
        "unistd.h",
        "sys/",
        "platforms/",
        "third_party/",
        "elog.h",
        "EasyLogger",
        "ep_file",
        "flash",
    ]
    found = [name for name in forbidden if name in content]

    assert not found, f"ep_config.h must stay platform-neutral, found: {found}"


def test_config_header_compiles_standalone(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    source = tmp_path / "config_header_smoke.c"
    obj = tmp_path / "config_header_smoke.o"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_config.h"
            #include "ep_config.h"

            int main(void)
            {
                int (*init_fn)(void) = ep_config_init;
                int (*set_int_fn)(const char *, int) = ep_config_set_int;
                int (*get_int_fn)(const char *, int) = ep_config_get_int;
                int (*set_bool_fn)(const char *, int) = ep_config_set_bool;
                int (*get_bool_fn)(const char *, int) = ep_config_get_bool;
                int (*set_string_fn)(const char *, const char *) = ep_config_set_string;
                const char *(*get_string_fn)(const char *, const char *) = ep_config_get_string;

                return (init_fn && set_int_fn && get_int_fn && set_bool_fn &&
                        get_bool_fn && set_string_fn && get_string_fn) ? 0 : 1;
            }
            """
        ).strip()
        + "\n"
    )

    result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(CONFIG_INCLUDE),
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

    assert result.returncode == 0, result.stderr
