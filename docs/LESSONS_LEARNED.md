# Lessons Learned

## Forex Factory time parsing

- Prefer `timeLabel` from `window.calendarComponentStates` over `dateline` when both exist.
- `timeLabel` matches the visible Forex Factory table; `dateline` can resolve one hour away from the operator-facing time.
- Keep `dateline` only as fallback when visible date/time fields are unavailable.

## GitHub Actions timing

- Scheduled workflows can run late. Alerts must use strict stale windows instead of catch-up behavior.
- Daily summaries should only send during a short local-midnight window; otherwise skip rather than send hours late.

## Result updates

- Do not notify result updates while `Actual` is empty, `N/D`, `NA`, or equivalent.
- Result retries should wait for real data and avoid sending repeated empty Telegram messages.
