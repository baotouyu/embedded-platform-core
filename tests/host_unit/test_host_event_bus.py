from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_event_component_is_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    event_cmake_path = REPO_ROOT / "components/event/CMakeLists.txt"
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "add_subdirectory(components/event)" in root_cmake
    assert event_cmake_path.exists()

    event_cmake = event_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_event STATIC" in event_cmake
    assert "src/ep_event.c" in event_cmake
    assert "components/event/include" not in event_cmake
    assert "ep_components_event" in host_cmake
