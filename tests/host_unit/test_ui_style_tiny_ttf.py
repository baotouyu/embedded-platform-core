import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_ui_style_component_uses_static_font_assets():
    header = REPO_ROOT / "components/ui_style/include/ui_style.h"
    source = REPO_ROOT / "components/ui_style/src/ui_style.c"
    cmake = REPO_ROOT / "components/ui_style/CMakeLists.txt"
    font = REPO_ROOT / "resources/host/fonts/SourceHan-Regular_arial_cn.ttf"
    generated_fonts = [
        REPO_ROOT / "components/ui_style/src/ui_font_source_han_24.c",
        REPO_ROOT / "components/ui_style/src/ui_font_source_han_28.c",
        REPO_ROOT / "components/ui_style/src/ui_font_source_han_40.c",
    ]

    assert header.is_file()
    assert source.is_file()
    assert cmake.is_file()
    assert font.is_file()
    for generated_font in generated_fonts:
        assert generated_font.is_file()

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

    assert "LV_FONT_DECLARE(ui_font_source_han_24)" in source_text
    assert "LV_FONT_DECLARE(ui_font_source_han_28)" in source_text
    assert "LV_FONT_DECLARE(ui_font_source_han_40)" in source_text
    assert "ui_font_source_han_24" in source_text
    assert "ui_font_source_han_28" in source_text
    assert "ui_font_source_han_40" in source_text
    assert "LV_FONT_DEFAULT" in source_text
    assert "#if LV_USE_FREETYPE" in source_text
    assert '#include "src/libs/freetype/lv_freetype.h"' in source_text
    assert 'UI_STYLE_FONT_FILE_NAME "SourceHan-Regular_arial_cn.ttf"' in source_text
    assert "ep_platform_font_path(UI_STYLE_FONT_FILE_NAME" in source_text
    assert "lv_freetype_font_create(" in source_text
    assert "lv_freetype_font_delete(" in source_text
    assert "tiny_ttf" not in source_text.lower()
    assert "lv_tiny_ttf_create_file_ex" not in source_text

    assert "add_library(ep_components_ui_style STATIC" in cmake_text
    assert "src/ui_font_source_han_24.c" in cmake_text
    assert "src/ui_font_source_han_28.c" in cmake_text
    assert "src/ui_font_source_han_40.c" in cmake_text
    assert "ep_thirdparty_lvgl" in cmake_text
    assert "add_subdirectory(components/ui_style)" in root_cmake
    assert "ep_components_ui_style" in host_cmake
    assert "components/ui_style/src/ui_style.c" in export_cmake
    assert "components/ui_style/src/ui_font_source_han_24.c" in export_cmake
    assert "components/ui_style/src/ui_font_source_han_28.c" in export_cmake
    assert "components/ui_style/src/ui_font_source_han_40.c" in export_cmake
    assert "components/ui_style/include" in export_cmake

    for generated_font in generated_fonts:
        generated_text = generated_font.read_text(encoding="utf-8")
        assert f"const lv_font_t {generated_font.stem}" in generated_text


def test_ui_style_font_generator_keeps_static_fonts_reproducible():
    generator = REPO_ROOT / "tools/scripts/generate_ui_fonts.py"
    source_font = REPO_ROOT / "resources/host/fonts/SourceHan-Regular_arial_cn.ttf"
    recipe_db = REPO_ROOT / "resources/host/recipe/recipelib.db"

    assert generator.is_file()
    assert source_font.is_file()
    assert recipe_db.is_file()

    generator_text = generator.read_text(encoding="utf-8")

    assert "SourceHan-Regular_arial_cn.ttf" in generator_text
    assert "recipelib.db" in generator_text
    assert "simplerecipeEntity" in generator_text
    assert "lv_font_conv" in generator_text
    assert "用户1234" in generator_text
    assert "设置语言亮度清洗关联开休眠详细信息" in generator_text
    assert "24" in generator_text
    assert "28" in generator_text
    assert "40" in generator_text


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


def test_ui_style_loads_fonts_without_tiny_ttf_runtime(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "ui_style_font_smoke.c"
    executable = tmp_path / "ui_style_font_smoke"

    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_ui.h"
            #include "ui_style.h"

            #include "lvgl.h"

            int main(void)
            {
                if (ep_ui_init() != EP_OK) {
                    return 1;
                }

                if (ui_style_init() != EP_OK) {
                    return 2;
                }

                if (ui_style_font(UI_STYLE_FONT_HOME_USER) == LV_FONT_DEFAULT) {
                    return 3;
                }

                if (lv_font_get_glyph_width(ui_style_font(UI_STYLE_FONT_HOME_USER), 0x7528, 0x6237) <= 0) {
                    return 4;
                }

                if (lv_font_get_glyph_width(ui_style_font(UI_STYLE_FONT_HOME_USER), 0x6237, 0) <= 0) {
                    return 5;
                }

                ui_style_deinit();
                (void)ep_ui_deinit();
                return 0;
            }
            """
        ).strip()
        + "\n"
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(REPO_ROOT / "components/ui/include"),
            "-I",
            str(REPO_ROOT / "components/ui_style/include"),
            "-I",
            str(REPO_ROOT / "platforms/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            "-I",
            str(REPO_ROOT / "third_party/prebuilt/lvgl/host_macos/include"),
            str(source),
            str(REPO_ROOT / "components/ui/src/ep_ui.c"),
            str(REPO_ROOT / "components/ui_style/src/ui_style.c"),
            str(REPO_ROOT / "platforms/host/posix/paths/ep_host_platform_paths.c"),
            str(REPO_ROOT / "components/ui_style/src/ui_font_source_han_24.c"),
            str(REPO_ROOT / "components/ui_style/src/ui_font_source_han_28.c"),
            str(REPO_ROOT / "components/ui_style/src/ui_font_source_han_40.c"),
            str(REPO_ROOT / "third_party/prebuilt/lvgl/host_macos/lib/liblvgl.a"),
            "-L/opt/homebrew/opt/freetype/lib",
            "-lfreetype",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert compile_result.returncode == 0, (
        f"stdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
    )

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
