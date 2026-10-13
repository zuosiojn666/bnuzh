"""飞书日历 v4：读取、创建、更新、删除日程，以及更新日历本身。

凭证只从参数或环境变量读取，不会写入仓库：
- FEISHU_APP_ID
- FEISHU_APP_SECRET
- FEISHU_USER_ACCESS_TOKEN  可选，有则优先用用户身份
- FEISHU_BASE_URL           可选，默认 https://open.feishu.cn
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

DEFAULT_BASE_URL = "https://open.feishu.cn"
DEFAULT_TIMEZONE = "Asia/Shanghai"

_POLICY_HINTS = {
    21001: (
        "飞书访问控制策略拒绝了这次请求。App ID 和 App Secret 已被识别，"
        "但平台没有签发 access token。请企业管理员在飞书管理后台放行当前出口 IP，"
        "或在应用「安全设置」中关闭/调整访问限制后重试。"
    ),
    21000: "飞书要求先完成安全验证后才能继续。请按返回的 challenge 地址由管理员完成验证。",
}


class FeishuAPIError(Exception):
    def __init__(self, code: int, message: str, payload: dict[str, Any] | None = None):
        self.code = code
        self.message = message
        self.payload = payload or {}
        hint = _POLICY_HINTS.get(code)
        text = f"飞书 API 错误 {code}: {message}"
        if hint:
            text = f"{text}\n{hint}"
        super().__init__(text)


def parse_time(value: str, timezone: str = DEFAULT_TIMEZONE) -> dict[str, str]:
    """把 CLI 时间转成飞书 time_info。

    YYYY-MM-DD 视为全天日程，使用 date。
    其他可解析的时间视为某一时刻，使用秒级 timestamp。
    纯数字视为已经是秒级时间戳。
    """
    text = value.strip()
    if not text:
        raise ValueError("时间为空")
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        datetime.strptime(text, "%Y-%m-%d")
        return {"date": text}
    if text.isdigit():
        return {"timestamp": text, "timezone": timezone}
    zone = ZoneInfo(timezone)
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = datetime.strptime(text, fmt).replace(tzinfo=zone)
            break
        except ValueError:
            parsed = None
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"无法解析时间: {value}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=zone)
    return {"timestamp": str(int(parsed.timestamp())), "timezone": timezone}


class FeishuCalendar:
    def __init__(
        self,
        app_id: str | None = None,
        app_secret: str | None = None,
        *,
        user_access_token: str | None = None,
        base_url: str | None = None,
        timeout: float = 30,
    ):
        self.app_id = app_id or os.environ.get("FEISHU_APP_ID", "")
        self.app_secret = app_secret or os.environ.get("FEISHU_APP_SECRET", "")
        self.user_access_token = user_access_token or os.environ.get("FEISHU_USER_ACCESS_TOKEN") or None
        self.base_url = (base_url or os.environ.get("FEISHU_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._tenant_token: str | None = None
        self._tenant_expire_at = 0.0

    def access_token(self) -> str:
        if self.user_access_token:
            return self.user_access_token
        now = time.time()
        if self._tenant_token and now < self._tenant_expire_at - 60:
            return self._tenant_token
        if not self.app_id or not self.app_secret:
            raise FeishuAPIError(0, "缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET")
        payload = self.request(
            "POST",
            "/open-apis/auth/v3/tenant_access_token/internal",
            body={"app_id": self.app_id, "app_secret": self.app_secret},
            auth=False,
        )
        token = payload.get("tenant_access_token")
        if not token:
            raise FeishuAPIError(payload.get("code", 0), "响应里没有 tenant_access_token", payload)
        self._tenant_token = token
        self._tenant_expire_at = now + int(payload.get("expire") or 7200)
        return token

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        auth: bool = True,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            encoded = urlencode({key: value for key, value in query.items() if value is not None})
            if encoded:
                url = f"{url}?{encoded}"
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if auth:
            headers["Authorization"] = f"Bearer {self.access_token()}"
        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode()
        except HTTPError as exc:
            raw = exc.read().decode()
            payload = _load_json(raw)
            raise FeishuAPIError(payload.get("code", exc.code), payload.get("msg") or exc.reason, payload) from exc
        except URLError as exc:
            raise FeishuAPIError(0, f"网络错误: {exc.reason}") from exc
        payload = _load_json(raw)
        code = payload.get("code", 0)
        if code != 0:
            raise FeishuAPIError(code, payload.get("msg") or "unknown error", payload)
        return payload

    def call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        payload = self.request(method, path, **kwargs)
        data = payload.get("data")
        return data if isinstance(data, dict) else {}

    def list_calendars(self, page_size: int = 50) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            data = self.call(
                "GET",
                "/open-apis/calendar/v4/calendars",
                query={"page_size": page_size, "page_token": page_token},
            )
            items.extend(data.get("calendar_list") or [])
            if not data.get("has_more"):
                return items
            page_token = data.get("page_token")
            if not page_token:
                return items

    def primary_calendar_id(self) -> str:
        data = self.call("POST", "/open-apis/calendar/v4/calendars/primary")
        calendars = data.get("calendars") or []
        if not calendars:
            raise FeishuAPIError(0, "当前身份没有主日历", data)
        first = calendars[0]
        calendar = first.get("calendar") if isinstance(first, dict) else None
        calendar_id = None
        if isinstance(calendar, dict):
            calendar_id = calendar.get("calendar_id")
        elif isinstance(first, dict):
            calendar_id = first.get("calendar_id")
        if not calendar_id:
            raise FeishuAPIError(0, "主日历响应里没有 calendar_id", data)
        return calendar_id

    def resolve_calendar_id(self, calendar_id: str) -> str:
        if calendar_id == "primary":
            return self.primary_calendar_id()
        return calendar_id

    def update_calendar(
        self,
        calendar_id: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        permissions: str | None = None,
        color: int | None = None,
        summary_alias: str | None = None,
    ) -> dict[str, Any]:
        body = _omit_none(
            {
                "summary": summary,
                "description": description,
                "permissions": permissions,
                "color": color,
                "summary_alias": summary_alias,
            }
        )
        if not body:
            raise ValueError("更新日历至少要提供一个字段")
        calendar_id = self.resolve_calendar_id(calendar_id)
        return self.call("PATCH", f"/open-apis/calendar/v4/calendars/{_path_id(calendar_id)}", body=body)

    def list_events(
        self,
        calendar_id: str,
        start: str,
        end: str,
        *,
        timezone: str = DEFAULT_TIMEZONE,
        page_size: int = 50,
    ) -> list[dict[str, Any]]:
        calendar_id = self.resolve_calendar_id(calendar_id)
        items: list[dict[str, Any]] = []
        page_token: str | None = None
        query_start = _query_timestamp(start, timezone, end_of_day=False)
        query_end = _query_timestamp(end, timezone, end_of_day=True)
        while True:
            data = self.call(
                "GET",
                f"/open-apis/calendar/v4/calendars/{_path_id(calendar_id)}/events",
                query={
                    "start_time": query_start,
                    "end_time": query_end,
                    "page_size": page_size,
                    "page_token": page_token,
                },
            )
            items.extend(data.get("items") or [])
            if not data.get("has_more"):
                return items
            page_token = data.get("page_token")
            if not page_token:
                return items

    def create_event(
        self,
        calendar_id: str,
        *,
        summary: str,
        start: str,
        end: str,
        description: str | None = None,
        timezone: str = DEFAULT_TIMEZONE,
        location: str | None = None,
        need_notification: bool = False,
    ) -> dict[str, Any]:
        calendar_id = self.resolve_calendar_id(calendar_id)
        body: dict[str, Any] = {
            "summary": summary,
            "start_time": parse_time(start, timezone),
            "end_time": parse_time(end, timezone),
            "need_notification": need_notification,
        }
        if description is not None:
            body["description"] = description
        if location is not None:
            body["location"] = {"name": location}
        data = self.call(
            "POST",
            f"/open-apis/calendar/v4/calendars/{_path_id(calendar_id)}/events",
            body=body,
        )
        event = data.get("event")
        return event if isinstance(event, dict) else data

    def update_event(
        self,
        calendar_id: str,
        event_id: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        start: str | None = None,
        end: str | None = None,
        timezone: str = DEFAULT_TIMEZONE,
        location: str | None = None,
        visibility: str | None = None,
        free_busy_status: str | None = None,
        need_notification: bool | None = False,
    ) -> dict[str, Any]:
        if (start is None) != (end is None):
            raise ValueError("修改时间时 start 和 end 必须同时提供")
        body = _omit_none(
            {
                "summary": summary,
                "description": description,
                "visibility": visibility,
                "free_busy_status": free_busy_status,
                "need_notification": need_notification,
            }
        )
        if start is not None and end is not None:
            body["start_time"] = parse_time(start, timezone)
            body["end_time"] = parse_time(end, timezone)
        if location is not None:
            body["location"] = {"name": location}
        if not body:
            raise ValueError("更新日程至少要提供一个字段")
        calendar_id = self.resolve_calendar_id(calendar_id)
        data = self.call(
            "PATCH",
            f"/open-apis/calendar/v4/calendars/{_path_id(calendar_id)}/events/{_path_id(event_id)}",
            body=body,
        )
        event = data.get("event")
        return event if isinstance(event, dict) else data

    def delete_event(self, calendar_id: str, event_id: str, *, need_notification: bool = False) -> dict[str, Any]:
        calendar_id = self.resolve_calendar_id(calendar_id)
        return self.call(
            "DELETE",
            f"/open-apis/calendar/v4/calendars/{_path_id(calendar_id)}/events/{_path_id(event_id)}",
            query={"need_notification": str(need_notification).lower()},
        )


def _path_id(value: str) -> str:
    return quote(value, safe="")


def _omit_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _load_json(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FeishuAPIError(0, f"响应不是 JSON: {raw[:200]}") from exc
    if not isinstance(payload, dict):
        raise FeishuAPIError(0, "响应 JSON 不是对象")
    return payload


def _query_timestamp(value: str, timezone: str, *, end_of_day: bool) -> str:
    info = parse_time(value, timezone)
    if "timestamp" in info:
        return info["timestamp"]
    zone = ZoneInfo(timezone)
    day = datetime.strptime(info["date"], "%Y-%m-%d").replace(tzinfo=zone)
    if end_of_day:
        day = day.replace(hour=23, minute=59, second=59)
    return str(int(day.timestamp()))
