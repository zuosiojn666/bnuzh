import json
import os
import unittest
from unittest.mock import patch
from urllib.parse import unquote

from feishu_calendar.client import FeishuAPIError, FeishuCalendar, parse_time
from feishu_calendar.cli import main


class _Response:
    def __init__(self, payload):
        self._raw = json.dumps(payload).encode()

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class CalendarClientTest(unittest.TestCase):
    def test_parse_time_all_day_and_clock(self):
        self.assertEqual(parse_time("2026-10-14"), {"date": "2026-10-14"})
        timed = parse_time("2026-10-14 15:00", "Asia/Shanghai")
        self.assertEqual(timed["timezone"], "Asia/Shanghai")
        self.assertTrue(timed["timestamp"].isdigit())

    def test_update_event_sends_patch_with_partial_body(self):
        captured = {}

        def fake_urlopen(req, timeout=0):
            captured["method"] = req.method
            captured["url"] = req.full_url
            captured["auth"] = req.get_header("Authorization")
            captured["body"] = json.loads(req.data.decode())
            return _Response({"code": 0, "data": {"event": {"event_id": "evt", "summary": "改后的标题"}}})

        client = FeishuCalendar(user_access_token="u-test")
        with patch("feishu_calendar.client.urlopen", fake_urlopen):
            event = client.update_event(
                "feishu.cn_abc@group.calendar.feishu.cn",
                "00592a0e-7edf-4678-bc9d-1b77383ef08e_0",
                summary="改后的标题",
                start="2026-10-14 15:00",
                end="2026-10-14 16:00",
            )

        self.assertEqual(event["summary"], "改后的标题")
        self.assertEqual(captured["method"], "PATCH")
        self.assertEqual(captured["auth"], "Bearer u-test")
        self.assertIn("/calendars/", captured["url"])
        self.assertIn("/events/", captured["url"])
        self.assertIn("%40", captured["url"])
        decoded = unquote(captured["url"])
        self.assertIn("feishu.cn_abc@group.calendar.feishu.cn", decoded)
        self.assertEqual(captured["body"]["summary"], "改后的标题")
        self.assertIn("timestamp", captured["body"]["start_time"])
        self.assertIn("timestamp", captured["body"]["end_time"])
        self.assertNotIn("description", captured["body"])

    def test_update_event_rejects_half_range(self):
        client = FeishuCalendar(user_access_token="u-test")
        with self.assertRaises(ValueError):
            client.update_event("primary", "evt", start="2026-10-14 15:00")

    def test_update_calendar_and_primary_resolution(self):
        calls = []

        def fake_urlopen(req, timeout=0):
            body = json.loads(req.data.decode()) if req.data else None
            calls.append((req.method, req.full_url, body))
            if req.full_url.endswith("/calendars/primary"):
                return _Response(
                    {
                        "code": 0,
                        "data": {"calendars": [{"calendar": {"calendar_id": "cal_primary"}}]},
                    }
                )
            return _Response({"code": 0, "data": {"calendar": {"calendar_id": "cal_primary", "summary": "口语"}}})

        client = FeishuCalendar(user_access_token="u-test")
        with patch("feishu_calendar.client.urlopen", fake_urlopen):
            result = client.update_calendar("primary", summary="口语", permissions="private")

        self.assertEqual(result["calendar"]["summary"], "口语")
        self.assertEqual(calls[0][0], "POST")
        self.assertTrue(calls[0][1].endswith("/calendars/primary"))
        self.assertEqual(calls[1][0], "PATCH")
        self.assertTrue(calls[1][1].endswith("/calendars/cal_primary"))
        self.assertEqual(calls[1][2], {"summary": "口语", "permissions": "private"})

    def test_policy_block_on_token(self):
        def fake_urlopen(req, timeout=0):
            return _Response({"code": 21001, "msg": "Access denied by access control policy. Contact the administrator for assistance."})

        client = FeishuCalendar(app_id="cli_test", app_secret="secret")
        with patch("feishu_calendar.client.urlopen", fake_urlopen):
            with self.assertRaises(FeishuAPIError) as raised:
                client.access_token()
        self.assertEqual(raised.exception.code, 21001)
        self.assertIn("访问控制策略", str(raised.exception))

    def test_cli_create_event(self):
        def fake_urlopen(req, timeout=0):
            self.assertEqual(req.method, "POST")
            body = json.loads(req.data.decode())
            self.assertEqual(body["summary"], "口语练习")
            self.assertFalse(body["need_notification"])
            return _Response({"code": 0, "data": {"event": {"event_id": "evt_1", "summary": body["summary"]}}})

        with patch.dict(os.environ, {"FEISHU_USER_ACCESS_TOKEN": "u-test"}, clear=False):
            with patch("feishu_calendar.client.urlopen", fake_urlopen):
                code = main(
                    [
                        "create-event",
                        "--calendar",
                        "cal_1",
                        "--summary",
                        "口语练习",
                        "--start",
                        "2026-10-14 19:00",
                        "--end",
                        "2026-10-14 20:00",
                    ]
                )
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
