"""命令行入口：修改飞书日历和日程。"""

from __future__ import annotations

import argparse
import json
import sys

from .client import DEFAULT_TIMEZONE, FeishuAPIError, FeishuCalendar


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="通过飞书开放平台读取和修改日历")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("auth", help="检查能否拿到 tenant_access_token")

    sub.add_parser("list-calendars", help="列出当前身份可见的日历")

    update_calendar = sub.add_parser("update-calendar", help="修改日历标题、描述或公开范围")
    _add_calendar_arg(update_calendar)
    update_calendar.add_argument("--summary")
    update_calendar.add_argument("--description")
    update_calendar.add_argument("--permissions", choices=["private", "show_only_free_busy", "public"])
    update_calendar.add_argument("--color", type=int)
    update_calendar.add_argument("--summary-alias")

    list_events = sub.add_parser("list-events", help="列出一段时间内的日程")
    _add_calendar_arg(list_events)
    list_events.add_argument("--start", required=True, help="YYYY-MM-DD 或 YYYY-MM-DD HH:MM")
    list_events.add_argument("--end", required=True)
    _add_timezone(list_events)

    create_event = sub.add_parser("create-event", help="创建日程")
    _add_calendar_arg(create_event)
    create_event.add_argument("--summary", required=True)
    create_event.add_argument("--start", required=True)
    create_event.add_argument("--end", required=True)
    create_event.add_argument("--description")
    create_event.add_argument("--location")
    create_event.add_argument("--notify", action="store_true")
    _add_timezone(create_event)

    update_event = sub.add_parser("update-event", help="修改已有日程")
    _add_calendar_arg(update_event)
    update_event.add_argument("--event", required=True, help="event_id")
    update_event.add_argument("--summary")
    update_event.add_argument("--description")
    update_event.add_argument("--start")
    update_event.add_argument("--end")
    update_event.add_argument("--location")
    update_event.add_argument("--visibility", choices=["default", "public", "private"])
    update_event.add_argument("--free-busy", choices=["busy", "free"], dest="free_busy_status")
    update_event.add_argument("--notify", action="store_true")
    _add_timezone(update_event)

    delete_event = sub.add_parser("delete-event", help="删除日程")
    _add_calendar_arg(delete_event)
    delete_event.add_argument("--event", required=True)
    delete_event.add_argument("--notify", action="store_true")

    args = parser.parse_args(argv)
    client = FeishuCalendar()
    try:
        result = _dispatch(client, args)
    except (FeishuAPIError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if result is not None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _dispatch(client: FeishuCalendar, args: argparse.Namespace):
    if args.command == "auth":
        token = client.access_token()
        return {"ok": True, "token_prefix": token[:6], "identity": "user" if client.user_access_token else "tenant"}
    if args.command == "list-calendars":
        return client.list_calendars()
    if args.command == "update-calendar":
        return client.update_calendar(
            args.calendar,
            summary=args.summary,
            description=args.description,
            permissions=args.permissions,
            color=args.color,
            summary_alias=args.summary_alias,
        )
    if args.command == "list-events":
        return client.list_events(args.calendar, args.start, args.end, timezone=args.timezone)
    if args.command == "create-event":
        return client.create_event(
            args.calendar,
            summary=args.summary,
            start=args.start,
            end=args.end,
            description=args.description,
            timezone=args.timezone,
            location=args.location,
            need_notification=args.notify,
        )
    if args.command == "update-event":
        return client.update_event(
            args.calendar,
            args.event,
            summary=args.summary,
            description=args.description,
            start=args.start,
            end=args.end,
            timezone=args.timezone,
            location=args.location,
            visibility=args.visibility,
            free_busy_status=args.free_busy_status,
            need_notification=True if args.notify else False,
        )
    if args.command == "delete-event":
        return client.delete_event(args.calendar, args.event, need_notification=args.notify)
    raise ValueError(f"未知命令: {args.command}")


def _add_calendar_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--calendar", default="primary", help="日历 ID，默认 primary（当前身份的主日历）")


def _add_timezone(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE)
