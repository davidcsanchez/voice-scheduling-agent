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
            user_id = _require_user_id(
                user_service.resolve_user_id(payload),
                tool_call["arguments"],
            )
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
        parsed_arguments = _parse_arguments(arguments)
        resolved_name = function.get("name") or call.get("name")
        resolved_arguments = parsed_arguments

        if resolved_name == "function_tool":
            wrapped_name, wrapped_arguments = _extract_wrapped_function_call(parsed_arguments)
            if wrapped_name:
                resolved_name = wrapped_name
                resolved_arguments = wrapped_arguments
            elif _looks_like_meeting_arguments(parsed_arguments):
                resolved_name = "create_calendar_event"

        normalized.append(
            {
                "id": call.get("id") or call.get("toolCallId") or "unknown",
                "name": resolved_name,
                "arguments": resolved_arguments,
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


def _extract_wrapped_function_call(arguments: dict) -> tuple[str | None, dict]:
    if not isinstance(arguments, dict):
        return None, {}

    direct_name = arguments.get("functionName") or arguments.get("toolName")
    if isinstance(direct_name, str) and direct_name.strip():
        wrapped_args = _extract_wrapped_arguments(arguments)
        return direct_name.strip(), wrapped_args

    function_payload = arguments.get("function")
    if isinstance(function_payload, dict):
        wrapped_name = function_payload.get("name")
        if isinstance(wrapped_name, str) and wrapped_name.strip():
            wrapped_args = _parse_arguments(function_payload.get("arguments") or {})
            return wrapped_name.strip(), wrapped_args

    return None, arguments


def _extract_wrapped_arguments(arguments: dict) -> dict:
    candidates = [
        arguments.get("arguments"),
        arguments.get("args"),
        arguments.get("parameters"),
        arguments.get("input"),
    ]
    for candidate in candidates:
        parsed = _parse_arguments(candidate)
        if parsed:
            return parsed
    return {}


def _looks_like_meeting_arguments(arguments: dict) -> bool:
    required = {"name", "date", "time", "timezone", "title"}
    return required.issubset(set(arguments.keys()))


def _require_user_id(user_id: str | None, tool_arguments: dict) -> str:
    if user_id is not None and user_id.strip():
        return user_id.strip()

    user_id_from_tool_arguments = _extract_customer_id_from_tool_arguments(tool_arguments)
    if user_id_from_tool_arguments is not None:
        return user_id_from_tool_arguments

    logger.warning(
        "Missing customer identity. tool_argument_keys=%s",
        sorted(tool_arguments.keys()),
    )
    raise ValueError(
        "Missing customer identity in Vapi payload. Pass customer.id or metadata.customer_id and reconnect OAuth for that same id."
    )


def _extract_customer_id_from_tool_arguments(tool_arguments: dict) -> str | None:
    direct_customer_id = tool_arguments.get("customer_id")
    if isinstance(direct_customer_id, str) and direct_customer_id.strip():
        return direct_customer_id.strip()

    nested_candidates = [
        _parse_arguments(tool_arguments.get("metadata")),
        _parse_arguments(tool_arguments.get("variableValues")),
        _parse_arguments(tool_arguments.get("context")),
    ]
    for candidate in nested_candidates:
        customer_id = candidate.get("customer_id")
        if isinstance(customer_id, str) and customer_id.strip():
            return customer_id.strip()
    return None
