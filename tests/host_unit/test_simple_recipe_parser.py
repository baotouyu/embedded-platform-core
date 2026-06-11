import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_simple_recipe_component_is_declared():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    component_cmake = REPO_ROOT / "components/recipe_parser/CMakeLists.txt"
    header = REPO_ROOT / "components/recipe_parser/include/ep_simple_recipe.h"
    source = REPO_ROOT / "components/recipe_parser/src/ep_simple_recipe.c"

    assert component_cmake.is_file()
    assert header.is_file()
    assert source.is_file()
    assert "add_subdirectory(components/recipe_parser)" in root_cmake
    assert "ep_components_recipe_parser" in component_cmake.read_text(encoding="utf-8")


def test_simple_recipe_parser_reads_saas2_simple_recipe_table(tmp_path):
    smoke_dir = REPO_ROOT / "build/simple_recipe_smoke"
    source = smoke_dir / "simple_recipe_smoke.c"
    build_dir = smoke_dir / "build"
    db_path = REPO_ROOT / "resources/host/recipe/recipelib.db"

    smoke_dir.mkdir(parents=True, exist_ok=True)

    source.write_text(
        textwrap.dedent(
            f"""
            #include "ep_osal_err.h"
            #include "ep_simple_recipe.h"

            #include <stddef.h>
            #include <string.h>

            static int find_param(
                const ep_simple_recipe_detail_t *detail,
                const char *key,
                ep_simple_recipe_param_t *out_param)
            {{
                size_t i;
                size_t j;

                for (i = 0u; i < detail->step_count; ++i) {{
                    for (j = 0u; j < detail->steps[i].param_count; ++j) {{
                        if (strcmp(detail->steps[i].params[j].key, key) == 0) {{
                            *out_param = detail->steps[i].params[j];
                            return 1;
                        }}
                    }}
                }}

                return 0;
            }}

            int main(void)
            {{
                ep_simple_recipe_store_t *store = 0;
                ep_simple_recipe_item_t items[16];
                ep_simple_recipe_detail_t detail;
                ep_simple_recipe_param_t param;
                size_t count = 0u;
                size_t loaded = 0u;
                int rc;

                rc = ep_simple_recipe_open_saas2_db("{db_path.as_posix()}", &store);
                if (rc != EP_OK || store == 0) {{
                    return 1;
                }}

                rc = ep_simple_recipe_count(store, &count);
                if (rc != EP_OK || count != 11u) {{
                    ep_simple_recipe_close(store);
                    return 2;
                }}

                rc = ep_simple_recipe_load_list(store, items, 16u, &loaded);
                if (rc != EP_OK || loaded != 11u) {{
                    ep_simple_recipe_close(store);
                    return 3;
                }}

                if (strcmp(items[0].id, "2061686127474393090") != 0 ||
                    strcmp(items[0].name, "Double Espresso") != 0 ||
                    strcmp(items[0].portrait_image_url, "https://file.kitchenidea.com.cn/cook_platform/images/2c5e9fef-51ff-4c45-b847-0fc59de4a590.png") != 0 ||
                    strcmp(items[0].landscape_image_url, "https://file.kitchenidea.com.cn/cook_platform/images/3a921f1b-1ce0-4a33-bc3e-c0ceff3ee3c5.png") != 0) {{
                    ep_simple_recipe_close(store);
                    return 4;
                }}

                rc = ep_simple_recipe_load_detail(store, "2061685591744331777", &detail);
                if (rc != EP_OK) {{
                    ep_simple_recipe_close(store);
                    return 5;
                }}

                if (detail.step_count != 1u ||
                    detail.steps[0].param_count != 9u) {{
                    ep_simple_recipe_close(store);
                    return 6;
                }}

                if (!find_param(&detail, "discharge", &param) ||
                    strcmp(param.ctl_val, "60") != 0 ||
                    strcmp(param.min_val, "25") != 0 ||
                    strcmp(param.max_val, "250") != 0) {{
                    ep_simple_recipe_close(store);
                    return 7;
                }}

                if (!find_param(&detail, "temperature", &param) ||
                    strcmp(param.ctl_val, "92") != 0 ||
                    strcmp(param.min_val, "86") != 0 ||
                    strcmp(param.max_val, "95") != 0) {{
                    ep_simple_recipe_close(store);
                    return 8;
                }}

                ep_simple_recipe_close(store);
                return 0;
            }}
            """
        ).strip()
        + "\n"
    )

    cmake_file = smoke_dir / "CMakeLists.txt"
    cmake_file.write_text(
        textwrap.dedent(
            f"""
            cmake_minimum_required(VERSION 3.20)
            project(simple_recipe_smoke C)

            add_subdirectory({(REPO_ROOT / "third_party").as_posix()} third_party)
            add_subdirectory({(REPO_ROOT / "components/recipe_parser").as_posix()} recipe_parser)

            add_executable(simple_recipe_smoke {source.as_posix()})
            target_include_directories(simple_recipe_smoke
              PRIVATE
                {(REPO_ROOT / "osal/include").as_posix()}
            )
            target_link_libraries(simple_recipe_smoke
              PRIVATE
                ep_components_recipe_parser
            )
            """
        ).strip()
        + "\n"
    )

    configure_result = subprocess.run(
        ["cmake", "-S", str(smoke_dir), "-B", str(build_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert configure_result.returncode == 0, (
        f"stdout:\n{configure_result.stdout}\nstderr:\n{configure_result.stderr}"
    )

    build_result = subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "simple_recipe_smoke"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build_result.returncode == 0, (
        f"stdout:\n{build_result.stdout}\nstderr:\n{build_result.stderr}"
    )

    run_result = subprocess.run(
        [str(build_dir / "simple_recipe_smoke")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run_result.returncode == 0, (
        f"stdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
