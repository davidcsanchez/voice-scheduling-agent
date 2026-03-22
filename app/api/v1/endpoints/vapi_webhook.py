import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError

from app.api.deps import get_calendar_service, get_user_service
from app.core.security import verify_vapi_signature
from app.domain.schemas import MeetingRequest
from app.services.calendar_service import CalendarService
from app.services.user_service import UserService

router = APIRouter(tags=["vapi"])
logger = logging.getLogger(__name__)


@router.post("/vapi/webhook")
async def vapi_webhook(
    request: Request,
    calendar_service: CalendarService = Depends(get_calendar_service),
    user_service: UserService = Depends(get_user_service),
) -> dict:
    await verify_vapi_signature(request)
    payload = await request.json()
    tool_calls = _extract_tool_calls(payload)
    logger.info("Vapi webhook received. extracted_tool_calls=%s", len(tool_calls))
    if not tool_calls:
        logger.warning("Vapi webhook payload has no tool calls.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No tool calls")

    results = []
    for tool_call in tool_calls:
        if tool_call["name"] != "create_calendar_event":
            logger.warning(
                "Unsupported tool requested. tool_call_id=%s tool=%s",
                tool_call.get("id"),
                tool_call.get("name"),
            )
            results.append(
                {
                    "toolCallId": tool_call["id"],
                    "result": {"error": "Unsupported tool"},
                }
            )
            continue

        try:
            meeting = MeetingRequest.model_validate(tool_call["arguments"])
            user_id = user_service.resolve_user_id(payload)
            event_result = calendar_service.create_event(user_id, meeting)
            logger.info(
                "Calendar event created. tool_call_id=%s resolved_user_id=%s event_id=%s",
                tool_call.get("id"),
                user_id,
                event_result.get("eventId"),
            )
            results.append({"toolCallId": tool_call["id"], "result": event_result})
        except (ValueError, ValidationError) as error:
            logger.warning(
                "Vapi tool call failed. tool_call_id=%s tool=%s resolved_user_id=%s error=%s",
                tool_call.get("id"),
                tool_call.get("name"),
                user_service.resolve_user_id(payload),
                str(error),
            )
            results.append(
                {"toolCallId": tool_call["id"], "result": {"error": str(error)}}
            )

    logger.info("Vapi webhook processed. tool_results=%s", len(results))

    return {
        "toolResults": results,
        "results": results,
    }


def _extract_tool_calls(payload: dict) -> list[dict]:
    if "toolCalls" in payload:
        return _normalize_tool_calls(payload.get("toolCalls"))
    message = payload.get("message", {})
    return _normalize_tool_calls(message.get("toolCalls"))


def _normalize_tool_calls(raw_calls: list | None) -> list[dict]:
    if not raw_calls:
        return []
    normalized = []
    for call in raw_calls:
        function = call.get("function", {})
        arguments = function.get("arguments") or call.get("arguments") or {}
        normalized.append(
            {
                "id": call.get("id") or call.get("toolCallId") or "unknown",
                "name": function.get("name") or call.get("name"),
                "arguments": _parse_arguments(arguments),
            }
        )
    return normalized


def _parse_arguments(arguments: object) -> dict:
    if isinstance(arguments, str):
        try:
            return json.loads(arguments)
        except json.JSONDecodeError:
            return {}
    if isinstance(arguments, dict):
        return arguments
    return {}
