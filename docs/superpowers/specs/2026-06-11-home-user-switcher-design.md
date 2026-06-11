# Home User Switcher Design

## Scope

Add the Home page user entry and expanded user selector shown in the provided 800x480 reference images. The change is limited to the Home page UI and host image resources. It does not add user persistence, user database records, or recipe behavior changes.

## Layout

The Home page keeps the existing full-screen background and carousel. The settings icon is aligned to the new reference coordinates at `x=32`, `y=24`, size `48x48`.

The current user entry is placed at the top right:

- Avatar: `x=677`, `y=24`, size `48x48`
- Arrow: `x=749`, `y=43`, size `19x10`

The expanded user selector is created as a foreground layer:

- Container: `x=399`, `y=112`, size `369x325`
- Corner radius: `12`
- Four rows: `用户1` through `用户4`
- Selected row background: `#FFFFFF`
- Unselected row background: `#2F2B29`

The first version uses the provided 48x48 avatar resource for all four users. The code should keep the image name as a constant so replacing it with four per-user assets later is straightforward.

## Behavior

Clicking the avatar or arrow toggles the selector. Clicking a row updates the selected user index, refreshes the row colors, and hides the selector. The default selected user is `用户1`.

The selector does not block or alter carousel state except where the selector itself receives the click. When opened, it is moved to the foreground so the carousel remains visible behind it.

## Error Handling

If the avatar image cannot be resolved from platform resources, the UI falls back to a text label in the same 48x48 area. If the selector or row allocation fails, the Home page still loads with the existing carousel and settings button.

## Testing

Host unit tests should verify the Home page defines the expected user switcher constants, uses platform image resource resolution, toggles the dropdown with LVGL hidden flags, applies the selected/unselected colors, and keeps the existing carousel tests intact. The host app should build after the change.
