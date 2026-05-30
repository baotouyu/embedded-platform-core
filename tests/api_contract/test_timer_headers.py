import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TIMER_INCLUDE = REPO_ROOT / "components" / "timer" / "include"
EVENT_INCLUDE = REPO_ROOT / "components" / "event" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_timer_header_does_not_include_platform_native_headers():
    header = TIMER_INCLUDE / "ep_timer.h"

    assert header.exists(), "Expected components/timer/include/ep_timer.h to exist"

    content = header.read_text(encoding="utf-8")
    forbidden = ["pthread.h", "rtthread.h", "unistd.h", "sys/", "platforms/"]
    found = [name for name in forbidden if name in content]

    assert not found, f"ep_timer.h must stay platform-neutral, found: {found}"


def test_timer_header_compiles_standalone(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    source = tmp_path / "timer_header_smoke.c"
    obj = tmp_path / "timer_header_smoke.o"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_timer.h"
            #include "ep_timer.h"

            int main(void)
            {
                ep_timer_id_t timer_id = 1;
                ep_event_id_t event_id = 10;
                int (*init_fn)(void) = ep_timer_init;
                int (*start_fn)(ep_timer_id_t, unsigned int, ep_event_id_t) = ep_timer_start;
                int (*stop_fn)(ep_timer_id_t) = ep_timer_stop;

                return (timer_id == 1 && event_id == 10 && init_fn && start_fn && stop_fn) ? 0 : 1;
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
            str(TIMER_INCLUDE),
            "-I",
            str(EVENT_INCLUDE),
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
