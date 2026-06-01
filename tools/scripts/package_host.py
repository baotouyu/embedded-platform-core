#!/usr/bin/env python3
"""package_host: package host/macOS build outputs into out/packages/host_macos."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


PACKAGE_NAME = "host_macos"
DEFAULT_OUTPUT_DIR = Path("out") / "packages" / PACKAGE_NAME

HOST_EXECUTABLES = [
    "ep_platform_host_posix",
    "ep_host_resource_smoke",
    "ep_host_lvgl_demo",
    "ep_host_lvgl_widgets_demo",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="打包 host/macOS 构建产物到 out/packages/host_macos。"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="仓库根目录，默认自动使用脚本所在仓库。",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR.parent,
        help=(
            "输出目录。脚本会在该目录下生成 host_macos 子目录，"
            "默认是 out/packages。"
        ),
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="打包前删除已有 host_macos 输出目录。",
    )
    return parser.parse_args()


def resolve_repo_root(repo_root: Path) -> Path:
    return repo_root.expanduser().resolve()


def resolve_output_root(output_dir: Path, repo_root: Path) -> Path:
    expanded = output_dir.expanduser()
    if not expanded.is_absolute():
        expanded = repo_root / expanded
    return expanded.resolve() / PACKAGE_NAME


def required_paths(repo_root: Path) -> list[Path]:
    build_dir = repo_root / "build" / "platforms" / "host" / "posix"
    paths = [build_dir / executable for executable in HOST_EXECUTABLES]
    paths.extend(
        [
            repo_root / "config" / "profiles" / "host.cfg",
            repo_root / "resources" / "host",
            repo_root / "resources" / "common",
        ]
    )
    return paths


def find_missing_required_paths(repo_root: Path) -> list[Path]:
    return [path for path in required_paths(repo_root) if not path.exists()]


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".gitkeep"))


def package_host(repo_root: Path, output_root: Path, clean: bool) -> list[str]:
    missing = find_missing_required_paths(repo_root)
    if missing:
        formatted = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"缺少必需产物：\n{formatted}")

    if clean and output_root.exists():
        shutil.rmtree(output_root)

    output_root.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    build_dir = repo_root / "build" / "platforms" / "host" / "posix"
    for executable in HOST_EXECUTABLES:
        relative = Path("bin") / executable
        copy_file(build_dir / executable, output_root / relative)
        copied.append(relative.as_posix())

    config_relative = Path("config") / "profiles" / "host.cfg"
    copy_file(
        repo_root / "config" / "profiles" / "host.cfg",
        output_root / config_relative,
    )
    copied.append(config_relative.as_posix())

    for resource_name in ["host", "common"]:
        relative = Path("resources") / resource_name
        copy_tree(repo_root / relative, output_root / relative)
        for path in sorted((output_root / relative).rglob("*")):
            if path.is_file():
                copied.append(path.relative_to(output_root).as_posix())

    write_manifest(output_root, copied)
    return copied


def write_manifest(output_root: Path, copied: list[str]) -> None:
    manifest = output_root / "manifest.txt"
    lines = [
        f"package={PACKAGE_NAME}",
        "format=directory",
        "platform=host/macOS",
        "",
        "[files]",
    ]
    lines.extend(copied)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root)
    output_root = resolve_output_root(args.output_dir, repo_root)

    try:
        copied = package_host(repo_root, output_root, args.clean)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"host/macOS 发布包已生成：{output_root}")
    print(f"文件数量：{len(copied)}")
    print(f"清单文件：{output_root / 'manifest.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())