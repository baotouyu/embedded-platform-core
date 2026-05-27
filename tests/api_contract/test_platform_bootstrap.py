from pathlib import Path


def test_both_platform_families_have_bootstrap_entries():
    rtos = Path("platforms/rtos/demo_family/startup/app_start.c").read_text()
    linux = Path("platforms/linux/demo_family/startup/main.c").read_text()
    assert "ep_platform_boot" in rtos
    assert "ep_framework_start" in rtos
    assert "ep_platform_boot" in linux
    assert "ep_framework_start" in linux
