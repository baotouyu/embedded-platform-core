#!/usr/bin/env python3
"""SDK 指针同步 YAML 辅助工具。

不引入外部 YAML 依赖，使用行级编辑保留现有格式。
"""

import sys
from pathlib import Path


def find_section_boundaries(lines, section_name):
    """返回 (start_idx, end_idx)，start_idx 是 'section_name:' 行的索引，end_idx 是块末（包含）"""
    start = None
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped == section_name + ":":
            start = i
            continue
        if start is not None:
            # 遇到下一个顶级 key 或空行后的非缩进行，结束
            if stripped and not stripped.startswith(" ") and stripped.endswith(":"):
                return start, i - 1
    if start is not None:
        return start, len(lines) - 1
    return None, None


def find_key_in_section(lines, section_name, key):
    """在指定 section 内查找 key 对应的行索引和值"""
    start, end = find_section_boundaries(lines, section_name)
    if start is None:
        return None, None
    prefix = "  " + key + ": "
    for i in range(start + 1, end + 1):
        if lines[i].startswith(prefix):
            return i, lines[i][len(prefix):].rstrip()
    return None, None


def read_sdk_upstream_ref(sdk_yaml_path):
    """读取 sdk.yaml 中 upstream.ref"""
    with open(sdk_yaml_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    _, ref = find_key_in_section(lines, "upstream", "ref")
    if ref is None:
        sys.stderr.write(f"sdk.yaml 缺少 upstream.ref 字段：{sdk_yaml_path}\n")
        sys.exit(1)
    print(ref)


def read_target_refs(targets_dir, sdk_name):
    """读取所有 sdk.name == sdk_name 的 target YAML 的 sdk.ref"""
    targets_path = Path(targets_dir)
    found_any = False
    for yaml_file in sorted(targets_path.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        idx, name = find_key_in_section(lines, "sdk", "name")
        if name != sdk_name:
            continue
        _, ref = find_key_in_section(lines, "sdk", "ref")
        if ref is None:
            sys.stderr.write(f"{yaml_file.name} 的 sdk.ref 字段缺失\n")
            sys.exit(1)
        found_any = True
        print(f"{yaml_file.name}:{ref}")
    if not found_any:
        sys.stderr.write(f"没有 target 使用 SDK：{sdk_name}\n")


def update_sdk_upstream_ref(sdk_yaml_path, new_ref):
    """更新 sdk.yaml 中 upstream.ref"""
    with open(sdk_yaml_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    idx, old_ref = find_key_in_section(lines, "upstream", "ref")
    if idx is None:
        sys.stderr.write(f"sdk.yaml 缺少 upstream.ref 字段：{sdk_yaml_path}\n")
        sys.exit(1)
    old_line = lines[idx]
    new_line = old_line.replace(old_ref, new_ref)
    lines[idx] = new_line
    with open(sdk_yaml_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"已更新 sdk.yaml upstream.ref：{old_ref} -> {new_ref}")


def update_sdk_notes_commit(sdk_yaml_path, old_commit, new_commit):
    """更新 sdk.yaml notes 中出现的 upstream commit 引用"""
    with open(sdk_yaml_path, "r", encoding="utf-8") as f:
        content = f.read()
    if old_commit not in content:
        return  # 没有需要更新的 notes
    new_content = content.replace(old_commit, new_commit)
    if new_content == content:
        return
    with open(sdk_yaml_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"已更新 sdk.yaml notes 中的 commit 引用：{old_commit} -> {new_commit}")


def update_target_refs(targets_dir, sdk_name, new_ref):
    """更新所有 sdk.name == sdk_name 的 target YAML 的 sdk.ref"""
    targets_path = Path(targets_dir)
    updated = 0
    for yaml_file in sorted(targets_path.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        idx, name = find_key_in_section(lines, "sdk", "name")
        if name != sdk_name:
            continue
        ref_idx, old_ref = find_key_in_section(lines, "sdk", "ref")
        if ref_idx is None:
            sys.stderr.write(f"{yaml_file.name} 的 sdk.ref 字段缺失\n")
            sys.exit(1)
        if old_ref == new_ref:
            continue
        old_line = lines[ref_idx]
        new_line = old_line.replace(old_ref, new_ref)
        lines[ref_idx] = new_line
        with open(yaml_file, "w", encoding="utf-8") as f:
            f.writelines(lines)
        updated += 1
        print(f"已更新 {yaml_file.name}：sdk.ref {old_ref} -> {new_ref}")
    print(f"已更新 target 数量：{updated}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write(
            "用法: _sync_sdk_pins_update_yaml.py <command> [args...]\n"
            "命令: read-sdk-upstream-ref | read-target-refs | "
            "update-sdk-upstream-ref | update-sdk-notes | update-target-refs\n"
        )
        sys.exit(2)

    cmd = sys.argv[1]

    if cmd == "read-sdk-upstream-ref":
        read_sdk_upstream_ref(sys.argv[2])
    elif cmd == "read-target-refs":
        read_target_refs(sys.argv[2], sys.argv[3])
    elif cmd == "update-sdk-upstream-ref":
        update_sdk_upstream_ref(sys.argv[2], sys.argv[3])
    elif cmd == "update-sdk-notes":
        update_sdk_notes_commit(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "update-target-refs":
        update_target_refs(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        sys.stderr.write(f"未知命令：{cmd}\n")
        sys.exit(2)
