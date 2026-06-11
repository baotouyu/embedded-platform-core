from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_ui_style_component_uses_tiny_ttf_font_resource():
    header = REPO_ROOT / "components/ui_style/include/ui_style.h"
    source = REPO_ROOT / "components/ui_style/src/ui_style.c"
    cmake = REPO_ROOT / "components/ui_style/CMakeLists.txt"
    font = REPO_ROOT / "resources/host/fonts/SourceHan-Regular_arial_cn.ttf"

    assert header.is_file()
    assert source.is_file()
    assert cmake.is_file()
    assert font.is_file()

    header_text = header.read_text(encoding="utf-8")
    source_text = source.read_text(encoding="utf-8")
    cmake_text = cmake.read_text(encoding="utf-8")
    root_cmake = _read("CMakeLists.txt")
    host_cmake = _read("platforms/host/posix/CMakeLists.txt")
    export_cmake = _read("cmake/modules/ep_export_targets.cmake")

    assert "UI_STYLE_FONT_HOME_SIDE" in header_text
    assert "UI_STYLE_FONT_HOME_CENTER" in header_text
    assert "int ui_style_init(void);" in header_text
    assert "const lv_font_t *ui_style_font(ui_style_font_id_t font_id);" in header_text

    assert 'UI_STYLE_FONT_FILE_NAME "SourceHan-Regular_arial_cn.ttf"' in source_text
    assert '#include "src/libs/tiny_ttf/lv_tiny_ttf.h"' in source_text
    assert "ep_platform_font_path(UI_STYLE_FONT_FILE_NAME" in source_text
    assert "lv_tiny_ttf_init()" in source_text
    assert "lv_tiny_ttf_create_file_ex(" in source_text
    assert "lv_tiny_ttf_destroy(" in source_text
    assert "LV_FONT_DEFAULT" in source_text

    assert "add_library(ep_components_ui_style STATIC" in cmake_text
    assert "ep_platform_api" in cmake_text
    assert "ep_thirdparty_lvgl" in cmake_text
    assert "add_subdirectory(components/ui_style)" in root_cmake
    assert "ep_components_ui_style" in host_cmake
    assert "components/ui_style/src/ui_style.c" in export_cmake
    assert "components/ui_style/include" in export_cmake


def test_home_page_applies_ui_style_fonts_to_chinese_labels():
    home_page = _read("app/ui/pages/home_page.c")
    app_cmake = _read("app/CMakeLists.txt")

    assert '#include "ui_style.h"' in home_page
    assert "ui_style_init()" in home_page
    assert "ui_style_font(UI_STYLE_FONT_HOME_SIDE)" in home_page
    assert "ui_style_font(UI_STYLE_FONT_HOME_CENTER)" in home_page
    assert "ui_style_font(UI_STYLE_FONT_HOME_USER)" in home_page
    assert "lv_obj_set_style_text_font(slot->label" in home_page
    assert "lv_obj_set_style_text_font(label" in home_page
    assert "ep_components_ui_style" in app_cmake
