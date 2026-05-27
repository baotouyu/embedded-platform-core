import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OSAL_INCLUDE = REPO_ROOT / "osal" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")

HEADER_SNIPPETS = {
    "ep_osal_types.h": """
        ep_thread_t *thread = 0;
        ep_mutex_t *mutex = 0;
        ep_sem_t *sem = 0;
        ep_queue_t *queue = 0;
        return (thread == 0 && mutex == 0 && sem == 0 && queue == 0) ? 0 : 1;
    """,
    "ep_osal_err.h": """
        ep_err_e err = EP_OK;
        err = EP_ERR_INVAL;
        err = EP_ERR_TIMEOUT;
        err = EP_ERR_BUSY;
        err = EP_ERR_UNSUPPORTED;
        return err == EP_ERR_UNSUPPORTED ? 0 : 1;
    """,
    "ep_osal_thread.h": """
        ep_thread_t *thread = 0;
        ep_thread_entry_t entry = 0;
        int (*create_fn)(ep_thread_t **, const char *, ep_thread_entry_t, void *) = ep_thread_create;
        int (*join_fn)(ep_thread_t *) = ep_thread_join;
        return (thread == 0 && entry == 0 && create_fn && join_fn) ? 0 : 1;
    """,
    "ep_osal_mutex.h": """
        ep_mutex_t *mutex = 0;
        int (*create_fn)(ep_mutex_t **) = ep_mutex_create;
        int (*lock_fn)(ep_mutex_t *) = ep_mutex_lock;
        int (*unlock_fn)(ep_mutex_t *) = ep_mutex_unlock;
        return (mutex == 0 && create_fn && lock_fn && unlock_fn) ? 0 : 1;
    """,
    "ep_osal_sem.h": """
        ep_sem_t *sem = 0;
        int (*create_fn)(ep_sem_t **, unsigned int) = ep_sem_create;
        int (*wait_fn)(ep_sem_t *, unsigned int) = ep_sem_wait;
        int (*post_fn)(ep_sem_t *) = ep_sem_post;
        return (sem == 0 && create_fn && wait_fn && post_fn) ? 0 : 1;
    """,
    "ep_osal_queue.h": """
        ep_queue_t *queue = 0;
        int (*create_fn)(ep_queue_t **, size_t, size_t) = ep_queue_create;
        int (*send_fn)(ep_queue_t *, const void *, unsigned int) = ep_queue_send;
        int (*recv_fn)(ep_queue_t *, void *, unsigned int) = ep_queue_recv;
        return (queue == 0 && create_fn && send_fn && recv_fn) ? 0 : 1;
    """,
    "ep_osal_time.h": """
        uint64_t (*now_fn)(void) = ep_time_now_ms;
        void (*sleep_fn)(unsigned int) = ep_sleep_ms;
        return (now_fn && sleep_fn) ? 0 : 1;
    """,
    "ep_osal_mem.h": """
        void *(*malloc_fn)(size_t) = ep_malloc;
        void (*free_fn)(void *) = ep_free;
        return (malloc_fn && free_fn) ? 0 : 1;
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
        [COMPILER, "-std=c11", "-Wall", "-Wextra", "-I", str(OSAL_INCLUDE), "-c", str(source), "-o", str(obj)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )


def test_osal_headers_compile_standalone(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    failures = []
    for header_name, body in HEADER_SNIPPETS.items():
        result = _compile_header_standalone(tmp_path, header_name, body)
        if result.returncode != 0:
            failures.append(f"{header_name}: {result.stderr}")

    assert not failures, "\n".join(failures)
