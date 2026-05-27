import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OSAL_INCLUDE = REPO_ROOT / "osal" / "include"
HEADERS = {
    "ep_osal_types.h": [
        "ep_thread_t",
        "ep_mutex_t",
        "ep_sem_t",
        "ep_queue_t",
    ],
    "ep_osal_err.h": [
        "ep_err_e",
        "EP_OK",
        "EP_ERR_INVAL",
        "EP_ERR_TIMEOUT",
        "EP_ERR_BUSY",
        "EP_ERR_UNSUPPORTED",
    ],
    "ep_osal_thread.h": [
        "ep_thread_entry_t",
        "ep_thread_create",
        "ep_thread_join",
    ],
    "ep_osal_mutex.h": [
        "ep_mutex_create",
        "ep_mutex_lock",
        "ep_mutex_unlock",
    ],
    "ep_osal_sem.h": [
        "ep_sem_create",
        "ep_sem_wait",
        "ep_sem_post",
    ],
    "ep_osal_queue.h": [
        "ep_queue_create",
        "ep_queue_send",
        "ep_queue_recv",
    ],
    "ep_osal_time.h": [
        "ep_time_now_ms",
        "ep_sleep_ms",
    ],
    "ep_osal_mem.h": [
        "ep_malloc",
        "ep_free",
    ],
}


def test_osal_headers_use_ep_prefix():
    for name, required_symbols in HEADERS.items():
        header = OSAL_INCLUDE / name
        text = header.read_text()
        assert "ep_" in text
        for symbol in required_symbols:
            assert symbol in text


def test_osal_headers_are_readable_from_repo_root():
    assert OSAL_INCLUDE.is_dir()
    for name in HEADERS:
        header = OSAL_INCLUDE / name
        assert header.is_file()
        assert header.read_text()


def test_osal_public_headers_compile_together(tmp_path):
    compiler = shutil.which("clang") or shutil.which("cc")
    assert compiler, "Expected clang or cc to be available for compile smoke test"

    source = tmp_path / "osal_smoke.c"
    obj = tmp_path / "osal_smoke.o"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_types.h"
            #include "ep_osal_err.h"
            #include "ep_osal_thread.h"
            #include "ep_osal_mutex.h"
            #include "ep_osal_sem.h"
            #include "ep_osal_queue.h"
            #include "ep_osal_time.h"
            #include "ep_osal_mem.h"

            int main(void) {
                return 0;
            }
            """
        ).strip()
        + "\n"
    )

    result = subprocess.run(
        [compiler, "-std=c11", "-Wall", "-Wextra", "-I", str(OSAL_INCLUDE), "-c", str(source), "-o", str(obj)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
