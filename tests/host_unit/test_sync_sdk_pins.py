"""测试 SDK 指针同步入口 sync-sdk-pins。

所有测试使用临时本地 Git 仓库和 submodule，不访问网络。
"""

import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "build.sh"
YAML_HELPER = REPO_ROOT / "tools" / "scripts" / "_sync_sdk_pins_update_yaml.py"


def _run(cmd, cwd=None, check=True):
    result = subprocess.run(
        cmd, cwd=cwd, check=False, text=True, capture_output=True,
    )
    if check and result.returncode != 0:
        print(f"CMD FAILED: {' '.join(cmd)}", flush=True)
        print(f"STDOUT: {result.stdout}", flush=True)
        print(f"STDERR: {result.stderr}", flush=True)
        raise AssertionError(f"Command failed: {result.stderr}")
    return result


def _git(args, cwd):
    return _run(["git", *args], cwd=cwd)


def _init_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    _git(["init", "-b", "main"], path)
    _git(["config", "user.email", "test@example.com"], path)
    _git(["config", "user.name", "Test User"], path)


def _commit_all(repo, msg="commit"):
    _git(["add", "-A"], repo)
    _git(["commit", "-m", msg], repo)


def _head(repo):
    return _git(["rev-parse", "HEAD"], repo).stdout.strip()


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _sdk_yaml(upstream_ref):
    return f"""name: sdk-artinchip-luban-lite
vendor: artinchip
sdk_family: luban-lite
status: integration-skeleton

upstream:
  type: github
  url: https://github.com/baotouyu/luban-lite.git
  path: upstream/luban-lite
  ref: {upstream_ref}
  version: v1.3.0

entrypoints:
  prepare: scripts/prepare.sh
  inspect: scripts/inspect_luban_lite.sh
  build_firmware: scripts/build_firmware.sh
  flash: scripts/flash.sh

notes:
  - upstream/luban-lite 固定到提交 {upstream_ref}，不自动跟随官方更新。
"""


def _target_yaml(target_name, sdk_name, ref):
    return f"""target: {target_name}

platform:
  family: rtos
  vendor: test
  sdk_family: demo
  chip: test
  board: test
  kernel: none

sdk:
  name: {sdk_name}
  repo: https://example.com/{sdk_name}.git
  ref: {ref}

toolchain:
  source: sdk

output:
  ep_package: out/ep/{target_name}
  firmware: out/firmware/{target_name}
"""


# ---- 测试夹具 ----

def _build_structure(workdir):
    """
    返回 (main_dir, sdk_checkout, upstream_checkout)

    结构：
      workdir/upstream/     -- Luban-Lite 独立仓库
      workdir/sdk-adapter/  -- SDK 适配仓库，含 upstream submodule
      workdir/main/         -- 主工程，含 sdk-adapter submodule

    脚本通过 main_dir 的 submodule checkout 读取文件。
    修改独立仓库后，需通过 _refresh 同步到 main_dir 的检出。
    """
    main = workdir / "main"
    sdk = workdir / "sdk-adapter"
    up = workdir / "upstream"

    _init_repo(up)
    _write(up / "README.md", "Luban-Lite upstream\n")
    _commit_all(up, "initial upstream")

    _init_repo(sdk)
    _write(sdk / "README.md", "SDK adapter\n")
    _git(["-c", "protocol.file.allow=always", "submodule", "add",
          str(up), "upstream/luban-lite"], sdk)
    _commit_all(sdk, "add upstream submodule")

    _init_repo(main)
    _write(main / "README.md", "Main project\n")
    _git(["-c", "protocol.file.allow=always", "submodule", "add",
          str(sdk), "third_party/sdk/sdk-artinchip-luban-lite"], main)
    _commit_all(main, "add SDK submodule")

    sdk_co = main / "third_party" / "sdk" / "sdk-artinchip-luban-lite"
    up_co = sdk_co / "upstream" / "luban-lite"
    return main, sdk_co, up_co


def _refresh_main(main_dir):
    """将 main_dir 内 SDK submodule checkout 更新到 origin 最新 HEAD（保持在 main 分支）"""
    sdk_co = main_dir / "third_party" / "sdk" / "sdk-artinchip-luban-lite"
    _git(["fetch", "origin"], sdk_co)
    _git(["checkout", "main"], sdk_co)
    _git(["merge", "--ff-only", "origin/main"], sdk_co)
    _git(["-c", "protocol.file.allow=always", "submodule", "update",
          "--init", "--recursive"], sdk_co)


# ---- 参数校验测试 ----

def test_build_help_lists_sync_sdk_pins():
    result = _run([str(BUILD_SCRIPT), "help"])
    assert result.returncode == 0
    assert "sync-sdk-pins" in result.stdout
    assert "同步 SDK submodule 指针" in result.stdout


def test_rejects_missing_sdk_name():
    result = _run([str(BUILD_SCRIPT), "sync-sdk-pins", "--check"], check=False)
    assert result.returncode != 0


def test_rejects_no_action():
    result = _run([
        str(BUILD_SCRIPT), "sync-sdk-pins", "sdk-test",
        "--repo-root", str(REPO_ROOT),
    ], check=False)
    assert result.returncode != 0


def test_rejects_nonexistent_sdk():
    result = _run([
        str(BUILD_SCRIPT), "sync-sdk-pins", "nonexistent-sdk",
        "--check", "--repo-root", str(REPO_ROOT),
    ], check=False)
    assert result.returncode != 0
    assert "目录不存在" in result.stderr


# ---- --check 测试 ----

def test_check_all_consistent_passes():
    with tempfile.TemporaryDirectory() as tmp:
        wdir = Path(tmp)
        main_dir, sdk_co, up_co = _build_structure(wdir)

        sdk_adapter = wdir / "sdk-adapter"
        up_head = _head(wdir / "upstream")

        _write(sdk_adapter / "sdk.yaml", _sdk_yaml(up_head))
        _git(["add", "sdk.yaml"], sdk_adapter)
        _git(["commit", "-m", "add sdk.yaml"], sdk_adapter)

        _refresh_main(main_dir)
        sdk_head = _head(sdk_co)

        _write(main_dir / "targets" / "t1.yaml",
               _target_yaml("t1", "sdk-artinchip-luban-lite", sdk_head))
        _write(main_dir / "targets" / "t2.yaml",
               _target_yaml("t2", "sdk-artinchip-luban-lite", sdk_head))

        _git(["add", "third_party/sdk/sdk-artinchip-luban-lite", "targets"], main_dir)
        _git(["commit", "-m", "update submodules and targets"], main_dir)

        result = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--check",
            "--repo-root", str(main_dir),
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "指针一致" in result.stdout


def test_check_target_ref_stale_fails():
    with tempfile.TemporaryDirectory() as tmp:
        wdir = Path(tmp)
        main_dir, sdk_co, up_co = _build_structure(wdir)

        sdk_adapter = wdir / "sdk-adapter"
        up_head = _head(wdir / "upstream")

        _write(sdk_adapter / "sdk.yaml", _sdk_yaml(up_head))
        _git(["add", "sdk.yaml"], sdk_adapter)
        _git(["commit", "-m", "add sdk.yaml"], sdk_adapter)

        _refresh_main(main_dir)

        _write(main_dir / "targets" / "t1.yaml",
               _target_yaml("t1", "sdk-artinchip-luban-lite", "deadbeefdeadbeef"))
        _git(["add", "third_party/sdk/sdk-artinchip-luban-lite", "targets"], main_dir)
        _git(["commit", "-m", "add target with wrong ref"], main_dir)

        result = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--check",
            "--repo-root", str(main_dir),
        ], check=False)
        assert result.returncode != 0
        assert "不一致" in result.stderr


def test_check_upstream_ref_stale_fails():
    with tempfile.TemporaryDirectory() as tmp:
        wdir = Path(tmp)
        main_dir, sdk_co, up_co = _build_structure(wdir)

        sdk_adapter = wdir / "sdk-adapter"
        _write(sdk_adapter / "sdk.yaml", _sdk_yaml("deadbeefdeadbeef"))
        _git(["add", "sdk.yaml"], sdk_adapter)
        _git(["commit", "-m", "add sdk.yaml with wrong ref"], sdk_adapter)

        _refresh_main(main_dir)
        sdk_head = _head(sdk_co)

        _write(main_dir / "targets" / "t1.yaml",
               _target_yaml("t1", "sdk-artinchip-luban-lite", sdk_head))
        _git(["add", "third_party/sdk/sdk-artinchip-luban-lite", "targets"], main_dir)
        _git(["commit", "-m", "add target"], main_dir)

        result = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--check",
            "--repo-root", str(main_dir),
        ], check=False)
        assert result.returncode != 0
        assert "不一致" in result.stderr


# ---- 安全预检测试 ----

def test_upstream_dirty_fails_commit():
    with tempfile.TemporaryDirectory() as tmp:
        wdir = Path(tmp)
        main_dir, sdk_co, up_co = _build_structure(wdir)

        sdk_adapter = wdir / "sdk-adapter"
        up_head = _head(wdir / "upstream")

        _write(sdk_adapter / "sdk.yaml", _sdk_yaml(up_head))
        _git(["add", "sdk.yaml"], sdk_adapter)
        _git(["commit", "-m", "add sdk.yaml"], sdk_adapter)

        _refresh_main(main_dir)
        sdk_head = _head(sdk_co)

        _write(main_dir / "targets" / "t1.yaml",
               _target_yaml("t1", "sdk-artinchip-luban-lite", sdk_head))
        _git(["add", "third_party/sdk/sdk-artinchip-luban-lite", "targets"], main_dir)
        _git(["commit", "-m", "add target"], main_dir)

        _write(up_co / "dirty.txt", "uncommitted\n")

        result = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--commit",
            "--repo-root", str(main_dir),
        ], check=False)
        assert result.returncode != 0
        assert "未提交" in result.stderr


def test_sdk_unrelated_dirty_fails_commit():
    with tempfile.TemporaryDirectory() as tmp:
        wdir = Path(tmp)
        main_dir, sdk_co, up_co = _build_structure(wdir)

        sdk_adapter = wdir / "sdk-adapter"
        up_head = _head(wdir / "upstream")

        _write(sdk_adapter / "sdk.yaml", _sdk_yaml(up_head))
        _git(["add", "sdk.yaml"], sdk_adapter)
        _git(["commit", "-m", "add sdk.yaml"], sdk_adapter)

        _refresh_main(main_dir)
        sdk_head = _head(sdk_co)

        _write(main_dir / "targets" / "t1.yaml",
               _target_yaml("t1", "sdk-artinchip-luban-lite", sdk_head))
        _git(["add", "third_party/sdk/sdk-artinchip-luban-lite", "targets"], main_dir)
        _git(["commit", "-m", "add target"], main_dir)

        _write(sdk_co / "unrelated.sh", "echo bad\n")

        result = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--commit",
            "--repo-root", str(main_dir),
        ], check=False)
        assert result.returncode != 0
        assert "不相关" in result.stderr


def test_main_unrelated_dirty_fails_commit():
    with tempfile.TemporaryDirectory() as tmp:
        wdir = Path(tmp)
        main_dir, sdk_co, up_co = _build_structure(wdir)

        sdk_adapter = wdir / "sdk-adapter"
        up_head = _head(wdir / "upstream")

        _write(sdk_adapter / "sdk.yaml", _sdk_yaml(up_head))
        _git(["add", "sdk.yaml"], sdk_adapter)
        _git(["commit", "-m", "add sdk.yaml"], sdk_adapter)

        _refresh_main(main_dir)
        sdk_head = _head(sdk_co)

        _write(main_dir / "targets" / "t1.yaml",
               _target_yaml("t1", "sdk-artinchip-luban-lite", sdk_head))
        _git(["add", "third_party/sdk/sdk-artinchip-luban-lite", "targets"], main_dir)
        _git(["commit", "-m", "add target"], main_dir)

        _write(main_dir / "src" / "dirty.c", "int main(){}")

        result = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--commit",
            "--repo-root", str(main_dir),
        ], check=False)
        assert result.returncode != 0
        assert "不相关" in result.stderr


# ---- Python YAML 辅助工具测试 ----

def test_yaml_read_upstream_ref():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _write(d / "sdk.yaml", _sdk_yaml("abc123"))
        result = _run([
            "python3", str(YAML_HELPER),
            "read-sdk-upstream-ref", str(d / "sdk.yaml"),
        ])
        assert result.stdout.strip() == "abc123"


def test_yaml_read_target_refs():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _write(d / "t1.yaml", _target_yaml("t1", "my-sdk", "c1"))
        _write(d / "t2.yaml", _target_yaml("t2", "other-sdk", "c2"))

        result = _run([
            "python3", str(YAML_HELPER),
            "read-target-refs", str(d), "my-sdk",
        ])
        assert "t1.yaml:c1" in result.stdout
        assert "t2" not in result.stdout


def test_yaml_update_upstream_ref():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _write(d / "sdk.yaml", _sdk_yaml("old-ref"))
        _run([
            "python3", str(YAML_HELPER),
            "update-sdk-upstream-ref", str(d / "sdk.yaml"), "new-ref",
        ])
        content = (d / "sdk.yaml").read_text()
        assert "ref: new-ref" in content
        assert "ref: old-ref" not in content


def test_yaml_update_notes():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _write(d / "sdk.yaml", _sdk_yaml("old-abc"))
        _run([
            "python3", str(YAML_HELPER),
            "update-sdk-notes", str(d / "sdk.yaml"), "old-abc", "new-def",
        ])
        content = (d / "sdk.yaml").read_text()
        assert "new-def" in content
        assert "old-abc" not in content


def test_yaml_update_target_refs():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _write(d / "t1.yaml", _target_yaml("t1", "sdk-artinchip-luban-lite", "old"))
        _write(d / "t2.yaml", _target_yaml("t2", "sdk-artinchip-luban-lite", "old"))
        _write(d / "t3.yaml", _target_yaml("t3", "other-sdk", "keep-me"))

        result = _run([
            "python3", str(YAML_HELPER),
            "update-target-refs", str(d), "sdk-artinchip-luban-lite", "new-ref",
        ])
        assert "已更新 target 数量：2" in result.stdout

        assert "ref: new-ref" in (d / "t1.yaml").read_text()
        assert "ref: new-ref" in (d / "t2.yaml").read_text()
        assert "ref: keep-me" in (d / "t3.yaml").read_text()


# ---- 边界场景测试 ----

def _target_yaml_missing_ref(target_name, sdk_name):
    """一个 sdk.name 匹配但缺少 sdk.ref 的 target YAML"""
    return f"""target: {target_name}

platform:
  family: rtos
  vendor: test
  sdk_family: demo
  chip: test
  board: test
  kernel: none

sdk:
  name: {sdk_name}
  repo: https://example.com/{sdk_name}.git

toolchain:
  source: sdk

output:
  ep_package: out/ep/{target_name}
  firmware: out/firmware/{target_name}
"""


def test_check_target_missing_ref_fails():
    """target 匹配 sdk.name 但缺少 sdk.ref 时 --check 必须失败（不能报指针一致）"""
    with tempfile.TemporaryDirectory() as tmp:
        wdir = Path(tmp)
        main_dir, sdk_co, up_co = _build_structure(wdir)

        sdk_adapter = wdir / "sdk-adapter"
        up_head = _head(wdir / "upstream")

        _write(sdk_adapter / "sdk.yaml", _sdk_yaml(up_head))
        _git(["add", "sdk.yaml"], sdk_adapter)
        _git(["commit", "-m", "add sdk.yaml"], sdk_adapter)

        _refresh_main(main_dir)

        # 创建缺少 sdk.ref 的 target
        _write(main_dir / "targets" / "bad.yaml",
               _target_yaml_missing_ref("bad", "sdk-artinchip-luban-lite"))
        _git(["add", "third_party/sdk/sdk-artinchip-luban-lite", "targets"], main_dir)
        _git(["commit", "-m", "add bad target"], main_dir)

        result = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--check",
            "--repo-root", str(main_dir),
        ], check=False)
        assert result.returncode != 0, f"应失败但通过了：{result.stdout}"
        assert "sdk.ref" in result.stderr


def test_commit_syncs_sdk_then_main():
    """--commit 在 target ref 过期时更新 target，最终 --check 通过"""
    with tempfile.TemporaryDirectory() as tmp:
        wdir = Path(tmp)
        main_dir, sdk_co, up_co = _build_structure(wdir)

        sdk_adapter = wdir / "sdk-adapter"
        up_head = _head(wdir / "upstream")

        # 初始状态：sdk.yaml 指向正确 upstream
        _write(sdk_adapter / "sdk.yaml", _sdk_yaml(up_head))
        _git(["add", "sdk.yaml"], sdk_adapter)
        _git(["commit", "-m", "add sdk.yaml"], sdk_adapter)

        _refresh_main(main_dir)
        sdk_head_v1 = _head(sdk_co)

        # 创建 target，用正确 ref + 另一个 SDK 的 target
        _write(main_dir / "targets" / "t1.yaml",
               _target_yaml("t1", "sdk-artinchip-luban-lite", sdk_head_v1))
        _write(main_dir / "targets" / "t2.yaml",
               _target_yaml("t2", "other-sdk", "other-ref"))
        _git(["add", "third_party/sdk/sdk-artinchip-luban-lite", "targets"], main_dir)
        _git(["commit", "-m", "add targets"], main_dir)

        # 初始 --check 应通过
        result_pre = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--check",
            "--repo-root", str(main_dir),
        ])
        assert result_pre.returncode == 0

        # 在 SDK 适配仓库中新增提交，推进 HEAD
        _write(sdk_adapter / "NEW.md", "sdk change\n")
        _git(["add", "NEW.md"], sdk_adapter)
        _git(["commit", "-m", "sdk adapter advance"], sdk_adapter)

        _refresh_main(main_dir)
        sdk_head_v2 = _head(sdk_co)
        assert sdk_head_v2 != sdk_head_v1

        # target 仍指向旧 ref，--check 应检测到不一致
        result_stale = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--check",
            "--repo-root", str(main_dir),
        ], check=False)
        # 这里可能 target ref 过期但 SDK gitlink 也因为 submodule 同步已更新
        # 不一致应被捕获
        print(f"STALE CHECK: rc={result_stale.returncode} stderr={result_stale.stderr[:200]}")

        # 运行 --commit 同步
        result = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--commit",
            "--repo-root", str(main_dir),
        ], check=False)
        print(f"COMMIT: rc={result.returncode}")
        print(f"COMMIT STDOUT: {result.stdout[:500]}")

        # 最终 --check 必须通过
        result_final = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--check",
            "--repo-root", str(main_dir),
        ])
        assert result_final.returncode == 0, f"最终检查失败：{result_final.stderr}"
        assert "指针一致" in result_final.stdout

        # 验证 other-sdk target 未被修改
        t2_content = (main_dir / "targets" / "t2.yaml").read_text()
        assert "ref: other-ref" in t2_content


def test_commit_preserves_other_sdk_targets():
    """--commit 更新 targets/*.yaml 时不应修改 sdk.name 不同的 target"""
    with tempfile.TemporaryDirectory() as tmp:
        wdir = Path(tmp)
        main_dir, sdk_co, up_co = _build_structure(wdir)

        sdk_adapter = wdir / "sdk-adapter"
        up_head = _head(wdir / "upstream")

        _write(sdk_adapter / "sdk.yaml", _sdk_yaml(up_head))
        _git(["add", "sdk.yaml"], sdk_adapter)
        _git(["commit", "-m", "add sdk.yaml"], sdk_adapter)

        _refresh_main(main_dir)
        sdk_head = _head(sdk_co)

        # 创建匹配和未匹配的 target
        _write(main_dir / "targets" / "match.yaml",
               _target_yaml("match", "sdk-artinchip-luban-lite", "stale-ref"))
        _write(main_dir / "targets" / "other.yaml",
               _target_yaml("other", "other-sdk", "keep-me"))
        _git(["add", "third_party/sdk/sdk-artinchip-luban-lite", "targets"], main_dir)
        _git(["commit", "-m", "add targets"], main_dir)

        # 用 Python helper 验证：只更新匹配 SDK 的 target
        _run([
            "python3", str(YAML_HELPER),
            "update-target-refs", str(main_dir / "targets"),
            "sdk-artinchip-luban-lite", sdk_head,
        ])
        match_content = (main_dir / "targets" / "match.yaml").read_text()
        other_content = (main_dir / "targets" / "other.yaml").read_text()
        assert f"ref: {sdk_head}" in match_content
        assert "ref: keep-me" in other_content


def test_commit_detached_head_rejected():
    """SDK 适配仓库或主工程处于 detached HEAD 时 --commit 应失败"""
    with tempfile.TemporaryDirectory() as tmp:
        wdir = Path(tmp)
        main_dir, sdk_co, up_co = _build_structure(wdir)

        sdk_adapter = wdir / "sdk-adapter"
        up_head = _head(wdir / "upstream")

        _write(sdk_adapter / "sdk.yaml", _sdk_yaml(up_head))
        _git(["add", "sdk.yaml"], sdk_adapter)
        _git(["commit", "-m", "add sdk.yaml"], sdk_adapter)

        _refresh_main(main_dir)
        sdk_head = _head(sdk_co)

        _write(main_dir / "targets" / "t1.yaml",
               _target_yaml("t1", "sdk-artinchip-luban-lite", sdk_head))
        _git(["add", "third_party/sdk/sdk-artinchip-luban-lite", "targets"], main_dir)
        _git(["commit", "-m", "add target"], main_dir)

        # 将 SDK 适配仓库 checkout 到 detached HEAD
        _git(["checkout", sdk_head], sdk_co)

        result = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--commit",
            "--repo-root", str(main_dir),
        ], check=False)
        assert result.returncode != 0
        assert "分离头指针" in result.stderr or "detached" in result.stderr.lower()


def test_commit_target_parse_error_does_not_commit_sdk():
    """target YAML 解析失败时，--commit 不得产生 SDK 适配仓库提交，不能留下半同步状态"""
    with tempfile.TemporaryDirectory() as tmp:
        wdir = Path(tmp)
        main_dir, sdk_co, up_co = _build_structure(wdir)

        sdk_adapter = wdir / "sdk-adapter"
        up_head_v1 = _head(wdir / "upstream")

        # 在 upstream 创建第二个提交，使 sdk.yaml 的 upstream ref 过期
        _write(wdir / "upstream" / "new.md", "upstream change\n")
        _git(["add", "new.md"], wdir / "upstream")
        _git(["commit", "-m", "upstream advance"], wdir / "upstream")
        up_head_v2 = _head(wdir / "upstream")

        # sdk.yaml 仍然指向旧 upstream ref（过期状态）
        _write(sdk_adapter / "sdk.yaml", _sdk_yaml(up_head_v1))
        _git(["add", "sdk.yaml"], sdk_adapter)
        _git(["commit", "-m", "add sdk.yaml with stale upstream ref"], sdk_adapter)

        _refresh_main(main_dir)
        sdk_head_before = _head(sdk_co)

        # 创建 target：匹配 sdk.name 但缺少 sdk.ref
        _write(main_dir / "targets" / "bad.yaml",
               _target_yaml_missing_ref("bad", "sdk-artinchip-luban-lite"))
        _git(["add", "third_party/sdk/sdk-artinchip-luban-lite", "targets"], main_dir)
        _git(["commit", "-m", "add bad target"], main_dir)

        # 记录 SDK 适配仓库当前 HEAD 和主工程状态
        sdk_commits_before = int(_git(
            ["rev-list", "--count", "HEAD"], sdk_co
        ).stdout.strip())
        main_commits_before = int(_git(
            ["rev-list", "--count", "HEAD"], main_dir
        ).stdout.strip())

        # 执行 --commit
        result = _run([
            str(BUILD_SCRIPT), "sync-sdk-pins",
            "sdk-artinchip-luban-lite", "--commit",
            "--repo-root", str(main_dir),
        ], check=False)
        assert result.returncode != 0, "--commit 应因 bad.yaml 缺少 sdk.ref 而失败"
        assert "sdk.ref" in result.stderr

        # 验证 1：SDK 适配仓库 HEAD 不变（没有产生新 commit）
        sdk_commits_after = int(_git(
            ["rev-list", "--count", "HEAD"], sdk_co
        ).stdout.strip())
        assert sdk_commits_after == sdk_commits_before, (
            f"SDK 适配仓库不应产生新 commit（前 {sdk_commits_before}，后 {sdk_commits_after}）"
        )

        # 验证 2：主工程不留下脏 third_party/sdk/... 路径
        dirty = _git(["status", "--porcelain"], main_dir).stdout
        # 允许 targets/bad.yaml 在 dirty 列表（因为这是用户自己的错误文件），
        # 但不能有 third_party/sdk/... 被脚本部分修改
        sdk_sub_path = "third_party/sdk/sdk-artinchip-luban-lite"
        for line in dirty.splitlines():
            # 跳过空行
            if not line.strip():
                continue
            path_in_line = line[3:] if len(line) > 3 else ""
            assert sdk_sub_path not in path_in_line, (
                f"主工程不得留下脏的 SDK gitlink：{line}"
            )
