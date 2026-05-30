import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EVENT_INCLUDE = REPO_ROOT / "components" / "event" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_event_header_does_not_include_platform_native_headers():
    header = EVENT_INCLUDE / "ep_event.h"

    assert header.exists(), "Expected components/event/include/ep_event.h to exist"

    content = header.read_text(encoding="utf-8")
    forbidden = ["pthread.h", "rtthread.h", "unistd.h", "sys/", "platforms/"]
    found = [name for name in forbidden if name in content]

    assert not found, f"ep_event.h must stay platform-neutral, found: {found}"


def test_event_header_compiles_standalone(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    source = tmp_path / "event_header_smoke.c"
    obj = tmp_path / "event_header_smoke.o"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_event.h"

            static void handler(
                ep_event_id_t event_id,
                const void *payload,
                size_t payload_size,
                void *user_data
            )
            {
                (void)event_id;
                (void)payload;
                (void)payload_size;
                (void)user_data;
            }

            int main(void)
            {
                ep_event_id_t event_id = 1;
                ep_event_handler_t handler_fn = handler;
                int (*init_fn)(void) = ep_event_init;
                int (*subscribe_fn)(ep_event_id_t, ep_event_handler_t, void *) = ep_event_subscribe;
                int (*publish_fn)(ep_event_id_t, const void *, size_t, unsigned int) = ep_event_publish;

                return (event_id == 1 && handler_fn && init_fn && subscribe_fn && publish_fn) ? 0 : 1;
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
