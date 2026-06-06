from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_app_business_skeleton_doc_tracks_current_code_paths_and_services():
    doc = REPO_ROOT / "docs" / "porting" / "app-business-skeleton.md"

    assert doc.is_file()

    text = doc.read_text(encoding="utf-8")
    required_terms = [
        "应用业务骨架",
        "app/main.c",
        "app/app_core.c",
        "app/include/app_context.h",
        "app/selftest/app_selftest.c",
        "app/services/beep_service.h",
        "BEEP_SERVICE_DEFAULT_FREQUENCY_HZ",
        "app/services/rtc_service.h",
        "app/services/lcd_sleep_service.h",
        "app/services/power_board_service.h",
        "app_context_init",
        "app_core_start",
        "app_selftest_run",
        "app_core_run",
        "EP_ERR_UNSUPPORTED",
        "libep_app_core.a",
        "application/rt-thread/ep_app",
    ]

    missing = [term for term in required_terms if term not in text]
    assert not missing, f"Missing app business doc terms: {missing}"


def test_porting_entry_and_luban_overview_link_app_business_doc():
    readme = _read("docs/porting/README.md")
    overview = _read("docs/porting/luban-lite-compatibility-overview.md")

    assert "app-business-skeleton.md" in readme
    assert "app-business-skeleton.md" in overview
