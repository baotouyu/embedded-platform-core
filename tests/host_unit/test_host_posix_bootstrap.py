import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_host_posix_package_shape_exists():
    expected_paths = [
        "platforms/host/common",
        "platforms/host/posix/CMakeLists.txt",
        "platforms/host/posix/startup/main.c",
        "platforms/host/posix/osal_port/ep_host_osal_stub.c",
        "platforms/host/posix/hal_port/ep_host_hal_stub.c",
        "platforms/host/posix/component_port/ep_host_component_stub.c",
        "platforms/host/posix/config/host_posix.cmake",
    ]

    missing = [path for path in expected_paths if not (REPO_ROOT / path).exists()]
    assert not missing, f"Missing host POSIX paths: {missing}"


def test_host_posix_cmake_target_is_named():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "add_executable(ep_platform_host_posix" in cmake
    assert "target_link_libraries(ep_platform_host_posix" in cmake
    assert "ep_core" in cmake
    assert "ep_app" in cmake


def test_host_posix_executable_runs_successfully(tmp_path):
    build_dir = tmp_path / "host-posix-build"

    configure = subprocess.run(
        ["cmake", "-S", str(REPO_ROOT), "-B", str(build_dir)],
        capture_output=True,
        text=True,
    )
    assert configure.returncode == 0, (
        f"configure failed\nstdout:\n{configure.stdout}\nstderr:\n{configure.stderr}"
    )

    build = subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "ep_platform_host_posix"],
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (
        f"build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )

    executable = build_dir / "platforms/host/posix/ep_platform_host_posix"
    run = subprocess.run([str(executable)], capture_output=True, text=True)
    assert run.returncode == 0, (
        f"host executable failed\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
    )
