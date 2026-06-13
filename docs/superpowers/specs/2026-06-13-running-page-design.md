# Running Page Design

## Scope

Add the first version of the recipe running page. The page is opened from the Home page recipe carousel when the user taps the active recipe. This version intentionally contains only the back button needed to validate navigation. Recipe-specific controls, progress, status text, and machine actions are deferred.

## Layout

The running page uses the same 800x480 LVGL screen size as the existing app pages.

- Background is black.
- Top-left back button matches the Settings subpage back control:
  - same back icon resource,
  - `x=32`, `y=32`,
  - `48x48` touch target.
- No other visible UI is added in this version.

## Behavior

- Add a new `APP_PAGE_RUNNING` page id.
- Register the running page from `app_ui_create()`.
- Tapping the currently centered Home carousel recipe opens the running page through `page_manager_switch()` with history enabled.
- Tapping the running page back button calls `page_manager_back()` and returns to the Home page.
- The Home page still supports settings navigation and carousel dragging as before.

## Architecture

- Add `app/ui/pages/running_page.c` and `app/ui/pages/running_page.h`.
- Keep the running page as a normal page-manager page, not an overlay inside `home_page.c`. This preserves a clean boundary for later recipe execution state, progress controls, and hardware/service integration.
- Reuse the Settings common back icon pattern where possible so the visual style stays consistent.
- Do not introduce recipe state plumbing yet. The first version only proves that every carousel recipe can navigate into the same running page.

## Error Handling

If the back icon image cannot be resolved, the page still loads and the button remains clickable with a text fallback.

## Testing

Extend host unit tests that inspect LVGL UI source for:

- `APP_PAGE_RUNNING` page id,
- running page registration in `app_ui.c`,
- running page source/header included in `app/CMakeLists.txt`,
- Home carousel recipe click navigation to `APP_PAGE_RUNNING` with history enabled,
- running page back button calling `page_manager_back()`,
- reuse of the same back icon resource and 48x48 top-left metrics.

