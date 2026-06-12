#!/usr/bin/env python3
"""Generate subsetted LVGL fonts for the UI style component."""

from __future__ import annotations

import argparse
import sqlite3
import subprocess
from pathlib import Path


FONT_SIZES = (24, 28, 40)
SOURCE_FONT_NAME = "SourceHan-Regular_arial_cn.ttf"
RECIPE_DB_NAME = "recipelib.db"
STATIC_UI_TEXT = "用户1234SettingsBackU设置语言亮度清洗关联开休眠详细信息"
ASCII_RANGE = "0x20-0x7E"


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def collect_recipe_names(recipe_db: Path) -> str:
    if not recipe_db.is_file():
        return ""

    with sqlite3.connect(recipe_db) as conn:
        rows = conn.execute("SELECT name FROM simplerecipeEntity ORDER BY id").fetchall()
    return "".join(row[0] or "" for row in rows)


def build_range_arg(text: str) -> str:
    codepoints = sorted({ord(char) for char in text if ord(char) > 0x7E})
    extra_ranges = [f"0x{codepoint:X}" for codepoint in codepoints]
    return ",".join([ASCII_RANGE, *extra_ranges])


def generate_font(repo_root: Path, size: int, range_arg: str) -> None:
    source_font = repo_root / "resources/host/fonts" / SOURCE_FONT_NAME
    output = repo_root / "components/ui_style/src" / f"ui_font_source_han_{size}.c"
    font_name = f"ui_font_source_han_{size}"

    subprocess.run(
        [
            "npx",
            "--yes",
            "lv_font_conv",
            "--font",
            str(source_font),
            "--range",
            range_arg,
            "--size",
            str(size),
            "--format",
            "lvgl",
            "--bpp",
            "4",
            "--no-compress",
            "--lv-include",
            "lvgl.h",
            "--lv-font-name",
            font_name,
            "-o",
            str(output),
        ],
        cwd=repo_root,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=repo_root_from_script(),
        help="Repository root. Defaults to the parent of this script directory.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    recipe_db = repo_root / "resources/host/recipe" / RECIPE_DB_NAME
    source_font = repo_root / "resources/host/fonts" / SOURCE_FONT_NAME

    if not source_font.is_file():
        raise FileNotFoundError(source_font)

    text = STATIC_UI_TEXT + collect_recipe_names(recipe_db)
    range_arg = build_range_arg(text)

    for size in FONT_SIZES:
        generate_font(repo_root, size, range_arg)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
