from pathlib import Path


def test_osal_headers_use_ep_prefix():
    root = Path("osal/include")
    headers = [
        "ep_osal_types.h",
        "ep_osal_err.h",
        "ep_osal_thread.h",
        "ep_osal_mutex.h",
        "ep_osal_sem.h",
        "ep_osal_queue.h",
        "ep_osal_time.h",
        "ep_osal_mem.h",
    ]
    for name in headers:
        text = (root / name).read_text()
        assert "ep_" in text
