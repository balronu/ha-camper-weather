# Camper Weather v0.1.0-beta.12 – Dropdown-Ursachenbericht

## Befund

Beta.11 protected interactive rendering with `_interactionLock` and
`_nativeSelectOpen`, but `pointerup` and `touchend` always scheduled a
150 ms unlock. A native HTML select emits those pointer events before the
user has completed the platform picker selection. If a Home Assistant state
update arrived after that timer, `_renderPanel()` was allowed to assign
`panel.innerHTML` again. That removed the original `<select>` node while its
native picker was still open, which explains the picker opening briefly and
closing before an option could be selected.

The existing `activeElement` check was not sufficient: native mobile picker
focus is platform-controlled and does not guarantee that the select remains
the active DOM element during the whole picker lifetime.

## Correction

Beta.12 treats a native select as a transaction:

- `pointerdown` records the exact select node as the active native control.
- `pointerup`/`touchend` no longer unlock or render that select.
- Repeated `hass` updates may refresh backend data, but `_renderPanel()` keeps
  the existing DOM while the native select transaction is pending.
- The transaction ends on the select's actual `change` event, after which the
  location request is awaited before the pending refresh is eligible to run.
- `pointercancel` and starting a different control provide bounded recovery
  for an abandoned picker; no fixed timer decides that the native picker is
  finished.

This prevents DOM replacement during the only interval in which replacement
can close the platform picker. Planner selects use the same lifecycle, while
their values remain in `_draft`; backend state updates therefore cannot reset
the activity or planner-location selection.

## Evidence

- **Static source proof:** beta.11's 150 ms `pointerup`/`touchend` unlock and
  subsequent `panel.innerHTML` render path are present in the beta.11 source.
- **Isolated runtime proof:** the mobile Chromium fixture sends
  `pointerdown → pointerup`, then five repeated HA state updates for 250 ms,
  asserts the original select node is still identical, and performs a real
  option change. It covers overview location, planner activity, and planner
  location controls.
- **Scope:** no DWD, weather engine, score, forecast, map/radar, provider,
  saved-activity data model, HACS settings, or VM 104 state is changed.

