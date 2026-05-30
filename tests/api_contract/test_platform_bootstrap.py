import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_platform_families_have_bootstrap_entries():
    rtos = (REPO_ROOT / "platforms/rtos/demo_family/startup/app_start.c").read_text()
    linux = (REPO_ROOT / "platforms/linux/demo_family/startup/main.c").read_text()
    host = (REPO_ROOT / "platforms/host/posix/startup/main.c").read_text()

    assert "ep_platform_boot" in rtos
    assert "ep_framework_start" in rtos
    assert "ep_platform_boot" in linux
    assert "ep_framework_start" in linux
    assert "ep_platform_boot" in host
    assert "ep_framework_start" in host


def test_platform_executables_link_framework_components():
    linux_cmake = (REPO_ROOT / "platforms/linux/demo_family/CMakeLists.txt").read_text()
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text()
    timer_cmake = (REPO_ROOT / "components/timer/CMakeLists.txt").read_text()

    assert "ep_components_timer" in host_cmake
    assert "ep_components_timer" in linux_cmake
    assert "ep_components_log" in host_cmake
    assert "ep_components_log" in linux_cmake
    assert "ep_components_event" in timer_cmake
    assert "PUBLIC" in timer_cmake


def test_platform_demo_targets_configure_and_build(tmp_path):
    build_dir = tmp_path / "platform-smoke"

    configure = subprocess.run(
        ["cmake", "-S", str(REPO_ROOT), "-B", str(build_dir)],
        capture_output=True,
        text=True,
    )
    assert configure.returncode == 0, (
        f"configure failed\nstdout:\n{configure.stdout}\nstderr:\n{configure.stderr}"
    )

    build = subprocess.run(
        [
            "cmake",
            "--build",
            str(build_dir),
            "--target",
            "ep_platform_rtos_demo",
            "ep_platform_linux_demo",
            "ep_platform_host_posix",
        ],
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (
        f"build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )
