"""Learning-agent request and context composition."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.runtime.conversation import Conversation, Message
from study.prompt_plans import LearningTurnPlan
from study.state import LearningState

from chat.material_state import (
    _should_use_material_answer_conversation_window,
)
from chat.turn_contract import (
    TurnContract,
)
from chat.turn_predicates import (
    _overview_turn,
)

if TYPE_CHECKING:
    from chat.session import ChatSession


from chat.prior_answer import (
    _isolated_recall_conversation,
    _prior_answer_context_excerpt,
)
from chat.reply_repair import _should_buffer_learning_output, _user_visible_reply
from chat.turn_outputs import (
    _LearningAgentBuffer,
    _LearningAgentOutput,
    _LearningAgentRequest,
)

_MATERIAL_CONTEXT_MESSAGE_LIMIT = 4


def _learning_agent_output_from_buffer(
    plan: LearningTurnPlan,
    buffer: _LearningAgentBuffer,
) -> _LearningAgentOutput:
    streamed_reply = buffer.streamed_reply
    raw_reply = streamed_reply
    if not raw_reply and buffer.completion_event is not None:
        raw_reply = buffer.completion_event.full_text
    visible_reply = _user_visible_reply(plan, raw_reply)
    if _overview_turn(plan):
        raw_reply = visible_reply
    return _LearningAgentOutput(
        streamed_reply=streamed_reply,
        raw_reply=raw_reply,
        visible_reply=visible_reply,
        completion_event=buffer.completion_event,
    )


def _learning_agent_request(
    plan: LearningTurnPlan,
    original_learning_state: LearningState,
    user_input: str,
    session: ChatSession,
    contract: TurnContract | None,
) -> _LearningAgentRequest:
    conversation = _learning_agent_conversation(
        plan,
        original_learning_state,
        user_input,
        session,
        contract,
    )
    return _LearningAgentRequest(
        conversation=conversation,
        buffer_output=_should_buffer_learning_output(plan),
    )


def _learning_agent_conversation(
    plan: LearningTurnPlan,
    original_learning_state: LearningState,
    user_input: str,
    session: ChatSession,
    contract: TurnContract | None,
) -> Conversation:
    isolated = _isolated_recall_conversation(
        plan,
        original_learning_state,
        user_input,
        contract,
    )
    if isolated is not None:
        return isolated
    if _should_use_material_answer_conversation_window(plan, contract):
        return _material_answer_conversation_window(session.conversation, user_input)
    return session.conversation


def _material_answer_conversation_window(
    conversation: Conversation,
    user_input: str,
) -> Conversation:
    window = Conversation()
    for message in _recent_material_context_messages(conversation, user_input):
        content = _material_context_message_content(message)
        if content:
            window.add(message.role, content)
    window.add("user", user_input)
    return window


def _recent_material_context_messages(
    conversation: Conversation,
    user_input: str,
) -> tuple[Message, ...]:
    messages = conversation.messages
    if messages and messages[-1].role == "user" and messages[-1].content == user_input:
        messages = messages[:-1]
    eligible = [
        message
        for message in messages
        if message.role in {"user", "assistant"} and message.content.strip()
    ]
    return tuple(eligible[-_MATERIAL_CONTEXT_MESSAGE_LIMIT:])


def _material_context_message_content(message: Message) -> str:
    content = message.content.strip()
    if message.role != "assistant":
        return content
    return _prior_answer_context_excerpt(content)
