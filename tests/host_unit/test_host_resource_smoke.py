import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_host_resource_smoke_files_and_cmake_are_declared():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )
    source = REPO_ROOT / "platforms/host/posix/demos/resource_smoke_main.c"

    assert source.is_file()
    content = source.read_text(encoding="utf-8")
    assert "ep_platform_image_path" in content
    assert "ep_platform_font_path" in content
    assert "ep_platform_theme_path" in content
    assert "ep_file_open" in content
    assert "ep_file_read" in content

    assert "add_executable(ep_host_resource_smoke" in cmake
    assert "demos/resource_smoke_main.c" in cmake
    assert "paths/ep_host_platform_paths.c" in cmake
    assert "ep_components_file" in cmake
    assert "ep_platform_api" in cmake


def test_host_resource_smoke_assets_exist_and_are_not_empty():
    for relative_path in [
        "resources/host/images/smoke.txt",
        "resources/host/fonts/smoke.txt",
        "resources/host/themes/smoke.txt",
    ]:
        resource = REPO_ROOT / relative_path
        assert resource.is_file()
        assert resource.read_text(encoding="utf-8").strip()


def test_host_resource_smoke_builds_and_runs():
    build_dir = REPO_ROOT / "build"

    configure_result = subprocess.run(
        ["cmake", "-S", ".", "-B", str(build_dir)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert configure_result.returncode == 0, (
        f"stdout:\n{configure_result.stdout}\nstderr:\n{configure_result.stderr}"
    )

    build_result = subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "ep_host_resource_smoke"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert build_result.returncode == 0, (
        f"stdout:\n{build_result.stdout}\nstderr:\n{build_result.stderr}"
    )

    executable = build_dir / "platforms/host/posix/ep_host_resource_smoke"
    run_result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert run_result.returncode == 0, (
        f"stdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
