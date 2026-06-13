from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_app_ui_public_api_is_portable_and_platform_free():
    header = REPO_ROOT / "app/ui/app_ui.h"

    assert header.is_file()
    text = header.read_text(encoding="utf-8")

    assert "int app_ui_create(void);" in text
    forbidden = [
        "lvgl.h",
        "SDL",
        "rtthread",
        "aic",
        "artinchip",
        "ep_host_ui_port",
    ]
    for token in forbidden:
        assert token not in text


def test_app_ui_source_uses_common_lvgl_api_only():
    source = REPO_ROOT / "app/ui/app_ui.c"
    home_page = REPO_ROOT / "app/ui/pages/home_page.c"
    running_page = REPO_ROOT / "app/ui/pages/running_page.c"

    assert source.is_file()
    text = source.read_text(encoding="utf-8")
    home_text = home_page.read_text(encoding="utf-8")
    running_text = running_page.read_text(encoding="utf-8")

    assert '#include "app_ui.h"' in text
    assert '#include "ep_log.h"' in text
    assert '#include "page_manager.h"' in text
    assert '#include "pages/app_pages.h"' in text
    assert '#include "pages/home_page.h"' in text
    assert '#include "pages/running_page.h"' in text
    assert "page_manager_init(NULL)" in text
    assert "page_manager_register(APP_PAGE_HOME" in text
    assert "page_manager_register(APP_PAGE_RUNNING" in text
    assert "page_manager_switch(APP_PAGE_BOOT" in text
    assert 'EP_LOGI("app", "app ui ready")' in text
    assert "return rc;" in text

    assert '#include "lvgl.h"' in home_text
    assert "lv_obj_create(NULL)" in home_text
    assert "lv_label_create(" in home_text
    assert "lv_label_set_text(" in home_text
    assert "lv_obj_align(" in home_text or "lv_obj_set_pos(" in home_text

    forbidden = [
        "SDL2/SDL.h",
        "ep_host_ui_port.h",
        "rtthread.h",
        "aic",
        "artinchip",
        "drv_",
    ]
    for token in forbidden:
        assert token not in text
        assert token not in running_text


def test_app_cmake_builds_portable_ui_without_host_port_dependency():
    cmake = _read("app/CMakeLists.txt")

    assert "ui/app_ui.c" in cmake
    assert "ui/page_manager.c" in cmake
    assert "ui/pages/home_page.c" in cmake
    assert "ui/pages/running_page.c" in cmake
    assert "ui/pages/settings_page.c" in cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/ui" in cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/ui/pages" in cmake
    assert "${EP_LVGL_INCLUDE_DIR}" in cmake
    assert "EP_HAS_HOST_SDL2_UI" not in cmake
    assert "ep_host_ui_port" not in cmake


def test_static_export_targets_include_portable_ui_sources_and_headers():
    host_export = _read("cmake/modules/ep_export_targets.cmake")
    package_export = _read("tools/scripts/export_ep_package.sh")
    sdk_export = _read("tools/scripts/export_sdk_ep_package.sh")

    assert "${CMAKE_SOURCE_DIR}/app/ui/app_ui.c" in host_export
    assert "${CMAKE_SOURCE_DIR}/app/ui/page_manager.c" in host_export
    assert "${CMAKE_SOURCE_DIR}/app/ui/pages/home_page.c" in host_export
    assert "${CMAKE_SOURCE_DIR}/app/ui/pages/running_page.c" in host_export
    assert "${CMAKE_SOURCE_DIR}/app/ui/pages/settings_page.c" in host_export
    assert "${CMAKE_SOURCE_DIR}/app/ui" in host_export
    assert "${CMAKE_SOURCE_DIR}/app/ui/pages" in host_export
    assert "app/ui" in package_export
    assert "app/ui/app_ui.c" in sdk_export
    assert "app/ui/page_manager.c" in sdk_export
    assert "app/ui/pages/home_page.c" in sdk_export
    assert "app/ui/pages/running_page.c" in sdk_export
    assert "app/ui/pages/settings_page.c" in sdk_export
    assert "-I$REPO_ROOT/app/ui" in sdk_export
    assert "-I$REPO_ROOT/app/ui/pages" in sdk_export
    assert "packages/artinchip/lvgl-ui/lvgl_v9" in sdk_export
    assert "append_luban_lvgl_custom_include_flags" in sdk_export
    assert "AIC_LVGL_DEMO_HUB_DEMO:aic_demo/demo_hub" in sdk_export
    assert "components/ui/src/ep_ui.c" not in sdk_export
    assert "ep_thirdparty_lvgl" not in sdk_export
