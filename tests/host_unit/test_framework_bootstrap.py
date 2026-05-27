from pathlib import Path


def test_framework_bootstrap_symbols_exist():
    header = Path("core/include/ep_framework.h").read_text()
    app_header = Path("app/include/app_main.h").read_text()
    source = Path("core/src/ep_framework.c").read_text()
    assert "int ep_platform_boot(void);" in header
    assert "int ep_framework_init(void);" in header
    assert "int app_main(void);" in app_header
    assert "int ep_framework_init(void)" in source
