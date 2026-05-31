import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_INCLUDE = REPO_ROOT / "components" / "log" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_log_header_does_not_expose_easylogger_or_platform_headers():
    header = LOG_INCLUDE / "ep_log.h"

    assert header.exists(), "Expected components/log/include/ep_log.h to exist"

    content = header.read_text(encoding="utf-8")
    forbidden = [
        "elog.h",
        "pthread.h",
        "rtthread.h",
        "unistd.h",
        "sys/",
        "platforms/",
        "third_party/",
    ]
    found = [name for name in forbidden if name in content]

    assert not found, f"ep_log.h must hide EasyLogger and stay platform-neutral, found: {found}"


def test_log_header_compiles_standalone(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    source = tmp_path / "log_header_smoke.c"
    obj = tmp_path / "log_header_smoke.o"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_log.h"
            #include "ep_log.h"

            int main(void)
            {
                ep_log_level_e level = EP_LOG_LEVEL_INFO;
                int (*init_fn)(void) = ep_log_init;
                int (*set_level_fn)(ep_log_level_e) = ep_log_set_level;
                ep_log_level_e (*get_level_fn)(void) = ep_log_get_level;
                int (*write_fn)(ep_log_level_e, const char *, const char *, ...) = ep_log_write;

                if (EP_LOG_LEVEL_ASSERT != 0) {
                    return 1;
                }

                EP_LOGE("contract", "error %d", 1);
                EP_LOGW("contract", "warn %d", 2);
                EP_LOGI("contract", "info %d", 3);
                EP_LOGD("contract", "debug %d", 4);
                EP_LOGV("contract", "verbose %d", 5);

                return (level == EP_LOG_LEVEL_INFO &&
                        init_fn &&
                        set_level_fn &&
                        get_level_fn &&
                        write_fn) ? 0 : 2;
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
            str(LOG_INCLUDE),
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
