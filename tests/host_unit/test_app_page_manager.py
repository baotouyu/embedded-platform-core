from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_page_manager_is_portable_lvgl9_component():
    header = _read("app/ui/page_manager.h")
    source = _read("app/ui/page_manager.c")

    assert '#include "lvgl.h"' in header
    assert "ui_manager_t" not in header
    assert "ui_objects.h" not in header
    assert "aic_ui.h" not in header
    assert "ui_util.h" not in header
    assert "page_manager_init(void *app_ctx);" in header
    assert "page_manager_register(" in header
    assert "page_manager_switch(" in header
    assert "page_manager_back(" in header
    assert "page_manager_send_event(" in header
    assert "page_manager_freeze(" in header
    assert "page_manager_unfreeze(" in header
    assert "page_manager_current_page_id(void);" in header

    assert "screen_is_loading" not in source
    assert "ui_manager" not in source
    assert "static page_node_t *current_node" not in source
    assert "lv_screen_load_anim" in source


def test_page_manager_can_freeze_and_unfreeze_page_switching():
    header = _read("app/ui/page_manager.h")
    source = _read("app/ui/page_manager.c")

    assert "int page_manager_freeze(page_manager_page_id_t page_id);" in header
    assert "int page_manager_unfreeze(page_manager_page_id_t page_id);" in header
    assert "bool is_frozen;" in source
    assert "entry->is_frozen = false" in source
    assert "if (entry->is_frozen)" in source
    assert "int page_manager_freeze(page_manager_page_id_t page_id)" in source
    assert "int page_manager_unfreeze(page_manager_page_id_t page_id)" in source
    assert "entry->is_frozen = true" in source


def test_page_manager_dispatches_events_to_current_page_only():
    header = _read("app/ui/page_manager.h")
    source = _read("app/ui/page_manager.c")
    home_page = _read("app/ui/pages/home_page.c")
    settings_page = _read("app/ui/pages/settings_page.c")

    assert (
        "int page_manager_send_event(page_manager_page_id_t page_id,\n"
        "                            uint32_t code,\n"
        "                            uint32_t wparam,\n"
        "                            uint32_t lparam);"
    ) in header
    assert "page_manager_send_event(page_manager_page_id_t page_id" in source
    assert "page_id != current_page_id" in source
    assert "entry->event_cb == NULL" in source
    assert "entry->event_cb(&ctx, code, wparam, lparam)" in source
    assert "ctx.screen = entry->screen" in source

    assert "HOME_PAGE_EVENT_REFRESH" in home_page
    assert "SETTINGS_PAGE_EVENT_REFRESH" in settings_page


def test_page_manager_keeps_switch_lock_until_screen_loaded_event():
    source = _read("app/ui/page_manager.c")

    assert "page_manager_screen_loaded_event" in source
    assert "LV_EVENT_SCREEN_LOADED" in source
    assert "LV_EVENT_SCREEN_UNLOADED" in source
    assert "page_manager_switching = false" in source
    assert "page_manager_transition_page_id" in source
    assert "lv_obj_add_event_cb(entry->screen, page_manager_screen_loaded_event" in source

    load_call = "lv_screen_load_anim(entry->screen, anim_type, anim_time, 0, true);"
    load_index = source.index(load_call)
    after_load = source[load_index : load_index + 180]
    assert "page_manager_switching = false" not in after_load


def test_page_manager_exposes_history_back_navigation():
    header = _read("app/ui/page_manager.h")
    source = _read("app/ui/page_manager.c")
    settings_page = _read("app/ui/pages/settings_page.c")

    assert "int page_manager_back(lv_screen_load_anim_t anim_type, uint32_t anim_time);" in header
    assert "#define PAGE_MANAGER_HISTORY_SIZE" in source
    assert "page_history[" in source
    assert "page_history_count" in source
    assert "page_manager_push_history" in source
    assert "page_manager_back(" in source
    assert "page_manager_switch(previous_page_id" in source

    assert "page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180)" in settings_page
    assert "page_manager_switch(APP_PAGE_HOME" not in settings_page


def test_home_page_builds_recipe_carousel_from_portrait_images():
    home_page = _read("app/ui/pages/home_page.c")
    app_cmake = _read("app/CMakeLists.txt")

    assert "lv_obj_create(NULL)" in home_page
    assert "HOME_PAGE_BG_IMAGE_NAME" in home_page
    assert '"home_bg.png"' in home_page
    assert "HOME_PAGE_SETTINGS_ICON_NAME" in home_page
    assert '"icon_settings.png"' in home_page
    assert "ep_simple_recipe_open_saas2_db" in home_page
    assert "ep_simple_recipe_load_list" in home_page
    assert "portrait_image_url" in home_page
    assert "home_page_extract_url_filename" in home_page
    assert "ep_platform_lvgl_recipe_src" in home_page
    assert "home_page_wrap_index" in home_page
    assert "home_page_apply_carousel_layout" in home_page
    assert "HOME_PAGE_CAROUSEL_SLOT_COUNT" in home_page
    assert "#define HOME_PAGE_SCREEN_WIDTH 800" in home_page
    assert "#define HOME_PAGE_SCREEN_HEIGHT 480" in home_page
    assert "#define HOME_PAGE_HEADER_HEIGHT 96" in home_page
    assert "#define HOME_PAGE_MENU_HEIGHT 260" in home_page
    assert "#define HOME_PAGE_TITLE_HEIGHT 124" in home_page
    assert "#define HOME_PAGE_SIDE_SLOT_WIDTH 270" in home_page
    assert "#define HOME_PAGE_CENTER_SLOT_WIDTH 260" in home_page
    assert "#define HOME_PAGE_CENTER_SLOT_X 270" in home_page
    assert "#define HOME_PAGE_RIGHT_SLOT_X 530" in home_page
    assert "#define HOME_PAGE_SIDE_ITEM_SIZE 180" in home_page
    assert "#define HOME_PAGE_CENTER_ITEM_SIZE 260" in home_page
    assert "#define HOME_PAGE_LEFT_IMAGE_X 42" in home_page
    assert "#define HOME_PAGE_RIGHT_IMAGE_X 48" in home_page
    assert "#define HOME_PAGE_SETTINGS_SIZE 48" in home_page
    assert "lv_obj_remove_style_all(state->screen)" in home_page
    assert "lv_obj_set_pos(button, HOME_PAGE_SETTINGS_X, HOME_PAGE_SETTINGS_Y)" in home_page
    assert "HOME_PAGE_SELECTED_SCALE" in home_page
    assert "HOME_PAGE_SIDE_SCALE" in home_page
    assert "LV_EVENT_PRESSING" in home_page
    assert "LV_EVENT_RELEASED" in home_page
    assert "home_page_settings_clicked" in home_page
    assert "has_recipe" in home_page
    assert "slot->recipe_index == recipe_index" in home_page
    assert "slot->recipe_index = recipe_index" in home_page
    assert "home_page_apply_carousel_layout(home_page_state_t *state, bool refresh_content)" in home_page
    assert "if (refresh_content)" in home_page
    assert "home_page_apply_carousel_layout(state, false)" in home_page
    assert "home_page_apply_carousel_layout(state, true)" in home_page
    assert "EP_HOME_CAROUSEL_DISABLE_LIVE_SCALE" not in home_page

    assert "ep_components_recipe_parser" in app_cmake
    assert "ep_platform_api" in app_cmake


def test_home_page_preloads_offscreen_carousel_items_before_drag_commit():
    home_page = _read("app/ui/pages/home_page.c")

    assert "#define HOME_PAGE_CAROUSEL_SLOT_COUNT 5u" in home_page
    assert "#define HOME_PAGE_CENTER_SLOT 2u" in home_page
    assert "#define HOME_PAGE_FAR_LEFT_SLOT_X (-270)" in home_page
    assert "#define HOME_PAGE_FAR_RIGHT_SLOT_X 800" in home_page
    assert "center_index - 2" in home_page
    assert "center_index + 2" in home_page
    assert "home_page_set_slot_recipe(state, 0u, (size_t)far_left_index)" in home_page
    assert "home_page_set_slot_recipe(state, 4u, (size_t)far_right_index)" in home_page
    assert "for (size_t i = 0u; i < HOME_PAGE_CAROUSEL_SLOT_COUNT; ++i)" in home_page
    assert "slot->drag_weight * HOME_PAGE_WEIGHT_UNIT + visual_progress" in home_page
    assert "home_page_foreground_slot_index" in home_page


def test_home_page_uses_single_step_inertia_snap_after_release():
    home_page = _read("app/ui/pages/home_page.c")

    assert "#define HOME_PAGE_SNAP_ANIM_MS" in home_page
    assert "#define HOME_PAGE_RELEASE_VELOCITY_THRESHOLD" in home_page
    assert "lv_timer_t *snap_timer" in home_page
    assert "snap_start_offset" in home_page
    assert "snap_target_offset" in home_page
    assert "snap_target_step" in home_page
    assert "last_drag_x" in home_page
    assert "last_drag_tick" in home_page
    assert "release_velocity" in home_page
    assert "home_page_start_snap_animation" in home_page
    assert "home_page_snap_timer_cb" in home_page
    assert "lv_timer_create(home_page_snap_timer_cb" in home_page
    assert "lv_timer_del(state->snap_timer)" in home_page
    assert "home_page_finish_snap_animation(state)" in home_page
    assert "state->selected_index = (size_t)home_page_wrap_index((int)state->selected_index + state->snap_step_direction" in home_page
    assert "home_page_snap_step_for_release" in home_page
    assert "direction = home_page_snap_step_for_release(state)" in home_page
    assert "state->snap_step_direction = direction" in home_page
    assert "state->snap_target_step = direction" in home_page
    assert "return 1;" in home_page
    assert "return -1;" in home_page


def test_home_page_can_run_continuous_multiple_inertia_steps():
    home_page = _read("app/ui/pages/home_page.c")

    assert "#define HOME_PAGE_MAX_INERTIA_STEPS 3" in home_page
    assert "#define HOME_PAGE_FAST_RELEASE_VELOCITY_THRESHOLD" in home_page
    assert "#define HOME_PAGE_FLING_RELEASE_VELOCITY_THRESHOLD" in home_page
    assert "#define HOME_PAGE_SNAP_EXTRA_STEP_MS" in home_page
    assert "snap_total_steps" in home_page
    assert "snap_completed_steps" in home_page
    assert "snap_step_direction" in home_page
    assert "snap_start_progress" in home_page
    assert "snap_target_progress" in home_page
    assert "snap_duration_ms" in home_page
    assert "home_page_snap_steps_for_release" in home_page
    assert "home_page_apply_snap_progress" in home_page
    assert "home_page_snap_duration_for_steps" in home_page
    assert "while (state->snap_completed_steps < completed_steps)" in home_page
    assert "state->snap_completed_steps++" in home_page
    assert "home_page_clamp_i32(steps, 1, HOME_PAGE_MAX_INERTIA_STEPS)" in home_page
    assert "home_page_start_next_snap_step" not in home_page


def test_home_page_inertia_is_easy_to_trigger_and_fast():
    home_page = _read("app/ui/pages/home_page.c")

    assert "#define HOME_PAGE_SNAP_ANIM_MS 120u" in home_page
    assert "#define HOME_PAGE_SNAP_EXTRA_STEP_MS 45u" in home_page
    assert "#define HOME_PAGE_DISTANCE_SNAP_THRESHOLD 14" in home_page
    assert "#define HOME_PAGE_RELEASE_VELOCITY_THRESHOLD 160" in home_page
    assert "#define HOME_PAGE_FAST_RELEASE_VELOCITY_THRESHOLD 420" in home_page
    assert "#define HOME_PAGE_FLING_RELEASE_VELOCITY_THRESHOLD 760" in home_page


def test_home_page_keeps_last_nonzero_velocity_when_release_has_no_delta():
    home_page = _read("app/ui/pages/home_page.c")

    assert "HOME_PAGE_MIN_VELOCITY_SAMPLE_DELTA" in home_page
    assert "sample_delta = x - state->last_drag_x" in home_page
    assert "home_page_abs_i32(sample_delta) >= HOME_PAGE_MIN_VELOCITY_SAMPLE_DELTA" in home_page
    assert "state->release_velocity = (int32_t)(sample_delta * 1000 / (int32_t)elapsed)" in home_page
    update_sample = home_page[
        home_page.index("static void home_page_update_drag_sample") :
        home_page.index("static void home_page_carousel_event")
    ]
    sample_branch = update_sample[
        update_sample.index("if (state->last_drag_tick != 0u") :
        update_sample.index("} else if (elapsed > 160u)")
    ]
    assert "state->release_velocity = 0" not in sample_branch


def test_home_page_snap_back_with_no_direction_cannot_commit_loop():
    home_page = _read("app/ui/pages/home_page.c")

    assert "direction == 0 ? 0 : home_page_snap_steps_for_release(state)" in home_page
    assert "if (state->snap_total_steps == 0 && state->snap_step_direction == 0)" in home_page
    assert "state->snap_target_progress = 0" in home_page


def test_home_page_starting_snap_keeps_current_drag_offset_and_velocity():
    home_page = _read("app/ui/pages/home_page.c")

    assert "home_page_stop_snap_timer(state)" in home_page
    start_snap = home_page[
        home_page.index("static void home_page_start_snap_animation") :
        home_page.index("static void home_page_update_drag_sample")
    ]
    assert "home_page_cancel_snap_animation(state)" not in start_snap
    assert "home_page_reset_snap_state(state)" not in start_snap
    assert "state->snap_start_offset = state->drag_offset" in start_snap
    assert "direction = home_page_snap_step_for_release(state)" in start_snap


def test_home_page_snap_uses_directional_step_to_avoid_commit_jitter():
    home_page = _read("app/ui/pages/home_page.c")

    assert "home_page_visual_progress_for_offset" in home_page
    assert "home_page_visual_x_for_weight" in home_page
    assert "home_page_image_x_for_weight" in home_page
    assert "home_page_image_y_for_weight" in home_page
    assert "home_page_scale_for_weight" in home_page
    assert "slot->drag_weight * HOME_PAGE_WEIGHT_UNIT + visual_progress" in home_page
    assert "lv_obj_set_pos(slot->container, x, slot->base_y)" in home_page
    assert "HOME_PAGE_ITEM_STEP" not in home_page
    assert "HOME_PAGE_LEFT_SNAP_STEP" not in home_page
    assert "HOME_PAGE_RIGHT_SNAP_STEP" not in home_page


def test_app_ui_registers_home_page_through_page_manager():
    app_ui = _read("app/ui/app_ui.c")
    app_cmake = _read("app/CMakeLists.txt")

    assert '#include "page_manager.h"' in app_ui
    assert '#include "pages/app_pages.h"' in app_ui
    assert '#include "pages/home_page.h"' in app_ui
    assert "page_manager_init(NULL)" in app_ui
    assert "page_manager_register(APP_PAGE_HOME" in app_ui
    assert "page_manager_switch(APP_PAGE_HOME" in app_ui

    assert "ui/page_manager.c" in app_cmake
    assert "ui/pages/home_page.c" in app_cmake


def test_app_ui_registers_settings_page_and_home_can_navigate_to_it():
    app_ui = _read("app/ui/app_ui.c")
    app_pages = _read("app/ui/pages/app_pages.h")
    home_page = _read("app/ui/pages/home_page.c")
    settings_page = _read("app/ui/pages/settings_page.c")
    settings_header = _read("app/ui/pages/settings_page.h")
    app_cmake = _read("app/CMakeLists.txt")

    assert "APP_PAGE_SETTINGS" in app_pages
    assert '#include "pages/settings_page.h"' in app_ui
    assert "page_manager_register(APP_PAGE_SETTINGS" in app_ui
    assert "settings_page_create" in app_ui
    assert "settings_page_event" in app_ui

    assert "HOME_PAGE_SETTINGS_TEXT" in home_page
    assert "lv_button_create(screen)" in home_page
    assert "home_page_settings_clicked" in home_page
    assert "page_manager_switch(APP_PAGE_SETTINGS" in home_page

    assert "settings_page_create(page_manager_page_ctx_t *ctx)" in settings_page
    assert "SETTINGS_PAGE_TITLE_TEXT" in settings_page
    assert "SETTINGS_PAGE_BACK_TEXT" in settings_page
    assert "settings_page_back_clicked" in settings_page
    assert "page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180)" in settings_page
    assert "page_manager_switch(APP_PAGE_HOME" not in settings_page
    assert "settings_page_event(page_manager_page_ctx_t *ctx" in settings_header

    assert "ui/pages/settings_page.c" in app_cmake
