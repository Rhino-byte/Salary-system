# Admin email alerts and attendance (operations)

## Admin email: new advance and off-day requests

When a user submits a **new** advance (`POST /api/advances`) or off-day request (`POST /api/off-days`), the API attempts to email a single admin address (if enabled).

### Environment variables

| Variable | Purpose |
|----------|---------|
| `ADMIN_NOTIFICATION_EMAIL` | Recipient inbox for these alerts. If empty, no admin email is sent. |
| `ENABLE_ADMIN_EMAIL_NOTIFICATIONS` | `true` / `false` (optional). If unset, notifications are **on** when `ADMIN_NOTIFICATION_EMAIL` and SMTP credentials are set (see `app/config/config.py`). |
| `EMAIL_USER`, `EMAIL_PASSWORD` | SMTP login (Gmail app password, etc.) |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_FROM` | Optional; defaults match Gmail-style SMTP. |
| `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM_EMAIL` | **Fallback** names: if `EMAIL_*` is empty, these are used so existing `.env` files work. |

Implementation: [`app/services/notification_service.py`](../app/services/notification_service.py) (`notify_admin_new_advance`, `notify_admin_new_off_day`) and [`app/config/config.py`](../app/config/config.py).

## Attendance: daily job (calendar days minus approved off days)

The daily script [`scripts/daily_attendance_update.py`](../scripts/daily_attendance_update.py) recomputes `days_worked_this_month` and `total_days_worked` for **every** employee using the same rules as the rest of the app: **calendar days in range minus approved off-day spans** (see [`app/utils/attendance.py`](../app/utils/attendance.py), `recompute_all_employees_attendance`).

On the **1st of the month**, the script still runs monthly resets (attendance + salary) before the recompute, as before.

The older **incremental** counters in `app/services/attendance_service.py` are **deprecated**; do not use them for new code.

## Related docs

- [DAILY_ATTENDANCE_UPDATE.md](DAILY_ATTENDANCE_UPDATE.md) — scheduling the daily job
