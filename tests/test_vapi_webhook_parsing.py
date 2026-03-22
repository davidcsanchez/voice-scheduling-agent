from app.api.v1.endpoints.vapi_webhook import _normalize_tool_calls


def test_normalize_tool_calls_supports_function_tool_with_function_payload() -> None:
    raw_calls = [
        {
            "id": "call-1",
            "name": "function_tool",
            "arguments": {
                "function": {
                    "name": "create_calendar_event",
                    "arguments": {
                        "name": "Alex",
                        "date": "2026-03-25",
                        "time": "10:00",
                        "timezone": "America/New_York",
                        "title": "Planning",
                    },
                }
            },
        }
    ]

    normalized = _normalize_tool_calls(raw_calls)

    assert normalized[0]["name"] == "create_calendar_event"
    assert normalized[0]["arguments"]["title"] == "Planning"


def test_normalize_tool_calls_supports_function_tool_with_direct_function_name() -> None:
    raw_calls = [
        {
            "id": "call-2",
            "name": "function_tool",
            "arguments": {
                "functionName": "create_calendar_event",
                "arguments": {
                    "name": "Sam",
                    "date": "2026-03-30",
                    "time": "09:30",
                    "timezone": "America/Chicago",
                    "title": "Sync",
                },
            },
        }
    ]

    normalized = _normalize_tool_calls(raw_calls)

    assert normalized[0]["name"] == "create_calendar_event"
    assert normalized[0]["arguments"]["name"] == "Sam"


def test_normalize_tool_calls_maps_function_tool_when_arguments_match_meeting_schema() -> None:
    raw_calls = [
        {
            "id": "call-3",
            "name": "function_tool",
            "arguments": {
                "name": "Taylor",
                "date": "2026-04-01",
                "time": "15:00",
                "timezone": "America/Los_Angeles",
                "title": "Demo",
            },
        }
    ]

    normalized = _normalize_tool_calls(raw_calls)

    assert normalized[0]["name"] == "create_calendar_event"
    assert normalized[0]["arguments"]["timezone"] == "America/Los_Angeles"
