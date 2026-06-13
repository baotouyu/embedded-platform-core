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
    slot_block = home_page[
        home_page.index("static void home_page_create_slot") :
        home_page.index("static void home_page_create_carousel")
    ]

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
    assert "is_center ? ui_style_font(UI_STYLE_FONT_HOME_USER)" in slot_block
    assert "ui_style_font(UI_STYLE_FONT_DETAILS_MENU_TITLE)" in slot_block
    assert "UI_STYLE_FONT_HOME_CENTER" not in slot_block
    assert "EP_HOME_CAROUSEL_DISABLE_LIVE_SCALE" not in home_page

    assert "ep_components_recipe_parser" in app_cmake
    assert "ep_platform_api" in app_cmake


def test_home_page_uses_platform_recipe_db_path():
    home_page = _read("app/ui/pages/home_page.c")

    assert 'resources/host/recipe/recipelib.db' not in home_page
    assert 'HOME_PAGE_RECIPE_DB_NAME "recipelib.db"' in home_page
    assert "char recipe_db_path[160];" in home_page
    assert "ep_platform_recipe_path(HOME_PAGE_RECIPE_DB_NAME" in home_page
    assert "ep_simple_recipe_open_saas2_db(recipe_db_path, &store)" in home_page


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


def test_home_page_keeps_titles_visible_while_carousel_is_moving():
    home_page = _read("app/ui/pages/home_page.c")

    assert "labels_visible" not in home_page
    assert "home_page_set_carousel_labels_visible" not in home_page

    pressing = home_page[
        home_page.index("if (code == LV_EVENT_PRESSING && state->dragging)") :
        home_page.index("if (code == LV_EVENT_RELEASED && state->dragging)")
    ]
    assert "LV_OBJ_FLAG_HIDDEN" not in pressing

    finish_snap = home_page[
        home_page.index("static void home_page_finish_snap_animation") :
        home_page.index("static void home_page_apply_snap_progress")
    ]
    assert "LV_OBJ_FLAG_HIDDEN" not in finish_snap


def test_home_page_has_reference_positioned_user_switcher():
    home_page = _read("app/ui/pages/home_page.c")

    assert 'HOME_PAGE_USER_AVATAR_1_IMAGE_NAME "avatar_user_1.png"' in home_page
    assert "#define HOME_PAGE_SETTINGS_X 32" in home_page
    assert "#define HOME_PAGE_SETTINGS_Y 24" in home_page
    assert "#define HOME_PAGE_USER_AVATAR_X 677" in home_page
    assert "#define HOME_PAGE_USER_AVATAR_Y 24" in home_page
    assert "#define HOME_PAGE_USER_ARROW_X 749" in home_page
    assert "#define HOME_PAGE_USER_ARROW_Y 43" in home_page
    assert "#define HOME_PAGE_USER_DROPDOWN_X 399" in home_page
    assert "#define HOME_PAGE_USER_DROPDOWN_Y 112" in home_page
    assert "#define HOME_PAGE_USER_DROPDOWN_WIDTH 369" in home_page
    assert "#define HOME_PAGE_USER_DROPDOWN_HEIGHT 325" in home_page
    assert "#define HOME_PAGE_USER_DROPDOWN_RADIUS 12" in home_page
    assert "home_page_create_user_switcher(state)" in home_page


def test_home_page_user_switcher_toggles_dropdown_and_rows():
    home_page = _read("app/ui/pages/home_page.c")

    assert "lv_obj_t *user_dropdown_mask" in home_page
    assert "home_page_user_mask_clicked" in home_page
    assert "lv_obj_set_size(state->user_dropdown_mask, HOME_PAGE_SCREEN_WIDTH, HOME_PAGE_SCREEN_HEIGHT)" in home_page
    assert "lv_obj_add_event_cb(state->user_dropdown_mask, home_page_user_mask_clicked, LV_EVENT_CLICKED, state)" in home_page
    assert "lv_obj_clear_flag(state->user_dropdown_mask, LV_OBJ_FLAG_HIDDEN)" in home_page
    assert "lv_obj_move_foreground(state->user_dropdown_mask)" in home_page
    assert "lv_obj_add_flag(state->user_dropdown, LV_OBJ_FLAG_HIDDEN)" in home_page
    assert "lv_obj_clear_flag(state->user_dropdown, LV_OBJ_FLAG_HIDDEN)" in home_page
    assert "lv_obj_move_foreground(state->user_dropdown)" in home_page
    assert "lv_line_create(arrow)" in home_page
    assert "lv_line_set_points(arrow_line" in home_page
    assert "home_page_user_arrow_points" in home_page
    assert "home_page_toggle_user_dropdown" in home_page
    assert "home_page_user_row_clicked" in home_page
    assert "home_page_refresh_user_rows" in home_page
    assert "state->selected_user_index = 0u" in home_page
    assert "lv_obj_add_event_cb(button, home_page_toggle_user_dropdown, LV_EVENT_CLICKED, state)" in home_page
    assert "lv_obj_add_event_cb(row, home_page_user_row_clicked, LV_EVENT_CLICKED, state)" in home_page
    assert "lv_obj_add_event_cb(avatar_holder, home_page_user_row_clicked, LV_EVENT_CLICKED, state)" in home_page
    assert "lv_obj_add_event_cb(label, home_page_user_row_clicked, LV_EVENT_CLICKED, state)" in home_page
    assert "lv_event_get_current_target_obj(event)" in home_page
    assert "lv_obj_t *user_row_avatar_holders[HOME_PAGE_USER_COUNT]" in home_page
    assert "state->user_row_avatar_holders[i] == target" in home_page


def test_home_page_user_switcher_centers_row_content_and_uses_gray_internal_lines():
    home_page = _read("app/ui/pages/home_page.c")

    assert "#define HOME_PAGE_USER_DROPDOWN_BORDER_COLOR 0x666666" in home_page
    assert "#define HOME_PAGE_USER_ROW_BORDER_COLOR 0x666666" in home_page
    assert "#define HOME_PAGE_USER_ROW_CONTENT_WIDTH" in home_page
    assert "#define HOME_PAGE_USER_ROW_CONTENT_X ((HOME_PAGE_USER_DROPDOWN_WIDTH - HOME_PAGE_USER_ROW_CONTENT_WIDTH) / 2)" in home_page
    assert "lv_obj_t *user_row_content[HOME_PAGE_USER_COUNT]" in home_page
    assert "lv_obj_set_pos(content, HOME_PAGE_USER_ROW_CONTENT_X, HOME_PAGE_USER_ROW_CONTENT_Y)" in home_page
    assert "lv_obj_set_style_border_color(row, lv_color_hex(HOME_PAGE_USER_ROW_BORDER_COLOR), LV_PART_MAIN)" in home_page
    assert "lv_obj_set_style_border_side(row, LV_BORDER_SIDE_BOTTOM, LV_PART_MAIN)" in home_page
    assert "HOME_PAGE_USER_TEXT_X" not in home_page
    assert "HOME_PAGE_USER_ROW_AVATAR_X" not in home_page


def test_home_page_user_switcher_uses_requested_row_colors_and_resources():
    home_page = _read("app/ui/pages/home_page.c")
    user_dropdown_block = home_page[
        home_page.index("static void home_page_create_user_dropdown") :
        home_page.index("static void home_page_create_user_switcher")
    ]

    assert "HOME_PAGE_USER_SELECTED_COLOR 0xFFFFFF" in home_page
    assert "HOME_PAGE_USER_UNSELECTED_COLOR 0x2F2B29" in home_page
    assert 'HOME_PAGE_USER_AVATAR_1_IMAGE_NAME "avatar_user_1.png"' in home_page
    assert 'HOME_PAGE_USER_AVATAR_2_IMAGE_NAME "avatar_user_2.png"' in home_page
    assert 'HOME_PAGE_USER_AVATAR_3_IMAGE_NAME "avatar_user_3.png"' in home_page
    assert 'HOME_PAGE_USER_AVATAR_4_IMAGE_NAME "avatar_user_4.png"' in home_page
    assert "home_page_user_avatar_names[HOME_PAGE_USER_COUNT]" in home_page
    assert "ep_platform_lvgl_image_src(home_page_user_avatar_names[i]" in home_page
    assert "static const char *const home_page_user_names[HOME_PAGE_USER_COUNT]" in home_page
    assert '"用户1"' in home_page
    assert '"用户4"' in home_page
    assert "ui_style_font(UI_STYLE_FONT_HOME_SIDE)" in user_dropdown_block
    assert "ui_style_font(UI_STYLE_FONT_HOME_USER)" not in user_dropdown_block

    assert (REPO_ROOT / "resources/host/images/avatar_user_1.png").exists()
    assert (REPO_ROOT / "resources/host/images/avatar_user_2.png").exists()
    assert (REPO_ROOT / "resources/host/images/avatar_user_3.png").exists()
    assert (REPO_ROOT / "resources/host/images/avatar_user_4.png").exists()


def test_home_page_user_switcher_updates_top_avatar_after_selection():
    home_page = _read("app/ui/pages/home_page.c")

    assert "char user_avatar_src[HOME_PAGE_USER_COUNT][128]" in home_page
    assert "lv_obj_t *user_avatar_image" in home_page
    assert "home_page_refresh_selected_user_avatar(state)" in home_page
    assert "lv_image_set_src(state->user_avatar_image, state->user_avatar_src[state->selected_user_index])" in home_page


def test_app_ui_registers_home_page_through_page_manager():
    app_ui = _read("app/ui/app_ui.c")
    app_cmake = _read("app/CMakeLists.txt")
    app_pages = _read("app/ui/pages/app_pages.h")
    boot_page = _read("app/ui/pages/boot_page.c")

    assert '#include "page_manager.h"' in app_ui
    assert '#include "pages/app_pages.h"' in app_ui
    assert '#include "pages/boot_page.h"' in app_ui
    assert '#include "pages/home_page.h"' in app_ui
    assert "page_manager_init(NULL)" in app_ui
    assert "APP_PAGE_BOOT" in app_pages
    assert "page_manager_register(APP_PAGE_BOOT" in app_ui
    assert "boot_page_create" in app_ui
    assert "page_manager_register(APP_PAGE_HOME" in app_ui
    assert "page_manager_switch(APP_PAGE_BOOT" in app_ui
    assert "page_manager_switch(APP_PAGE_HOME" not in app_ui
    assert "boot_page_create(page_manager_page_ctx_t *ctx)" in boot_page

    assert "ui/page_manager.c" in app_cmake
    assert "ui/pages/boot_page.c" in app_cmake
    assert "ui/pages/home_page.c" in app_cmake


def test_boot_page_runs_logo_and_startup_sequence():
    boot_page = _read("app/ui/pages/boot_page.c")
    boot_header = _read("app/ui/pages/boot_page.h")
    export_cmake = _read("cmake/modules/ep_export_targets.cmake")
    host_cmake = _read("platforms/host/posix/CMakeLists.txt")

    assert "boot_page_create(page_manager_page_ctx_t *ctx)" in boot_header
    assert "BOOT_PAGE_BG_IMAGE_NAME" not in boot_page
    assert "#define BOOT_PAGE_LOGO_IMAGE_NAME \"boot_logo.png\"" in boot_page
    assert "#define BOOT_PAGE_SPINNER_IMAGE_NAME \"boot_loading.png\"" in boot_page
    assert "#define BOOT_PAGE_DONE_IMAGE_NAME \"boot_done.png\"" in boot_page
    assert "#define BOOT_PAGE_LOGO_DELAY_MS 2000u" in boot_page
    assert "#define BOOT_PAGE_STAGE_DELAY_MS 2000u" in boot_page
    assert "#define BOOT_PAGE_SPINNER_PERIOD_MS 80u" in boot_page
    assert "#define BOOT_PAGE_STAGE_COUNT 4u" in boot_page
    assert "#define BOOT_PAGE_STAGE_CARD_WIDTH 144" in boot_page
    assert "#define BOOT_PAGE_STAGE_CARD_HEIGHT 155" in boot_page
    assert "#define BOOT_PAGE_STAGE_CARD_RADIUS 16" in boot_page
    assert "#define BOOT_PAGE_STAGE_BORDER_COLOR 0x666666" in boot_page
    assert "#define BOOT_PAGE_STAGE_ICON_Y 24" in boot_page
    assert "#define BOOT_PAGE_STAGE_TEXT_CONTAINER_Y 94" in boot_page
    assert "boot_page_create_background" not in boot_page
    assert "ep_platform_lvgl_image_src(BOOT_PAGE_BG_IMAGE_NAME" not in boot_page
    assert "home_bg.png" not in boot_page
    assert "boot_bg.png" not in boot_page
    assert "lv_arc_create" not in boot_page
    assert "boot_page_create_bottom_arc" not in boot_page
    assert "stage_icon_holders[BOOT_PAGE_STAGE_COUNT]" in boot_page
    assert "lv_obj_set_pos(icon_holder, BOOT_PAGE_STAGE_ICON_X, BOOT_PAGE_STAGE_ICON_Y)" in boot_page
    assert "lv_obj_center(icon)" in boot_page
    assert "lv_image_set_pivot(icon, BOOT_PAGE_STAGE_ICON_SIZE / 2, BOOT_PAGE_STAGE_ICON_SIZE / 2)" in boot_page
    assert "lv_obj_set_pos(label_container, BOOT_PAGE_STAGE_TEXT_CONTAINER_X, BOOT_PAGE_STAGE_TEXT_CONTAINER_Y)" in boot_page
    assert "lv_obj_set_width(label, BOOT_PAGE_STAGE_TEXT_CONTAINER_WIDTH)" in boot_page
    assert "lv_obj_set_height(label, LV_SIZE_CONTENT)" in boot_page
    assert "lv_obj_center(label)" in boot_page
    assert "static const boot_stage_t boot_page_stages[]" in boot_page
    for label in ["自检", "加热", "清洗", "复位"]:
        assert label in boot_page
    assert "lv_timer_create(boot_page_timer_cb, BOOT_PAGE_LOGO_DELAY_MS" in boot_page
    assert "lv_timer_create(boot_page_spinner_timer_cb, BOOT_PAGE_SPINNER_PERIOD_MS" in boot_page
    assert "lv_timer_set_period(state->timer, BOOT_PAGE_STAGE_DELAY_MS)" in boot_page
    assert "lv_timer_reset(state->timer)" in boot_page
    assert "lv_image_set_rotation(state->stage_icons[state->active_stage], state->spinner_rotation)" in boot_page
    assert "boot_page_delete_spinner_timer(state)" in boot_page
    assert "lv_image_set_src(state->stage_icons[stage_index], state->done_src)" in boot_page
    assert "page_manager_switch(APP_PAGE_HOME, LV_SCR_LOAD_ANIM_NONE, 0, false)" in boot_page
    assert "lv_timer_del(state->timer)" in boot_page
    assert "app/ui/pages/boot_page.c" in export_cmake
    assert "app/ui/pages/boot_page.c" in host_cmake
    assert (REPO_ROOT / "resources/host/images/boot_logo.png").exists()
    assert (REPO_ROOT / "resources/host/images/boot_loading.png").exists()
    assert (REPO_ROOT / "resources/host/images/boot_done.png").exists()


def test_app_ui_registers_settings_page_and_home_can_navigate_to_it():
    app_ui = _read("app/ui/app_ui.c")
    app_pages = _read("app/ui/pages/app_pages.h")
    home_page = _read("app/ui/pages/home_page.c")
    settings_page = _read("app/ui/pages/settings_page.c")
    settings_header = _read("app/ui/pages/settings_page.h")
    app_cmake = _read("app/CMakeLists.txt")
    export_cmake = _read("cmake/modules/ep_export_targets.cmake")
    host_cmake = _read("platforms/host/posix/CMakeLists.txt")

    assert "APP_PAGE_SETTINGS" in app_pages
    assert '#include "pages/settings_page.h"' in app_ui
    assert "page_manager_register(APP_PAGE_SETTINGS" in app_ui
    assert "settings_page_create" in app_ui
    assert "settings_page_event" in app_ui
    assert "settings_page_destroy" in app_ui

    assert "HOME_PAGE_SETTINGS_TEXT" in home_page
    assert "lv_button_create(screen)" in home_page
    assert "home_page_settings_clicked" in home_page
    assert "page_manager_switch(APP_PAGE_SETTINGS" in home_page

    assert "settings_page_create(page_manager_page_ctx_t *ctx)" in settings_page
    assert "SETTINGS_PAGE_TITLE_KEY" in settings_page
    assert "SETTINGS_PAGE_BACK_ICON_NAME" in settings_page
    assert "settings_page_back_clicked" in settings_page
    assert "page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180)" in settings_page
    assert "page_manager_switch(APP_PAGE_HOME" not in settings_page
    assert "settings_page_event(page_manager_page_ctx_t *ctx" in settings_header
    assert "settings_page_destroy(page_manager_page_ctx_t *ctx" in settings_header

    assert "ui/pages/settings_page.c" in app_cmake
    assert "ui/pages/settings_common.c" in app_cmake
    assert "ui/pages/settings_language_page.c" in app_cmake
    assert "ui/pages/settings_sleep_page.c" in app_cmake
    assert "ui/pages/settings_brightness_page.c" in app_cmake
    assert "ui/pages/settings_details_page.c" in app_cmake
    assert "ui/pages/settings_cleaning_page.c" in app_cmake
    for source in [
        "app/ui/pages/settings_common.c",
        "app/ui/pages/running_page.c",
        "app/ui/pages/settings_language_page.c",
        "app/ui/pages/settings_sleep_page.c",
        "app/ui/pages/settings_brightness_page.c",
        "app/ui/pages/settings_details_page.c",
        "app/ui/pages/settings_cleaning_page.c",
    ]:
        assert source in export_cmake
        assert source in host_cmake


def test_settings_page_matches_reference_layout_and_resources():
    settings_page = _read("app/ui/pages/settings_page.c")
    settings_common = _read("app/ui/pages/settings_common.c")
    settings_common_header = _read("app/ui/pages/settings_common.h")
    app_cmake = _read("app/CMakeLists.txt")
    title_block = settings_page[
        settings_page.index("static bool settings_page_create_title") :
        settings_page.index("static bool settings_page_create_back_button")
    ]
    button_block = settings_page[
        settings_page.index("static bool settings_page_create_button(") :
        settings_page.index("static bool settings_page_create_buttons")
    ]

    assert '#include "ep_platform_paths.h"' in settings_page
    assert '#include "multi_lang.h"' in settings_page
    assert '#include "ui_style.h"' in settings_page
    assert "#define SETTINGS_PAGE_SCREEN_WIDTH 800" in settings_common_header
    assert "#define SETTINGS_PAGE_SCREEN_HEIGHT 480" in settings_common_header
    assert "#define SETTINGS_PAGE_CONTENT_HEIGHT 696" in settings_page
    assert "#define SETTINGS_PAGE_BACK_X 32" in settings_common_header
    assert "#define SETTINGS_PAGE_BACK_Y 32" in settings_common_header
    assert "#define SETTINGS_PAGE_BACK_SIZE 48" in settings_common_header
    assert "#define SETTINGS_PAGE_TITLE_Y 48" in settings_page
    assert "#define SETTINGS_PAGE_BUTTON_CONTAINER_Y 140" in settings_page
    assert "#define SETTINGS_PAGE_BUTTON_CONTAINER_HEIGHT (SETTINGS_PAGE_SCREEN_HEIGHT - SETTINGS_PAGE_BUTTON_CONTAINER_Y)" in settings_page
    assert "#define SETTINGS_PAGE_BUTTON_CONTENT_HEIGHT (SETTINGS_PAGE_CONTENT_HEIGHT - SETTINGS_PAGE_BUTTON_CONTAINER_Y)" in settings_page
    assert "#define SETTINGS_PAGE_BUTTON_WIDTH 356" in settings_page
    assert "#define SETTINGS_PAGE_BUTTON_HEIGHT 112" in settings_page
    assert "#define SETTINGS_PAGE_BUTTON_RADIUS 56" in settings_page
    assert "#define SETTINGS_PAGE_BUTTON_GAP_X 40" in settings_page
    assert "#define SETTINGS_PAGE_BUTTON_GAP_Y 24" in settings_page
    assert "#define SETTINGS_PAGE_LEFT_X 24" in settings_page
    assert "#define SETTINGS_PAGE_RIGHT_X (SETTINGS_PAGE_LEFT_X + SETTINGS_PAGE_BUTTON_WIDTH + SETTINGS_PAGE_BUTTON_GAP_X)" in settings_page
    assert "#define SETTINGS_PAGE_ROW_0_Y 0" in settings_page
    assert "#define SETTINGS_PAGE_ROW_STEP (SETTINGS_PAGE_BUTTON_HEIGHT + SETTINGS_PAGE_BUTTON_GAP_Y)" in settings_page
    assert "#define SETTINGS_PAGE_ICON_SIZE 80" in settings_page
    assert "#define SETTINGS_PAGE_BUTTON_COLOR 0x2F2B29" in settings_common_header
    assert "#define SETTINGS_PAGE_BUTTON_BORDER_COLOR 0x666666" in settings_page

    assert "typedef struct {" in settings_page
    assert "settings_page_button_spec_t" in settings_page
    assert "settings_page_items[]" in settings_page
    assert 'SETTINGS_PAGE_LANG_DB_NAME "recipelib.db"' in settings_page
    assert 'SETTINGS_PAGE_LANGUAGE "zh-CN"' in settings_page
    assert "multi_lang_open_db(" in settings_page
    assert "multi_lang_set_language(" in settings_page
    assert "multi_lang_get_text(" in settings_page
    assert "multi_lang_close(" in settings_page
    assert "lv_obj_clear_flag(screen, LV_OBJ_FLAG_SCROLLABLE)" in settings_common
    assert "lv_obj_set_scroll_dir(container, LV_DIR_VER)" in settings_page
    assert "lv_obj_set_scrollbar_mode(container, LV_SCROLLBAR_MODE_OFF)" in settings_page
    assert "lv_obj_set_size(container, SETTINGS_PAGE_SCREEN_WIDTH, SETTINGS_PAGE_BUTTON_CONTAINER_HEIGHT)" in settings_page
    assert "lv_obj_set_pos(container, 0, SETTINGS_PAGE_BUTTON_CONTAINER_Y)" in settings_page
    assert "settings_page_create_scroll_spacer(state)" in settings_page
    assert "lv_obj_set_pos(button, spec->x, spec->y)" in settings_page
    assert "ep_platform_lvgl_image_src(spec->icon_name" in settings_page
    assert "ui_style_font(UI_STYLE_FONT_HOME_USER)" in title_block
    assert "ui_style_font(UI_STYLE_FONT_HOME_CENTER)" not in title_block
    assert "ui_style_font(UI_STYLE_FONT_HOME_SIDE)" in button_block
    assert "ui_style_font(UI_STYLE_FONT_HOME_USER)" not in button_block

    for key in [
        "MULTI_LANG_KEY_SETTING",
        "MULTI_LANG_KEY_LANGUAGE",
        "MULTI_LANG_KEY_WIFI",
        "MULTI_LANG_KEY_BRIGHTNESS",
        "MULTI_LANG_KEY_ON",
        "MULTI_LANG_KEY_RINSE",
        "MULTI_LANG_KEY_SLEEP",
        "MULTI_LANG_KEY_APP_LINK",
        "MULTI_LANG_KEY_DETAILS",
    ]:
        assert key in settings_page

    for text in ["设置", "语言", "亮度", "开", "清洗", "休眠", "关联", "详细信息"]:
        assert f'"{text}"' not in settings_page

    settings_page_icons = [
        "settings_icon_language.png",
        "settings_icon_wifi.png",
        "settings_icon_brightness.png",
        "settings_icon_volume.png",
        "settings_icon_clean.png",
        "settings_icon_sleep.png",
        "settings_icon_app_link.png",
        "settings_icon_info.png",
    ]
    for icon_name in settings_page_icons:
        assert f'"{icon_name}"' in settings_page
        assert (REPO_ROOT / "resources/host/images" / icon_name).exists()

    shared_icons = [
        "settings_icon_back.png",
        "settings_icon_confirm.png",
    ]
    for icon_name in shared_icons:
        assert f'"{icon_name}"' in settings_common_header
        assert (REPO_ROOT / "resources/host/images" / icon_name).exists()

    assert "components/multi_lang/include" in app_cmake
    assert "ep_components_multi_lang" in app_cmake
    assert "settings_selection_list_create(" not in settings_page
    assert "settings_language_page_create" not in settings_page
    assert "settings_sleep_page_create" not in settings_page


def test_language_page_is_registered_and_reachable():
    app_pages = _read("app/ui/pages/app_pages.h")
    app_ui = _read("app/ui/app_ui.c")
    settings_page = _read("app/ui/pages/settings_page.c")
    language_page = _read("app/ui/pages/settings_language_page.c")

    assert "APP_PAGE_LANGUAGE" in app_pages
    assert "page_manager_register(APP_PAGE_LANGUAGE" in app_ui
    assert "settings_language_page_create" in app_ui
    assert "page_manager_switch(APP_PAGE_LANGUAGE" in settings_page
    assert "SETTINGS_PAGE_ACTION_LANGUAGE" in settings_page
    assert "settings_language_page_create(page_manager_page_ctx_t *ctx)" in language_page


def test_settings_selection_list_reusable_metrics_and_language_options():
    common = _read("app/ui/pages/settings_common.c")
    common_header = _read("app/ui/pages/settings_common.h")
    language_page = _read("app/ui/pages/settings_language_page.c")

    assert "#define SETTINGS_SELECTION_LIST_WIDTH 369" in common_header
    assert "#define SETTINGS_SELECTION_LIST_ROW_HEIGHT 64" in common_header
    assert "#define SETTINGS_SELECTION_LIST_RADIUS 12" in common_header
    assert "#define SETTINGS_SELECTION_LIST_Y 160" in common_header
    assert "#define SETTINGS_SELECTION_LIST_UNSELECTED_COLOR SETTINGS_PAGE_BUTTON_COLOR" in common_header
    assert "#define SETTINGS_PAGE_BUTTON_COLOR 0x2F2B29" in common_header
    assert "settings_selection_list_create(" in common
    assert "settings_common_create_title(" in common
    assert "ui_style_font(UI_STYLE_FONT_HOME_SIDE)" in common
    assert "ui_style_font(UI_STYLE_FONT_HOME_USER)" in common
    assert "ui_style_font(UI_STYLE_FONT_HOME_CENTER)" not in common
    assert "#define SETTINGS_LANGUAGE_TITLE_TEXT \"语言\"" in language_page
    assert "settings_language_create_title(state)" in language_page
    assert "settings_common_create_title(state->screen, SETTINGS_LANGUAGE_TITLE_TEXT)" in language_page
    assert "ui_style_font(UI_STYLE_FONT_HOME_CENTER)" not in language_page
    assert "settings_selection_option_index(settings_language_options" in language_page
    assert "SETTINGS_PAGE_LANGUAGE)" in language_page
    assert "settings_language_options[]" in language_page
    for label in ["English", "简体中文", "Français", "Italiano", "Deutsch", "Русский"]:
        assert label in language_page


def test_language_page_confirm_and_back_return_to_settings():
    language_page = _read("app/ui/pages/settings_language_page.c")

    assert "settings_language_back_clicked" in language_page
    assert "settings_language_confirm_clicked" in language_page
    assert language_page.count("page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180)") >= 2


def test_sleep_page_is_registered_and_reachable():
    app_pages = _read("app/ui/pages/app_pages.h")
    app_ui = _read("app/ui/app_ui.c")
    settings_page = _read("app/ui/pages/settings_page.c")
    sleep_page = _read("app/ui/pages/settings_sleep_page.c")

    assert "APP_PAGE_SLEEP" in app_pages
    assert "page_manager_register(APP_PAGE_SLEEP" in app_ui
    assert "settings_sleep_page_create" in app_ui
    assert "page_manager_switch(APP_PAGE_SLEEP" in settings_page
    assert "SETTINGS_PAGE_ACTION_SLEEP" in settings_page
    assert "settings_sleep_page_create(page_manager_page_ctx_t *ctx)" in sleep_page


def test_sleep_page_reuses_selection_list_with_sleep_options():
    sleep_page = _read("app/ui/pages/settings_sleep_page.c")

    assert "#define SETTINGS_SLEEP_TITLE_TEXT \"休眠\"" in sleep_page
    assert "settings_sleep_options[]" in sleep_page
    assert "settings_sleep_default_index" in sleep_page
    assert "SETTINGS_SLEEP_DEFAULT_VALUE" in sleep_page
    assert "#define SETTINGS_SLEEP_VISIBLE_ROWS 4" in sleep_page
    assert "settings_sleep_create_title(state)" in sleep_page
    assert "settings_common_create_title(state->screen, SETTINGS_SLEEP_TITLE_TEXT)" in sleep_page
    assert "ui_style_font(UI_STYLE_FONT_HOME_CENTER)" not in sleep_page
    assert "settings_selection_option_index(settings_sleep_options" in sleep_page
    for label in ["10mins", "30mins", "1h", "2h"]:
        assert label in sleep_page
    assert "settings_sleep_back_clicked" in sleep_page
    assert "settings_sleep_confirm_clicked" in sleep_page
    assert "SETTINGS_SLEEP_VISIBLE_ROWS))" in sleep_page
    assert "settings_selection_list_create(screen" in sleep_page


def test_brightness_page_is_registered_and_reachable():
    app_pages = _read("app/ui/pages/app_pages.h")
    app_ui = _read("app/ui/app_ui.c")
    settings_page = _read("app/ui/pages/settings_page.c")
    brightness_page = _read("app/ui/pages/settings_brightness_page.c")

    assert "APP_PAGE_BRIGHTNESS" in app_pages
    assert "page_manager_register(APP_PAGE_BRIGHTNESS" in app_ui
    assert "settings_brightness_page_create" in app_ui
    assert "page_manager_switch(APP_PAGE_BRIGHTNESS" in settings_page
    assert "SETTINGS_PAGE_ACTION_BRIGHTNESS" in settings_page
    assert "settings_brightness_page_create(page_manager_page_ctx_t *ctx)" in brightness_page


def test_brightness_page_matches_reference_layout_and_resources():
    brightness_page = _read("app/ui/pages/settings_brightness_page.c")
    title_block = brightness_page[
        brightness_page.index("static bool settings_brightness_create_title") :
        brightness_page.index("static bool settings_brightness_create_icon_button")
    ]

    assert "#define SETTINGS_BRIGHTNESS_TITLE_X 372" in brightness_page
    assert "#define SETTINGS_BRIGHTNESS_TITLE_Y 90" in brightness_page
    assert "#define SETTINGS_BRIGHTNESS_CONTROL_X 166" in brightness_page
    assert "#define SETTINGS_BRIGHTNESS_CONTROL_Y 230" in brightness_page
    assert "#define SETTINGS_BRIGHTNESS_CONTROL_WIDTH 524" in brightness_page
    assert "#define SETTINGS_BRIGHTNESS_SEGMENT_COUNT 5u" in brightness_page
    assert "#define SETTINGS_BRIGHTNESS_SEGMENT_BORDER_WIDTH 3" in brightness_page
    assert "#define SETTINGS_BRIGHTNESS_DEFAULT_INDEX 0u" in brightness_page
    assert "settings_brightness_min_icon.png" in brightness_page
    assert "settings_brightness_max_icon.png" in brightness_page
    assert "settings_brightness_level_clicked" in brightness_page
    assert "settings_brightness_create_levels(control, state)" in brightness_page
    assert "i <= state->selected_index" in brightness_page
    assert "ui_style_font(UI_STYLE_FONT_HOME_USER)" in title_block
    assert "ui_style_font(UI_STYLE_FONT_HOME_CENTER)" not in title_block

    assert (REPO_ROOT / "resources/host/images/settings_brightness_min_icon.png").exists()
    assert (REPO_ROOT / "resources/host/images/settings_brightness_max_icon.png").exists()


def test_details_page_is_registered_and_reachable():
    app_pages = _read("app/ui/pages/app_pages.h")
    app_ui = _read("app/ui/app_ui.c")
    settings_page = _read("app/ui/pages/settings_page.c")
    settings_header = _read("app/ui/pages/settings_page.h")
    details_page = _read("app/ui/pages/settings_details_page.c")

    assert "APP_PAGE_DETAILS" in app_pages
    assert "page_manager_register(APP_PAGE_DETAILS" in app_ui
    assert "settings_details_page_create" in app_ui
    assert "settings_details_page_create(page_manager_page_ctx_t *ctx)" in settings_header
    assert "settings_details_page_destroy(page_manager_page_ctx_t *ctx)" in settings_header
    assert "settings_details_page_event(page_manager_page_ctx_t *ctx" in settings_header
    assert "page_manager_switch(APP_PAGE_DETAILS" in settings_page
    assert "SETTINGS_PAGE_ACTION_DETAILS" in settings_page
    assert "settings_details_page_create(page_manager_page_ctx_t *ctx)" in details_page


def test_cleaning_page_is_registered_and_reachable():
    app_pages = _read("app/ui/pages/app_pages.h")
    app_ui = _read("app/ui/app_ui.c")
    settings_page = _read("app/ui/pages/settings_page.c")
    settings_header = _read("app/ui/pages/settings_page.h")
    cleaning_page = _read("app/ui/pages/settings_cleaning_page.c")

    assert "APP_PAGE_CLEANING" in app_pages
    assert "page_manager_register(APP_PAGE_CLEANING" in app_ui
    assert "settings_cleaning_page_create" in app_ui
    assert "settings_cleaning_page_create(page_manager_page_ctx_t *ctx)" in settings_header
    assert "settings_cleaning_page_destroy(page_manager_page_ctx_t *ctx)" in settings_header
    assert "settings_cleaning_page_event(page_manager_page_ctx_t *ctx" in settings_header
    assert "page_manager_switch(APP_PAGE_CLEANING" in settings_page
    assert "SETTINGS_PAGE_ACTION_CLEAN" in settings_page
    assert "settings_cleaning_page_create(page_manager_page_ctx_t *ctx)" in cleaning_page


def test_cleaning_page_matches_details_style_layout():
    cleaning_page = _read("app/ui/pages/settings_cleaning_page.c")
    title_block = cleaning_page[
        cleaning_page.index("static bool settings_cleaning_create_title") :
        cleaning_page.index("static bool settings_cleaning_create_action_button")
    ]

    assert "#define SETTINGS_CLEANING_TITLE_TEXT \"清洗\"" in cleaning_page
    assert "#define SETTINGS_CLEANING_HEADER_HEIGHT 96" in cleaning_page
    assert "#define SETTINGS_CLEANING_MENU_WIDTH 240" in cleaning_page
    assert "#define SETTINGS_CLEANING_MENU_ITEM_COUNT 3u" in cleaning_page
    assert "#define SETTINGS_CLEANING_MENU_ROW_HEIGHT 64" in cleaning_page
    assert "#define SETTINGS_CLEANING_MENU_SELECTED_COLOR 0x000000" in cleaning_page
    assert "#define SETTINGS_CLEANING_MENU_UNSELECTED_COLOR SETTINGS_PAGE_BUTTON_COLOR" in cleaning_page
    assert "#define SETTINGS_CLEANING_CONTENT_X SETTINGS_CLEANING_MENU_WIDTH" in cleaning_page
    assert "#define SETTINGS_CLEANING_CONTENT_WIDTH 560" in cleaning_page
    assert "#define SETTINGS_CLEANING_CONTENT_HEIGHT 384" in cleaning_page
    assert "#define SETTINGS_CLEANING_CARD_WIDTH 496" in cleaning_page
    assert "#define SETTINGS_CLEANING_CARD_HEIGHT 72" in cleaning_page
    assert "#define SETTINGS_CLEANING_CARD_RADIUS 12" in cleaning_page
    assert "#define SETTINGS_CLEANING_ACTION_BUTTON_COLOR 0xB56A2E" in cleaning_page
    assert "#define SETTINGS_CLEANING_LEVEL_GROUP_WIDTH 416" in cleaning_page
    assert "#define SETTINGS_CLEANING_LEVEL_GROUP_HEIGHT 32" in cleaning_page
    assert "#define SETTINGS_CLEANING_LEVEL_ICON_AREA_WIDTH 44" in cleaning_page
    assert "#define SETTINGS_CLEANING_LEVEL_TRACK_WIDTH 304" in cleaning_page
    assert "#define SETTINGS_CLEANING_LEVEL_TRACK_HEIGHT 10" in cleaning_page
    assert "#define SETTINGS_CLEANING_LEVEL_KNOB_SIZE 30" in cleaning_page
    assert "#define SETTINGS_CLEANING_LEVEL_MAX_LABEL_WIDTH 68" in cleaning_page
    assert "settings_cleaning_create_menu" in cleaning_page
    assert "settings_cleaning_create_content" in cleaning_page
    assert "settings_cleaning_refresh_menu" in cleaning_page
    assert "settings_common_create_icon_button(screen" in cleaning_page
    assert "UI_STYLE_FONT_HOME_USER" in title_block
    assert "UI_STYLE_FONT_DETAILS_MENU_TITLE" in cleaning_page
    assert "UI_STYLE_FONT_DETAILS_MENU_VALUE" in cleaning_page

    for text in [
        "日常清洗",
        "机器维护清洁",
        "除垢等级",
        "冲泡器简易清洗",
        "奶泡器简易清洗",
        "奶泡器深度清洗",
        "冲泡器深度清洁（加药片）",
        "奶泡器深度清洁（加药片）",
        "除垢",
        "立即除垢",
        "2级",
        "5级",
    ]:
        assert text in cleaning_page


def test_cleaning_page_daily_maintenance_and_descaling_content():
    cleaning_page = _read("app/ui/pages/settings_cleaning_page.c")
    daily_block = cleaning_page[
        cleaning_page.index("static bool settings_cleaning_create_daily_clean") :
        cleaning_page.index("static bool settings_cleaning_create_maintenance_clean")
    ]
    maintenance_block = cleaning_page[
        cleaning_page.index("static bool settings_cleaning_create_maintenance_clean") :
        cleaning_page.index("static bool settings_cleaning_create_descaling_level")
    ]
    progress_block = cleaning_page[
        cleaning_page.index("static bool settings_cleaning_create_descaling_progress") :
        cleaning_page.index("static bool settings_cleaning_create_descaling_level")
    ]
    descaling_block = cleaning_page[
        cleaning_page.index("static bool settings_cleaning_create_descaling_level") :
        cleaning_page.index("static bool settings_cleaning_create_content_for_tab")
    ]

    assert "SETTINGS_CLEANING_TAB_DAILY" in cleaning_page
    assert "SETTINGS_CLEANING_TAB_MAINTENANCE" in cleaning_page
    assert "SETTINGS_CLEANING_TAB_DESCALING_LEVEL" in cleaning_page
    assert "settings_cleaning_daily_items[]" in cleaning_page
    assert "settings_cleaning_maintenance_items[]" in cleaning_page
    assert "settings_cleaning_create_clean_card" in cleaning_page
    assert "sizeof(settings_cleaning_daily_items) / sizeof(settings_cleaning_daily_items[0])" in daily_block
    assert "sizeof(settings_cleaning_maintenance_items) / sizeof(settings_cleaning_maintenance_items[0])" in maintenance_block
    assert "settings_cleaning_create_clean_card(state, &settings_cleaning_daily_items[i], i)" in daily_block
    assert "settings_cleaning_create_clean_card(state, &settings_cleaning_maintenance_items[i], i)" in maintenance_block
    assert "settings_cleaning_create_descaling_progress" in descaling_block
    assert "settings_cleaning_create_descaling_progress_group" in cleaning_page
    assert "lv_slider_create" not in cleaning_page
    assert "LV_PART_KNOB" not in cleaning_page
    assert "LV_PART_INDICATOR" not in cleaning_page
    assert "descaling_level" in cleaning_page
    assert "descaling_progress_fill" in cleaning_page
    assert "descaling_knob" in cleaning_page
    assert "descaling_value_label" in cleaning_page
    assert "settings_cleaning_level_for_point" in cleaning_page
    assert "settings_cleaning_set_descaling_level" in cleaning_page
    assert "settings_cleaning_descaling_progress_event" in cleaning_page
    assert "lv_indev_get_point(lv_indev_active(), &point)" in cleaning_page
    assert "lv_obj_add_event_cb(group, settings_cleaning_descaling_progress_event, LV_EVENT_PRESSED, state)" in cleaning_page
    assert "lv_obj_add_event_cb(group, settings_cleaning_descaling_progress_event, LV_EVENT_PRESSING, state)" in cleaning_page
    assert "lv_obj_add_event_cb(track, settings_cleaning_descaling_progress_event, LV_EVENT_PRESSED, state)" in cleaning_page
    assert "lv_obj_add_event_cb(knob, settings_cleaning_descaling_progress_event, LV_EVENT_PRESSING, state)" in cleaning_page
    assert "lv_label_set_text_fmt(state->descaling_value_label, \"%d级\", state->descaling_level)" in cleaning_page
    assert "SETTINGS_CLEANING_LEVEL_PROGRESS_WIDTH" in cleaning_page
    assert "SETTINGS_CLEANING_LEVEL_KNOB_X" in cleaning_page
    assert "SETTINGS_CLEANING_MAINTENANCE_DESCALING_ICON_NAME \"settings_details_descaling_icon.png\"" in cleaning_page
    assert "settings_cleaning_descaling_icon.png" in cleaning_page
    assert "settings_details_descaling_icon.png" in cleaning_page
    assert "settings_icon_clean.png" in cleaning_page
    assert "SETTINGS_CLEANING_LEVEL_GOLD_COLOR" in cleaning_page
    assert "settings_cleaning_create_gold_label" in progress_block
    assert (
        "SETTINGS_CLEANING_LEVEL_MAX_LABEL_WIDTH,\n"
        "                                            SETTINGS_CLEANING_LEVEL_MAX_LABEL_HEIGHT,\n"
        "                                            UI_STYLE_FONT_DETAILS_MENU_VALUE,\n"
        "                                            LV_TEXT_ALIGN_CENTER"
    ) in progress_block
    assert "lv_obj_add_event_cb(row, settings_cleaning_menu_row_clicked" in cleaning_page
    assert "settings_cleaning_create_content_for_tab(state)" in cleaning_page
    assert (REPO_ROOT / "resources/host/images/settings_cleaning_descaling_icon.png").exists()
    assert (REPO_ROOT / "resources/host/images/settings_details_descaling_icon.png").exists()


def test_cleaning_page_quick_rinse_status_flow():
    cleaning_page = _read("app/ui/pages/settings_cleaning_page.c")
    daily_block = cleaning_page[
        cleaning_page.index("static const settings_cleaning_action_item_t settings_cleaning_daily_items[]") :
        cleaning_page.index("static const settings_cleaning_action_item_t settings_cleaning_maintenance_items[]")
    ]
    status_block = cleaning_page[
        cleaning_page.index("static bool settings_cleaning_create_rinse_status") :
        cleaning_page.index("static bool settings_cleaning_create_daily_clean")
    ]

    assert "#define SETTINGS_CLEANING_RINSE_DURATION_MS 10000u" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_TICK_MS 1000u" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_RETURN_DELAY_MS 1000u" in cleaning_page
    assert "SETTINGS_CLEANING_RINSE_COMPLETE_ICON_NAME \"Frame-2.png\"" in cleaning_page
    assert "SETTINGS_CLEANING_RINSE_INTERRUPTED_ICON_NAME \"Frame-3.png\"" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_PAGE_WIDTH SETTINGS_PAGE_SCREEN_WIDTH" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_PAGE_HEIGHT SETTINGS_PAGE_SCREEN_HEIGHT" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_BUTTON_WIDTH 236" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_BUTTON_HEIGHT 74" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_BUTTON_X 482" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_BUTTON_Y 203" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_BUTTON_LABEL_X 34" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_BUTTON_LABEL_WIDTH 132" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_RUNNING_LABEL_X 0" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_RUNNING_LABEL_WIDTH SETTINGS_CLEANING_RINSE_BUTTON_WIDTH" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_HELPER_X 540" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_HELPER_Y 139" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_STATUS_ICON_X 168" in cleaning_page
    assert "#define SETTINGS_CLEANING_RINSE_STATUS_ICON_Y 20" in cleaning_page
    assert "settings_cleaning_create_rinse_graphic" not in cleaning_page
    assert "SETTINGS_CLEANING_RINSE_GRAPHIC" not in cleaning_page
    assert "lv_arc_create" not in cleaning_page
    assert "{\"冲泡器简易清洗\", \"清洗\", SETTINGS_CLEANING_CARD_ICON_NAME, true, false, false, NULL," in daily_block
    assert "{\"奶泡器简易清洗\", \"清洗\", SETTINGS_CLEANING_CARD_ICON_NAME, true, false, false, NULL," in daily_block
    assert "{\"奶泡器深度清洗\", \"立即除垢\", SETTINGS_CLEANING_CARD_ICON_NAME, false, true, false, NULL," in daily_block
    assert "settings_cleaning_create_clean_card(state, &settings_cleaning_daily_items[i], i)" in cleaning_page
    assert "lv_obj_add_event_cb(card, settings_cleaning_quick_rinse_clicked, LV_EVENT_CLICKED, state)" in cleaning_page
    assert "lv_obj_add_event_cb(button, settings_cleaning_quick_rinse_clicked, LV_EVENT_CLICKED, state)" in cleaning_page
    assert "settings_cleaning_start_quick_rinse(state)" in cleaning_page
    assert "state->rinse_overlay = lv_obj_create(state->screen)" in status_block
    assert "lv_obj_set_size(state->rinse_overlay, SETTINGS_CLEANING_RINSE_PAGE_WIDTH, SETTINGS_CLEANING_RINSE_PAGE_HEIGHT)" in status_block
    assert "lv_obj_set_style_bg_color(state->rinse_overlay, lv_color_hex(SETTINGS_PAGE_BG_COLOR), LV_PART_MAIN)" in status_block
    assert "state->rinse_timer = lv_timer_create(settings_cleaning_rinse_timer_cb" in cleaning_page
    assert "settings_cleaning_schedule_rinse_return(state)" in cleaning_page
    assert "settings_cleaning_rinse_return_timer_cb" in cleaning_page
    assert "lv_timer_set_cb(state->rinse_timer, settings_cleaning_rinse_return_timer_cb)" in cleaning_page
    assert "lv_timer_set_period(state->rinse_timer, SETTINGS_CLEANING_RINSE_RETURN_DELAY_MS)" in cleaning_page
    assert "lv_timer_reset(state->rinse_timer)" in cleaning_page
    assert "lv_timer_set_repeat_count(state->rinse_timer, 1)" in cleaning_page
    assert "SETTINGS_CLEANING_RINSE_TICK_MS" in status_block
    assert "lv_timer_set_repeat_count(state->rinse_timer, -1)" in cleaning_page
    assert "settings_cleaning_stop_rinse_timer(state)" in cleaning_page
    assert "settings_cleaning_set_rinse_status(state, SETTINGS_CLEANING_RINSE_RUNNING, 0)" in cleaning_page
    assert "settings_cleaning_set_rinse_status(state, SETTINGS_CLEANING_RINSE_COMPLETE, 100)" in cleaning_page
    assert "settings_cleaning_set_rinse_status(state, SETTINGS_CLEANING_RINSE_INTERRUPTED, state->rinse_progress)" in cleaning_page
    assert "settings_cleaning_set_rinse_final_layout(state, false)" in cleaning_page
    assert "settings_cleaning_set_rinse_final_layout(state, true)" in cleaning_page
    assert "lv_obj_set_width(state->rinse_button_label, SETTINGS_CLEANING_RINSE_RUNNING_LABEL_WIDTH)" in cleaning_page
    assert "lv_obj_set_x(state->rinse_button_label, SETTINGS_CLEANING_RINSE_RUNNING_LABEL_X)" in cleaning_page
    assert "lv_obj_set_width(state->rinse_button_label, SETTINGS_CLEANING_RINSE_BUTTON_LABEL_WIDTH)" in cleaning_page
    assert "lv_obj_set_x(state->rinse_button_label, SETTINGS_CLEANING_RINSE_BUTTON_LABEL_X)" in cleaning_page
    assert "state->rinse_icon = lv_image_create(button)" in cleaning_page
    assert "lv_obj_set_pos(state->rinse_icon, SETTINGS_CLEANING_RINSE_STATUS_ICON_X, SETTINGS_CLEANING_RINSE_STATUS_ICON_Y)" in cleaning_page
    assert (
        "SETTINGS_CLEANING_RINSE_BUTTON_LABEL_X,\n"
        "                                                               SETTINGS_CLEANING_RINSE_BUTTON_LABEL_Y,\n"
        "                                                               SETTINGS_CLEANING_RINSE_BUTTON_LABEL_WIDTH,"
    ) in cleaning_page
    assert "state->rinse_icon = lv_image_create(state->rinse_overlay)" not in cleaning_page
    assert "lv_label_set_text_fmt(state->rinse_button_label, \"清洗中 %d %%\", state->rinse_progress)" in cleaning_page
    assert "lv_label_set_text(state->rinse_button_label, \"清洗完成\")" in cleaning_page
    assert "lv_label_set_text(state->rinse_button_label, \"清洗中断\")" in cleaning_page
    assert "请返回重试" in cleaning_page
    assert "UI_STYLE_FONT_DETAILS_MODAL" in status_block
    assert "UI_STYLE_FONT_HOME_SIDE" in status_block
    assert (REPO_ROOT / "resources/host/images/Frame-2.png").exists()
    assert (REPO_ROOT / "resources/host/images/Frame-3.png").exists()


def test_cleaning_page_milk_frother_deep_clean_prepare_flow():
    cleaning_page = _read("app/ui/pages/settings_cleaning_page.c")
    daily_block = cleaning_page[
        cleaning_page.index("static const settings_cleaning_action_item_t settings_cleaning_daily_items[]") :
        cleaning_page.index("static const settings_cleaning_action_item_t settings_cleaning_maintenance_items[]")
    ]
    prepare_block = cleaning_page[
        cleaning_page.index("static int32_t settings_cleaning_prepare_progress_width_for_time") :
        cleaning_page.index("static bool settings_cleaning_create_clean_card")
    ]

    assert "#define SETTINGS_CLEANING_PREPARE_ICON_BOX_WIDTH 240" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_ICON_BOX_HEIGHT 240" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_ICON_BOX_X 56" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_ICON_BOX_Y 117" in cleaning_page
    assert "SETTINGS_CLEANING_PREPARE_ICON_NAME \"Frame-4.png\"" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_PANEL_WIDTH 416" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_PANEL_HEIGHT 376" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_PANEL_X 336" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_PANEL_Y 52" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_PROMPT_WIDTH 264" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_PROMPT_HEIGHT 64" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_PROMPT_X 76" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_PROMPT_Y 25" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_BUTTON_WIDTH 192" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_BUTTON_HEIGHT 64" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_CANCEL_X 0" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_START_X 224" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_BUTTON_Y 312" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_TIME_DEFAULT_SEC 32" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_TIME_MAX_SEC 60" in cleaning_page
    assert "#define SETTINGS_CLEANING_PREPARE_TIME_MAX_LABEL_Y 224" in cleaning_page
    assert "prepare_time_sec" in cleaning_page
    assert "settings_cleaning_set_prepare_time" in cleaning_page
    assert "settings_cleaning_prepare_time_event" in cleaning_page
    assert "lv_indev_get_point(lv_indev_active(), &point)" in prepare_block
    assert "settings_cleaning_create_prepare_time_progress" in prepare_block
    assert "SETTINGS_CLEANING_DESCALING_ICON_NAME" in prepare_block
    assert "settings_cleaning_load_icon(state, SETTINGS_CLEANING_PREPARE_ICON_NAME" in prepare_block
    assert "请向奶泡器中加入清水,\\n并设置清洗时间" in cleaning_page
    assert "清洗时间" in cleaning_page
    assert "32s" in cleaning_page
    assert "60s" in cleaning_page
    assert "取消" in cleaning_page
    assert "开始清洗" in cleaning_page
    assert "UI_STYLE_FONT_HOME_SIDE" in prepare_block
    assert "{\"奶泡器深度清洗\", \"立即除垢\", SETTINGS_CLEANING_CARD_ICON_NAME, false, true, false, NULL," in daily_block
    assert "settings_cleaning_prepare_clicked" in cleaning_page
    assert "lv_obj_add_event_cb(card, settings_cleaning_prepare_clicked, LV_EVENT_CLICKED, state)" in cleaning_page
    assert "lv_obj_add_event_cb(button, settings_cleaning_prepare_clicked, LV_EVENT_CLICKED, state)" in cleaning_page
    assert "settings_cleaning_delete_prepare_overlay(state)" in cleaning_page
    assert "settings_cleaning_start_quick_rinse(state)" in prepare_block
    assert "settings_cleaning_create_daily_clean(state)" in prepare_block
    assert (REPO_ROOT / "resources/host/images/Frame-4.png").exists()


def test_cleaning_page_brewer_deep_clean_tablet_and_water_flow():
    cleaning_page = _read("app/ui/pages/settings_cleaning_page.c")
    maintenance_items_block = cleaning_page[
        cleaning_page.index("static const settings_cleaning_action_item_t settings_cleaning_maintenance_items[]") :
        cleaning_page.index("static void settings_cleaning_delete_prepare_overlay")
    ]
    maintenance_prepare_block = cleaning_page[
        cleaning_page.index("static bool settings_cleaning_create_maintenance_prepare_overlay") :
        cleaning_page.index("static bool settings_cleaning_create_clean_card")
    ]
    rinse_return_block = cleaning_page[
        cleaning_page.index("static void settings_cleaning_rinse_return_timer_cb") :
        cleaning_page.index("static void settings_cleaning_schedule_rinse_return")
    ]

    assert "#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_NAME \"Frame-5.png\"" in cleaning_page
    assert "#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_WIDTH 240" in cleaning_page
    assert "#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_HEIGHT 240" in cleaning_page
    assert "#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_X 56" in cleaning_page
    assert "#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_Y 120" in cleaning_page
    assert "#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_PROMPT_X 404" in cleaning_page
    assert "#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_PROMPT_Y 160" in cleaning_page
    assert "#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_PROMPT_WIDTH 312" in cleaning_page
    assert "#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_PROMPT_HEIGHT 32" in cleaning_page
    assert "#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_CANCEL_X 352" in cleaning_page
    assert "#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_NEXT_X 576" in cleaning_page
    assert "#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_BUTTON_Y 256" in cleaning_page
    assert "{\"冲泡器深度清洁（加药片）\", \"清洗\", SETTINGS_CLEANING_CARD_ICON_NAME, false, false, true," in maintenance_items_block
    assert "\"请向冲泡器中加入清水和药片\", \"请向奶罐加入清水\", SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_NAME," in maintenance_items_block
    assert "SETTINGS_CLEANING_RINSE_AFTER_RETURN}" in maintenance_items_block
    assert "settings_cleaning_create_maintenance_prepare_overlay(" in cleaning_page
    assert "settings_cleaning_create_maintenance_prepare_overlay(" in rinse_return_block
    assert "SETTINGS_CLEANING_MAINTENANCE_PREPARE_WATER" in rinse_return_block
    assert "SETTINGS_CLEANING_RINSE_AFTER_RETURN" in rinse_return_block
    assert "SETTINGS_CLEANING_RINSE_AFTER_SHOW_MAINTENANCE_WATER" in cleaning_page
    assert "state->selected_tab == SETTINGS_CLEANING_TAB_MAINTENANCE" in cleaning_page
    assert "请向冲泡器中加入清水和药片" in maintenance_prepare_block
    assert "请向奶罐加入清水" in maintenance_prepare_block
    assert "下一步" in maintenance_prepare_block
    assert "settings_cleaning_start_rinse(state, state->maintenance_prepare_after_action)" in cleaning_page
    assert "settings_cleaning_start_rinse(state, SETTINGS_CLEANING_RINSE_AFTER_RETURN)" in cleaning_page
    assert "completed_status == SETTINGS_CLEANING_RINSE_COMPLETE" in rinse_return_block
    assert (REPO_ROOT / "resources/host/images/Frame-5.png").exists()


def test_cleaning_page_maintenance_tablet_rinse_preserves_after_action():
    cleaning_page = _read("app/ui/pages/settings_cleaning_page.c")
    delete_rinse_start = cleaning_page.index(
        "static void settings_cleaning_delete_rinse_overlay",
        cleaning_page.index("static void settings_cleaning_stop_rinse_timer"),
    )
    start_rinse_block = cleaning_page[
        cleaning_page.index("static void settings_cleaning_start_rinse") :
        cleaning_page.index("static void settings_cleaning_start_quick_rinse")
    ]

    create_rinse_index = start_rinse_block.index("(void)settings_cleaning_create_rinse_status(state)")
    assign_after_action_index = start_rinse_block.index("state->rinse_after_action = after_action")

    assert create_rinse_index < assign_after_action_index
    assert "settings_cleaning_delete_rinse_overlay(state)" in cleaning_page[
        cleaning_page.index("static bool settings_cleaning_create_rinse_status") :
        cleaning_page.index("static void settings_cleaning_start_rinse")
    ]
    assert "state->rinse_after_action = SETTINGS_CLEANING_RINSE_AFTER_RETURN" in cleaning_page[
        delete_rinse_start : cleaning_page.index("static void settings_cleaning_delete_prepare_overlay",
                                                 delete_rinse_start)
    ]


def test_cleaning_page_milk_frother_maintenance_tablet_and_water_flow():
    cleaning_page = _read("app/ui/pages/settings_cleaning_page.c")
    maintenance_items_block = cleaning_page[
        cleaning_page.index("static const settings_cleaning_action_item_t settings_cleaning_maintenance_items[]") :
        cleaning_page.index("static void settings_cleaning_delete_prepare_overlay")
    ]
    maintenance_prepare_block = cleaning_page[
        cleaning_page.index("static bool settings_cleaning_create_maintenance_prepare_overlay") :
        cleaning_page.index("static bool settings_cleaning_create_clean_card")
    ]
    maintenance_clicked_block = cleaning_page[
        cleaning_page.index("static void settings_cleaning_maintenance_prepare_clicked") :
        cleaning_page.index("static bool settings_cleaning_create_clean_card")
    ]

    assert "{\"奶泡器深度清洁（加药片）\", \"清洗\", SETTINGS_CLEANING_CARD_ICON_NAME, false, false, true," in maintenance_items_block
    assert "\"请向奶泡器中加入清水和药品\", \"请向奶罐加入清水\", SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_NAME," in maintenance_items_block
    assert "SETTINGS_CLEANING_RINSE_AFTER_SHOW_MAINTENANCE_WATER}" in maintenance_items_block
    assert "{\"冲泡器深度清洁（加药片）\", \"清洗\", SETTINGS_CLEANING_CARD_ICON_NAME, false, false, true," in maintenance_items_block
    assert "\"请向冲泡器中加入清水和药片\", \"请向奶罐加入清水\", SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_NAME," in maintenance_items_block
    assert "SETTINGS_CLEANING_RINSE_AFTER_RETURN}" in maintenance_items_block
    assert "const settings_cleaning_action_item_t *item" in maintenance_clicked_block
    assert "settings_cleaning_create_maintenance_prepare_overlay(" in maintenance_clicked_block
    assert "SETTINGS_CLEANING_MAINTENANCE_PREPARE_TABLET" in maintenance_clicked_block
    assert "item->maintenance_prepare_prompt" in maintenance_clicked_block
    assert "item->maintenance_prepare_water_prompt" in maintenance_clicked_block
    assert "item->maintenance_prepare_icon_name" in maintenance_clicked_block
    assert "item->maintenance_prepare_after_action" in maintenance_clicked_block
    assert "请向奶泡器中加入清水和药品" in maintenance_items_block
    assert "tablet_prompt" in maintenance_prepare_block
    assert "请向奶罐加入清水" in maintenance_prepare_block
    assert "next_text = step == SETTINGS_CLEANING_MAINTENANCE_PREPARE_WATER ? \"清水\" : \"下一步\"" in maintenance_prepare_block
    assert "lv_obj_add_event_cb(card, settings_cleaning_maintenance_prepare_clicked, LV_EVENT_CLICKED, (void *)item)" in cleaning_page
    assert "lv_obj_add_event_cb(button, settings_cleaning_maintenance_prepare_clicked, LV_EVENT_CLICKED, (void *)item)" in cleaning_page


def test_cleaning_page_descaling_prepare_tablet_and_water_flow():
    cleaning_page = _read("app/ui/pages/settings_cleaning_page.c")
    maintenance_items_block = cleaning_page[
        cleaning_page.index("static const settings_cleaning_action_item_t settings_cleaning_maintenance_items[]") :
        cleaning_page.index("static void settings_cleaning_delete_prepare_overlay")
    ]
    maintenance_prepare_block = cleaning_page[
        cleaning_page.index("static bool settings_cleaning_create_maintenance_prepare_overlay") :
        cleaning_page.index("static bool settings_cleaning_create_clean_card")
    ]
    maintenance_icon_block = cleaning_page[
        cleaning_page.index("static bool settings_cleaning_create_maintenance_prepare_icon_box") :
        cleaning_page.index("static bool settings_cleaning_create_maintenance_prepare_button")
    ]
    rinse_return_block = cleaning_page[
        cleaning_page.index("static void settings_cleaning_rinse_return_timer_cb") :
        cleaning_page.index("static void settings_cleaning_schedule_rinse_return")
    ]

    assert "{\"除垢\", \"立即除垢\", SETTINGS_CLEANING_MAINTENANCE_DESCALING_ICON_NAME, false, false, true," in maintenance_items_block
    assert "\"请向水箱中加入清水和清洁剂\"" in maintenance_items_block
    assert "\"再向水箱加入清水\"" in maintenance_items_block
    assert "\"Frame-6.png\"" in maintenance_items_block
    assert "SETTINGS_CLEANING_RINSE_AFTER_SHOW_MAINTENANCE_WATER" in maintenance_items_block
    assert "maintenance_prepare_icon_name" in cleaning_page
    assert "maintenance_prepare_water_prompt" in cleaning_page
    assert "state->maintenance_prepare_icon_name" in maintenance_icon_block
    assert "state->maintenance_prepare_water_prompt" in maintenance_prepare_block
    assert "请向水箱中加入清水和清洁剂" in maintenance_items_block
    assert "再向水箱加入清水" in maintenance_items_block
    assert "SETTINGS_CLEANING_MAINTENANCE_PREPARE_WATER" in rinse_return_block
    assert (REPO_ROOT / "resources/host/images/Frame-6.png").exists()


def test_details_page_menu_and_drink_statistics_layout():
    details_page = _read("app/ui/pages/settings_details_page.c")
    title_block = details_page[
        details_page.index("static bool settings_details_create_title") :
        details_page.index("static bool settings_details_load_recipe_image")
    ]

    assert "#define SETTINGS_DETAILS_TITLE_TEXT \"详细信息\"" in details_page
    assert "#define SETTINGS_DETAILS_DRINK_IMAGE_NATIVE_SIZE 240" in details_page
    assert "#define SETTINGS_DETAILS_DRINK_IMAGE_SCALE ((SETTINGS_DETAILS_DRINK_IMAGE_SIZE * 256) / SETTINGS_DETAILS_DRINK_IMAGE_NATIVE_SIZE)" in details_page
    assert "#define SETTINGS_DETAILS_HEADER_HEIGHT 96" in details_page
    assert "#define SETTINGS_DETAILS_MENU_WIDTH 240" in details_page
    assert "#define SETTINGS_DETAILS_MENU_ITEM_COUNT 3u" in details_page
    assert "SETTINGS_DETAILS_MENU_TOP_RIGHT_RADIUS" not in details_page
    assert "SETTINGS_DETAILS_MENU_TOP_RIGHT_CUTOUT_SIZE" not in details_page
    assert "SETTINGS_DETAILS_MENU_TOP_RIGHT_ROUND_SIZE" not in details_page
    assert "#define SETTINGS_DETAILS_CONTENT_X SETTINGS_DETAILS_MENU_WIDTH" in details_page
    assert "#define SETTINGS_DETAILS_CONTENT_WIDTH 560" in details_page
    assert "#define SETTINGS_DETAILS_CONTENT_HEIGHT 404" in details_page
    assert "#define SETTINGS_DETAILS_DRINK_CARD_WIDTH 236" in details_page
    assert "#define SETTINGS_DETAILS_DRINK_CARD_HEIGHT 96" in details_page
    assert "#define SETTINGS_DETAILS_DRINK_CARD_GAP_X 24" in details_page
    assert "#define SETTINGS_DETAILS_DRINK_CARD_GAP_Y 24" in details_page
    assert "#define SETTINGS_DETAILS_DRINK_IMAGE_SIZE 64" in details_page
    assert "SETTINGS_DETAILS_TAB_DRINKS" in details_page
    assert "settings_details_create_drink_statistics" in details_page
    assert "lv_obj_set_scroll_dir(state->content, LV_DIR_VER)" in details_page
    assert "lv_obj_set_scrollbar_mode(state->content, LV_SCROLLBAR_MODE_AUTO)" in details_page
    assert "UI_STYLE_FONT_HOME_USER" in title_block
    assert "UI_STYLE_FONT_DETAILS_DRINK" in details_page
    assert "UI_STYLE_FONT_DETAILS_MENU_TITLE" in details_page
    assert "UI_STYLE_FONT_DETAILS_MENU_VALUE" in details_page
    assert "lv_image_set_scale(image, SETTINGS_DETAILS_DRINK_IMAGE_SCALE)" in details_page
    assert "lv_image_set_pivot(image, 0, 0)" in details_page
    assert "settings_details_drinks[]" in details_page
    menu_block = details_page[
        details_page.index("static bool settings_details_create_menu(settings_details_page_state_t *state)") :
        details_page.index("static bool settings_details_create_content(settings_details_page_state_t *state)")
    ]
    assert "settings_details_create_menu_top_right_corner" not in details_page
    assert "menu_top_right_cutout" not in details_page
    assert "menu_top_right_round" not in details_page
    data_block = details_page[
        details_page.index("static const settings_details_menu_item_t settings_details_menu_items[]") :
        details_page.index("static const settings_details_drink_t settings_details_drinks[]")
    ]
    assert "SETTINGS_DETAILS_TAB_FACTORY" not in data_block
    assert "恢复出厂设置" not in data_block
    for text in ["饮品杯数统计", "234344", "意式浓缩", "意式大杯", "美式咖啡", "卡布奇诺", "拿铁咖啡", "拿铁玛琪雅朵"]:
        assert text in details_page


def test_details_page_descaling_and_machine_info_states():
    details_page = _read("app/ui/pages/settings_details_page.c")
    descaling_block = details_page[
        details_page.index("static bool settings_details_create_descaling") :
        details_page.index("static void settings_details_factory_button_clicked")
    ]
    machine_block = details_page[
        details_page.index("static bool settings_details_create_machine_info") :
        details_page.index("static bool settings_details_create_content_for_tab")
    ]

    assert "SETTINGS_DETAILS_TAB_DESCALING" in details_page
    assert "SETTINGS_DETAILS_TAB_MACHINE" in details_page
    assert "settings_details_create_descaling" in details_page
    assert "settings_details_create_machine_info" in details_page
    assert "settings_details_descaling_icon.png" in details_page
    assert "#define SETTINGS_DETAILS_DESCALING_CARD_HEIGHT 96" in details_page
    assert "#define SETTINGS_DETAILS_DESCALING_CARD_RADIUS 16" in details_page
    assert "#define SETTINGS_DETAILS_INFO_CARD_WIDTH 496" in details_page
    assert "#define SETTINGS_DETAILS_INFO_CARD_HEIGHT 215" in details_page
    assert "#define SETTINGS_DETAILS_INFO_CARD_RADIUS 16" in details_page
    assert "型号:" in details_page
    assert "HMI版本号:" in details_page
    assert "OS版本号:" in details_page
    assert "CTR版本号:" in details_page
    assert "SN号:" in details_page
    assert "CM01" in details_page
    assert "V1.0.0" in details_page
    assert "V1.0.1" in details_page
    assert "HSUIDF29023209023" in details_page
    assert "settings_details_factory_button_clicked" in details_page
    assert "SETTINGS_DETAILS_INFO_CARD_WIDTH, SETTINGS_DETAILS_DESCALING_CARD_HEIGHT" in descaling_block
    assert "lv_obj_set_style_radius(card, SETTINGS_DETAILS_DESCALING_CARD_RADIUS" in descaling_block
    assert descaling_block.count("UI_STYLE_FONT_DETAILS_MENU_VALUE") == 2
    assert "UI_STYLE_FONT_HOME_USER" not in descaling_block
    assert "UI_STYLE_FONT_HOME_SIDE" not in descaling_block
    assert machine_block.count("UI_STYLE_FONT_DETAILS_MENU_TITLE") == 2
    assert "UI_STYLE_FONT_HOME_SIDE" in machine_block
    assert "UI_STYLE_FONT_HOME_USER" not in machine_block
    assert (REPO_ROOT / "resources/host/images/settings_details_descaling_icon.png").exists()


def test_details_page_factory_reset_modal():
    details_page = _read("app/ui/pages/settings_details_page.c")
    modal_button_block = details_page[
        details_page.index("static bool settings_details_create_modal_button") :
        details_page.index("static bool settings_details_create_factory_modal")
    ]
    modal_block = details_page[
        details_page.index("static bool settings_details_create_factory_modal") :
        details_page.index("void settings_details_page_destroy")
    ]

    assert "settings_details_create_factory_modal" in details_page
    assert "settings_details_show_factory_modal" in details_page
    assert "settings_details_factory_cancel_clicked" in details_page
    assert "settings_details_factory_confirm_clicked" in details_page
    assert "是否恢复出厂设置" in details_page
    assert "取消" in details_page
    assert "确认" in details_page
    assert "#define SETTINGS_DETAILS_MODAL_BUTTON_WIDTH 240" in details_page
    assert "#define SETTINGS_DETAILS_MODAL_BUTTON_HEIGHT 64" in details_page
    assert "#define SETTINGS_DETAILS_MODAL_CONFIRM_COLOR 0xB56A2E" in details_page
    assert "UI_STYLE_FONT_DETAILS_MODAL" in modal_block
    assert "UI_STYLE_FONT_HOME_SIDE" in modal_button_block
    assert "UI_STYLE_FONT_HOME_USER" not in modal_block
    assert "UI_STYLE_FONT_HOME_USER" not in modal_button_block


def test_ui_style_exposes_20pt_details_drink_font():
    header = _read("components/ui_style/include/ui_style.h")
    source = _read("components/ui_style/src/ui_style.c")
    cmake = _read("components/ui_style/CMakeLists.txt")
    export_cmake = _read("cmake/modules/ep_export_targets.cmake")

    assert "UI_STYLE_FONT_DETAILS_DRINK" in header
    assert "UI_STYLE_FONT_DETAILS_MENU_TITLE" in header
    assert "UI_STYLE_FONT_DETAILS_MENU_VALUE" in header
    assert "UI_STYLE_FONT_DETAILS_MODAL" in header
    assert "LV_FONT_DECLARE(ui_font_source_han_18)" in source
    assert "LV_FONT_DECLARE(ui_font_source_han_20)" in source
    assert "LV_FONT_DECLARE(ui_font_source_han_32)" in source
    assert "{UI_STYLE_FONT_DETAILS_MENU_VALUE, 18u, &ui_font_source_han_18, NULL}" in source
    assert "{UI_STYLE_FONT_DETAILS_DRINK, 20u, &ui_font_source_han_20, NULL}" in source
    assert "{UI_STYLE_FONT_DETAILS_MENU_TITLE, 20u, &ui_font_source_han_20, NULL}" in source
    assert "{UI_STYLE_FONT_DETAILS_MODAL, 32u, &ui_font_source_han_32, NULL}" in source
    assert "src/ui_font_source_han_18.c" in cmake
    assert "src/ui_font_source_han_20.c" in cmake
    assert "src/ui_font_source_han_32.c" in cmake
    assert "components/ui_style/src/ui_font_source_han_18.c" in export_cmake
    assert "components/ui_style/src/ui_font_source_han_20.c" in export_cmake
    assert "components/ui_style/src/ui_font_source_han_32.c" in export_cmake
    assert (REPO_ROOT / "components/ui_style/src/ui_font_source_han_18.c").exists()
    assert (REPO_ROOT / "components/ui_style/src/ui_font_source_han_20.c").exists()
    assert (REPO_ROOT / "components/ui_style/src/ui_font_source_han_32.c").exists()


def test_settings_and_user_borders_are_gray():
    settings_page = _read("app/ui/pages/settings_page.c")
    home_page = _read("app/ui/pages/home_page.c")

    assert "#define SETTINGS_PAGE_BUTTON_BORDER_COLOR 0x666666" in settings_page
    assert "#define HOME_PAGE_USER_DROPDOWN_BORDER_COLOR 0x666666" in home_page
    assert "0x43382D" not in settings_page
    assert "0x3D3734" not in home_page


def test_home_recipe_opens_minimal_running_page_with_back_button():
    app_pages = _read("app/ui/pages/app_pages.h")
    app_ui = _read("app/ui/app_ui.c")
    app_cmake = _read("app/CMakeLists.txt")
    home_page = _read("app/ui/pages/home_page.c")
    running_header = _read("app/ui/pages/running_page.h")
    running_page = _read("app/ui/pages/running_page.c")

    assert "APP_PAGE_RUNNING" in app_pages
    assert '#include "pages/running_page.h"' in app_ui
    assert "page_manager_register(APP_PAGE_RUNNING" in app_ui
    assert "running_page_create" in app_ui
    assert "running_page_event" in app_ui
    assert "running_page_destroy" in app_ui
    assert "ui/pages/running_page.c" in app_cmake

    assert "static void home_page_recipe_clicked(lv_event_t *event)" in home_page
    assert "home_page_open_running_page(state)" in home_page
    assert "running_page_set_recipe_image_src(state->recipe_src[HOME_PAGE_CENTER_SLOT])" in home_page
    assert "page_manager_switch(APP_PAGE_RUNNING, LV_SCR_LOAD_ANIM_MOVE_LEFT, 180, true)" in home_page
    assert "lv_obj_add_event_cb(slot->container, home_page_recipe_clicked, LV_EVENT_CLICKED, state)" in home_page
    assert "lv_obj_add_event_cb(slot->image, home_page_recipe_clicked, LV_EVENT_CLICKED, state)" in home_page
    assert "slot_index == HOME_PAGE_CENTER_SLOT" in home_page

    assert "void running_page_set_recipe_image_src(const char *src);" in running_header
    assert "lv_obj_t *running_page_create(page_manager_page_ctx_t *ctx);" in running_header
    assert (
        "void running_page_event(page_manager_page_ctx_t *ctx, uint32_t code, uint32_t wparam, uint32_t lparam);"
        in running_header
    )
    assert "void running_page_destroy(page_manager_page_ctx_t *ctx);" in running_header
    assert "#define RUNNING_PAGE_BG_IMAGE_NAME \"running_bg.png\"" in running_page
    assert "#define RUNNING_PAGE_START_ICON_NAME \"running_start.png\"" in running_page
    assert "char bg_src[RUNNING_PAGE_SRC_BUFFER_SIZE]" in running_page
    assert "char start_src[RUNNING_PAGE_SRC_BUFFER_SIZE]" in running_page
    assert "ep_platform_lvgl_image_src(RUNNING_PAGE_BG_IMAGE_NAME" in running_page
    assert "lv_obj_move_background(bg)" in running_page
    assert "#define RUNNING_PAGE_RECIPE_IMAGE_FALLBACK_X 47" in running_page
    assert "#define RUNNING_PAGE_RECIPE_IMAGE_FALLBACK_Y 139" in running_page
    assert "#define RUNNING_PAGE_RECIPE_IMAGE_SIZE 180" in running_page
    assert "#define RUNNING_PAGE_RECIPE_ALPHA_THRESHOLD 8u" in running_page
    assert "#define RUNNING_PAGE_RECIPE_TARGET_CENTER_X" in running_page
    assert "#define RUNNING_PAGE_RECIPE_TARGET_CENTER_OFFSET_X (-5)" in running_page
    assert "#define RUNNING_PAGE_RECIPE_TARGET_BOTTOM_OFFSET_Y 50" in running_page
    assert "#define RUNNING_PAGE_RECIPE_TARGET_BOTTOM_Y" in running_page
    assert "char recipe_image_src[RUNNING_PAGE_SRC_BUFFER_SIZE]" in running_page
    assert "static char running_page_pending_recipe_image_src[RUNNING_PAGE_SRC_BUFFER_SIZE]" in running_page
    assert "running_page_set_recipe_image_src(const char *src)" in running_page
    assert "running_page_copy_string(running_page_pending_recipe_image_src" in running_page
    assert "lv_image_decoder_get_info(state->recipe_image_src, &header)" in running_page
    assert "running_page_recipe_bounds_t" in running_page
    assert "running_page_recipe_layout_t" in running_page
    assert "running_page_measure_recipe_bounds" in running_page
    assert "running_page_recipe_bottom_anchor_x" in running_page
    assert "RUNNING_PAGE_RECIPE_ANCHOR_BAND_MIN_HEIGHT 8u" in running_page
    assert "lv_image_decoder_open(&dsc, src, &args)" in running_page
    assert "lv_image_decoder_close(&dsc)" in running_page
    assert "LV_COLOR_FORMAT_ARGB8888" in running_page
    assert "LV_COLOR_FORMAT_RGB565A8" in running_page
    assert "LV_COLOR_FORMAT_A8" in running_page
    assert "running_page_recipe_image_layout(&header, &bounds)" in running_page
    assert "RUNNING_PAGE_RECIPE_TARGET_CENTER_X + RUNNING_PAGE_RECIPE_TARGET_CENTER_OFFSET_X" in running_page
    assert "lv_image_set_scale(image, layout.scale)" in running_page
    assert "lv_obj_set_pos(image, layout.x, layout.y)" in running_page
    assert "RUNNING_PAGE_STRENGTH_LIGHT" in running_page
    assert "RUNNING_PAGE_STRENGTH_MEDIUM" in running_page
    assert "RUNNING_PAGE_STRENGTH_STRONG" in running_page
    assert "RUNNING_PAGE_STRENGTH_DEFAULT RUNNING_PAGE_STRENGTH_MEDIUM" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_CONTROL_X 32" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_CONTROL_Y 112" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_CONTROL_WIDTH 224" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_CONTROL_HEIGHT 44" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_MINUS_X 0" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_PLUS_X (RUNNING_PAGE_STRENGTH_CONTROL_WIDTH - RUNNING_PAGE_STRENGTH_BUTTON_SIZE)" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_TEXT_WIDTH (RUNNING_PAGE_STRENGTH_CONTROL_WIDTH - RUNNING_PAGE_STRENGTH_BUTTON_SIZE * 2)" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_RING_X 63" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_RING_Y 271" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_X (RUNNING_PAGE_STRENGTH_RING_X + 26)" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_WIDTH 134" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_HEIGHT 80" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_RING_LIGHT_X (RUNNING_PAGE_STRENGTH_RING_X + 84)" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_RING_LIGHT_WIDTH 76" in running_page
    assert "#define RUNNING_PAGE_STRENGTH_RING_LIGHT_HEIGHT 66" in running_page
    assert "#define RUNNING_PAGE_START_X 114" in running_page
    assert "#define RUNNING_PAGE_START_Y (SETTINGS_PAGE_SCREEN_HEIGHT - 44 - RUNNING_PAGE_START_SIZE)" in running_page
    assert "#define RUNNING_PAGE_START_SIZE 60" in running_page
    for icon_name in [
        "running_start.png",
        "running_minus.png",
        "running_plus.png",
        "running_ring_base.png",
        "running_ring_light.png",
        "running_ring_medium.png",
        "running_ring_strong.png",
    ]:
        assert icon_name in running_page
        assert (REPO_ROOT / "resources/host/images" / icon_name).exists()
    for text in ["清淡", "适中", "浓郁"]:
        assert text in running_page
    assert "lv_obj_t *strength_control" in running_page
    assert "running_page_create_strength_controls(state)" in running_page
    assert "state->strength_control = lv_obj_create(state->screen)" in running_page
    assert "lv_obj_set_pos(state->strength_control, RUNNING_PAGE_STRENGTH_CONTROL_X, RUNNING_PAGE_STRENGTH_CONTROL_Y)" in running_page
    assert "lv_obj_set_size(state->strength_control," in running_page
    assert "RUNNING_PAGE_STRENGTH_CONTROL_WIDTH" in running_page
    assert "RUNNING_PAGE_STRENGTH_CONTROL_HEIGHT" in running_page
    assert "lv_button_create(parent)" in running_page
    assert "lv_obj_set_pos(button, x, 0)" in running_page
    assert "lv_obj_align(icon, LV_ALIGN_CENTER, 0, 0)" in running_page
    assert "lv_label_create(state->strength_control)" in running_page
    assert "lv_obj_set_width(state->strength_label, RUNNING_PAGE_STRENGTH_TEXT_WIDTH)" in running_page
    assert "lv_obj_set_height(state->strength_label, LV_SIZE_CONTENT)" in running_page
    assert "lv_obj_align(state->strength_label, LV_ALIGN_CENTER, 0, 0)" in running_page
    assert "running_page_strength_minus_clicked" in running_page
    assert "running_page_strength_plus_clicked" in running_page
    assert "running_page_refresh_strength(state)" in running_page
    assert "running_page_start_clicked" in running_page
    assert "running_page_create_start_button(state)" in running_page
    assert "lv_obj_add_event_cb(button, running_page_start_clicked, LV_EVENT_CLICKED, state)" in running_page
    assert "running_page_create_strength_ring(state)" in running_page
    assert "lv_image_set_src(state->strength_overlay, state->strength_ring_light_src)" in running_page
    assert "lv_image_set_src(state->strength_overlay, state->strength_ring_medium_src)" in running_page
    assert "lv_image_set_src(state->strength_overlay, state->strength_ring_strong_src)" in running_page
    assert "lv_obj_set_pos(state->strength_overlay, RUNNING_PAGE_STRENGTH_RING_LIGHT_X" in running_page
    assert "RUNNING_PAGE_STRENGTH_RING_LIGHT_WIDTH" in running_page
    assert "RUNNING_PAGE_STRENGTH_RING_MEDIUM_WIDTH" in running_page
    assert "RUNNING_PAGE_STRENGTH_RING_STRONG_WIDTH" in running_page
    assert (
        running_page.index("running_page_create_strength_ring(state)")
        < running_page.index("running_page_create_recipe_image(state)")
        < running_page.index("running_page_create_start_button(state)")
        < running_page.index("running_page_create_strength_controls(state)")
    )
    assert "settings_common_style_screen(screen)" in running_page
    assert "SETTINGS_PAGE_BACK_ICON_NAME" in running_page
    assert "SETTINGS_PAGE_BACK_X" in running_page
    assert "SETTINGS_PAGE_BACK_Y" in running_page
    assert "SETTINGS_PAGE_BACK_SIZE" in running_page
    assert "page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180)" in running_page
    assert (REPO_ROOT / "resources/host/images/running_bg.png").exists()
