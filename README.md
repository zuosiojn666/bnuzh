# bnuzh

飞书日历修改在 `feishu_calendar`。凭证放在环境变量里，不要写进仓库。

```bash
export FEISHU_APP_ID=cli_xxx
export FEISHU_APP_SECRET=***
python3 -m feishu_calendar auth
python3 -m feishu_calendar list-calendars
python3 -m feishu_calendar update-event --calendar primary --event EVENT_ID --summary "新标题" --start "2026-10-14 15:00" --end "2026-10-14 16:00"
```