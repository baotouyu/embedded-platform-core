import subprocess
from pathlib import Path


def test_framework_bootstrap_symbols_exist():
    header = Path("core/include/ep_framework.h").read_text()
    app_header = Path("app/include/app_main.h").read_text()
    source = Path("core/src/ep_framework.c").read_text()
    cmake = Path("core/CMakeLists.txt").read_text()
    assert "int ep_platform_boot(void);" in header
    assert "int ep_framework_init(void);" in header
    assert "int ep_framework_start(void);" in header
    assert "int app_main(void);" in app_header
    assert "int ep_framework_init(void)" in source
    assert "int ep_framework_start(void)" in source
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in cmake
    assert "PUBLIC\n    ${CMAKE_CURRENT_SOURCE_DIR}/include" in cmake
    assert "PRIVATE\n    ${CMAKE_SOURCE_DIR}/app/include" in cmake
    assert "PUBLIC\n    ${CMAKE_SOURCE_DIR}/app/include" not in cmake
    assert '#include "ep_event.h"' in source
    assert '#include "ep_timer.h"' in source
    assert "int rc = ep_event_init();" in source
    assert "return ep_event_init();" not in source
    assert "return ep_timer_init();" in source
    assert source.index("ep_event_init()") < source.index("ep_timer_init()")
    assert "${CMAKE_SOURCE_DIR}/components/event/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/timer/include" in cmake


def test_framework_bootstrap_cmake_smoke(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    build_dir = tmp_path / "build"

    configure = subprocess.run(
        ["cmake", "-S", str(repo_root), "-B", str(build_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert configure.returncode == 0, (
        f"cmake configure failed\nstdout:\n{configure.stdout}\nstderr:\n{configure.stderr}"
    )

    build = subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "ep_core", "ep_app"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, (
        f"cmake build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )
