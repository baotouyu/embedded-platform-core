from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_app_main_is_a_thin_business_entrypoint():
    source = _read("app/main.c")

    assert '#include "app_core.h"' in source
    assert '#include "app_main.h"' in source
    assert "app_context_init(&app)" in source
    assert "app_core_start(&app)" in source
    assert "app_selftest_run(&app)" in source
    assert "app_core_run(&app)" in source
    assert "ep_event_subscribe" not in source
    assert "ep_timer_start" not in source
    assert "APP_TIMER_ID_SELF_TEST" not in source


def test_app_core_defines_application_lifecycle_boundary():
    header = _read("app/include/app_core.h")
    context = _read("app/include/app_context.h")
    source = _read("app/app_core.c")

    assert "typedef struct app_context" in context
    assert "int services_ready;" in context
    assert "void app_context_init(app_context_t *app);" in header
    assert "int app_core_start(app_context_t *app);" in header
    assert "int app_core_run(app_context_t *app);" in header
    assert "beep_service_init()" in source
    assert "rtc_service_init()" in source
    assert "lcd_sleep_service_init()" in source
    assert "power_board_service_init()" in source
    assert 'EP_LOGI("app", "app lifecycle start")' in source
    assert 'EP_LOGI("app", "app lifecycle done")' in source


def test_app_selftest_owns_timer_event_smoke_flow():
    header = _read("app/selftest/app_selftest.h")
    source = _read("app/selftest/app_selftest.c")

    assert "int app_selftest_run(app_context_t *app);" in header
    assert "APP_EVENT_TIMER_DONE" in source
    assert "APP_TIMER_ID_SELF_TEST" in source
    assert "ep_event_subscribe(APP_EVENT_TIMER_DONE" in source
    assert "ep_timer_start(APP_TIMER_ID_SELF_TEST" in source
    assert "ep_sleep_ms(APP_WAIT_STEP_MS)" in source
    assert "return EP_ERR_TIMEOUT;" in source
    assert 'EP_LOGE("app", "app lifecycle timeout")' in source


def test_app_services_define_business_facing_device_boundaries():
    expected_headers = [
        "app/services/beep_service.h",
        "app/services/rtc_service.h",
        "app/services/lcd_sleep_service.h",
        "app/services/power_board_service.h",
    ]
    for header_path in expected_headers:
        assert (REPO_ROOT / header_path).is_file(), header_path

    beep_header = _read("app/services/beep_service.h")
    rtc_header = _read("app/services/rtc_service.h")
    lcd_header = _read("app/services/lcd_sleep_service.h")
    power_header = _read("app/services/power_board_service.h")

    assert "BEEP_SERVICE_DEFAULT_FREQUENCY_HZ 2700u" in beep_header
    assert "int beep_service_init(void);" in beep_header
    assert "int beep_service_beep_ms(unsigned int duration_ms);" in beep_header
    assert "int rtc_service_init(void);" in rtc_header
    assert "int rtc_service_get_time(ep_rtc_time_t *time);" in rtc_header
    assert "int lcd_sleep_service_set_sleep(int sleep_enabled);" in lcd_header
    assert "int power_board_service_init(void);" in power_header
    assert "int power_board_service_write(const void *buf, size_t len);" in power_header


def test_app_cmake_and_sdk_export_include_business_skeleton_sources():
    app_cmake = _read("app/CMakeLists.txt")
    sdk_export = _read("tools/scripts/export_sdk_ep_package.sh")
    host_export = _read("cmake/modules/ep_export_targets.cmake")

    expected_sources = [
        "app_core.c",
        "selftest/app_selftest.c",
        "services/beep_service.c",
        "services/rtc_service.c",
        "services/lcd_sleep_service.c",
        "services/power_board_service.c",
    ]
    for source in expected_sources:
        assert source in app_cmake
        assert f"app/{source}" in sdk_export

    assert "${CMAKE_CURRENT_SOURCE_DIR}/services" in app_cmake
    assert "app/app_core.c" in host_export
    assert "app/selftest/app_selftest.c" in host_export
