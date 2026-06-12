import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_multi_lang_component_uses_neutral_names():
    old_header = REPO_ROOT / "ki_multi_lang.h"
    old_source = REPO_ROOT / "ki_multi_lang.c"
    root_header = REPO_ROOT / "multi_lang.h"
    root_source = REPO_ROOT / "multi_lang.c"
    component = REPO_ROOT / "components" / "multi_lang"
    header = component / "include" / "multi_lang.h"
    source = component / "src" / "multi_lang.c"
    cmake = component / "CMakeLists.txt"

    assert not old_header.exists()
    assert not old_source.exists()
    assert not root_header.exists()
    assert not root_source.exists()
    assert header.is_file()
    assert source.is_file()
    assert cmake.is_file()

    header_text = header.read_text(encoding="utf-8")
    source_text = source.read_text(encoding="utf-8")
    cmake_text = cmake.read_text(encoding="utf-8")

    assert "MULTI_LANG_H" in header_text
    assert "MULTI_LANG_DEFAULT" in header_text
    assert "MULTI_LANG_KEY_CANCEL" in header_text
    assert "MULTI_LANG_KEY_WIFI" in header_text
    assert "MULTI_LANG_KEY_BRIGHTNESS" in header_text
    assert "MULTI_LANG_KEY_APP_LINK" in header_text
    assert "MULTI_LANG_KEY_SLEEP" in header_text
    assert "MULTI_LANG_KEY_ON" in header_text
    assert "MULTI_LANG_KEY_DETAILS" in header_text
    assert "typedef struct multi_lang_store multi_lang_store_t;" in header_text
    assert "multi_lang_open_db" in header_text
    assert "multi_lang_close" in header_text
    assert "multi_lang_set_language" in header_text
    assert "multi_lang_get_text" in header_text
    assert '#include "multi_lang.h"' in source_text
    assert "multi_lang_builtin_fallbacks[]" in source_text
    assert "multi_lang_get_builtin_text" in source_text
    assert '{"zh-CN", MULTI_LANG_KEY_SETTING' in source_text
    assert '{"zh-CN", MULTI_LANG_KEY_BRIGHTNESS' in source_text
    assert '{"zh-CN", MULTI_LANG_KEY_APP_LINK' in source_text
    assert "resources/host/recipe/recipelib.db" not in source_text
    assert "add_library(ep_components_multi_lang STATIC" in cmake_text
    assert "ep_thirdparty_cjson" in cmake_text
    assert "ep_thirdparty_sqlite" in cmake_text
    assert "ep_thirdparty_lvgl" not in cmake_text

    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "add_subdirectory(components/multi_lang)" in root_cmake

    forbidden_tokens = [
        "ki_multi_lang",
        "KI_MUTI_LANG",
        "KI_MULTI_LANG",
        "KI_LANG_",
        "ki_muti_lang",
    ]
    for token in forbidden_tokens:
        assert token not in header_text
        assert token not in source_text

    forbidden_public_deps = [
        "lvgl.h",
        "sqlite3.h",
        "cJSON.h",
    ]
    for token in forbidden_public_deps:
        assert token not in header_text


def test_multi_lang_loads_interface_translations_from_recipelib(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    source = tmp_path / "multi_lang_smoke.c"
    binary = tmp_path / "multi_lang_smoke"
    db_path = REPO_ROOT / "resources" / "host" / "recipe" / "recipelib.db"
    source.write_text(
        textwrap.dedent(
            f"""
            #include "multi_lang.h"
            #include "ep_osal_err.h"

            #include <string.h>

            int main(void)
            {{
                multi_lang_store_t *store = 0;
                const char *text = 0;

                if (multi_lang_open_db("{db_path.as_posix()}", &store) != EP_OK) {{
                    return 1;
                }}

                if (multi_lang_set_language(store, "en") != EP_OK) {{
                    multi_lang_close(store);
                    return 2;
                }}

                if (multi_lang_get_text(store, MULTI_LANG_KEY_CANCEL, &text) != EP_OK) {{
                    multi_lang_close(store);
                    return 3;
                }}

                if (strcmp(text, "Cancel") != 0) {{
                    multi_lang_close(store);
                    return 4;
                }}

                if (multi_lang_get_text(store, "missing_test_key", &text) == EP_OK) {{
                    multi_lang_close(store);
                    return 5;
                }}

                if (strcmp(text, "missing_test_key") != 0) {{
                    multi_lang_close(store);
                    return 6;
                }}

                if (multi_lang_get_text(store, MULTI_LANG_KEY_BRIGHTNESS, &text) != EP_OK) {{
                    multi_lang_close(store);
                    return 7;
                }}

                if (strcmp(text, "Brightness") != 0) {{
                    multi_lang_close(store);
                    return 8;
                }}

                multi_lang_close(store);
                return 0;
            }}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(REPO_ROOT / "components" / "multi_lang" / "include"),
            "-I",
            str(REPO_ROOT / "components" / "log" / "include"),
            "-I",
            str(REPO_ROOT / "osal" / "include"),
            "-I",
            str(REPO_ROOT / "third_party" / "external" / "cjson"),
            "-I",
            str(REPO_ROOT / "third_party" / "external" / "sqlite"),
            str(source),
            str(REPO_ROOT / "components" / "multi_lang" / "src" / "multi_lang.c"),
            str(REPO_ROOT / "third_party" / "external" / "cjson" / "cJSON.c"),
            str(REPO_ROOT / "third_party" / "external" / "sqlite" / "sqlite3.c"),
            "-o",
            str(binary),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    result = subprocess.run(
        [str(binary)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr
