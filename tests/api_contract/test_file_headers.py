import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FILE_INCLUDE = REPO_ROOT / "components" / "file" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_file_header_is_platform_neutral():
    header = FILE_INCLUDE / "ep_file.h"

    assert header.exists(), "Expected components/file/include/ep_file.h to exist"

    content = header.read_text(encoding="utf-8")
    forbidden = [
        "FILE *",
        "FILE*",
        "typedef FILE",
        "stdio.h",
        "pthread.h",
        "rtthread.h",
        "unistd.h",
        "fcntl.h",
        "sys/",
        "platforms/",
        "third_party/",
        "flash",
    ]
    found = [name for name in forbidden if name in content]

    assert not found, f"ep_file.h must stay platform-neutral, found: {found}"


def test_file_header_compiles_standalone(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    source = tmp_path / "file_header_smoke.c"
    obj = tmp_path / "file_header_smoke.o"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_file.h"
            #include "ep_file.h"

            int main(void)
            {
                ep_file_t *file = 0;
                int mode = EP_FILE_MODE_READ | EP_FILE_MODE_WRITE |
                           EP_FILE_MODE_CREATE | EP_FILE_MODE_TRUNCATE |
                           EP_FILE_MODE_APPEND;
                int (*open_fn)(ep_file_t **, const char *, int) = ep_file_open;
                int (*read_fn)(ep_file_t *, void *, size_t, size_t *) = ep_file_read;
                int (*write_fn)(ep_file_t *, const void *, size_t, size_t *) = ep_file_write;
                int (*close_fn)(ep_file_t *) = ep_file_close;

                return (file == 0 && mode != 0 && open_fn && read_fn && write_fn && close_fn) ? 0 : 1;
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
            str(FILE_INCLUDE),
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
