# Settings Selection List Design

## Scope

Add a reusable LVGL selection-list pattern for settings subpages. The first consumer is the language selection page opened from the Settings > Language button. The later sleep-time page can reuse the same list component with a different item set and container height.

## Visual Design

- Screen size remains 800x480 with black background.
- Top left is the existing 48x48 back icon at x=32, y=32.
- Top right is a 48x48 confirm icon at x=720, y=32.
- The usable top spacing between controls follows the supplied reference, leaving a 640pt center gap.
- The selection list is centered horizontally with width 369pt, row height 64pt, and corner radius 12pt.
- Selected row uses white background and black text. Unselected rows use the same dark fill as the home user dropdown with white text.
- Row separators use a restrained gray line, and container/button borders use gray instead of the existing brown-tinted colors.
- Fonts use the existing `ui_style_font()` family backed by SourceHan/TinyTTF so multilingual labels render consistently.

## Behavior

- Tapping Settings > Language opens the language selection page.
- The language page initially selects the current/default language visually.
- Tapping a row changes only the visual selected row in this version.
- Confirm and back both return to the settings page. Real language persistence and refresh behavior are intentionally deferred.
- The list is data-driven so adding languages only extends an item array; when item count exceeds the visible container, vertical scrolling is enabled.

## Architecture

- Add a new app page id for the language page and register it in `app_ui.c`.
- Add a small reusable selection-list helper under the settings page ownership boundary, not a broad framework component. This keeps the first change focused while still allowing the sleep page to reuse it later.
- Keep list metrics and shared colors as named constants so the language page, future sleep page, settings buttons, and home user dropdown can share the gray-border direction without duplicating magic values.

## Testing

- Extend host unit tests that inspect LVGL UI source for:
  - language page id and registration,
  - Settings > Language navigation,
  - reusable list constants for 369pt width, 64pt rows, and 12pt radius,
  - confirm/back returning through page-manager history,
  - gray border color replacing brown colors in settings buttons and the home user dropdown.

