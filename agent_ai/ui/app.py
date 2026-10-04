"""Chainlit chat UI for the Strands agent's FastAPI /chat endpoint."""

import json
import os
import uuid

import chainlit as cl
import httpx


AGENT_URL = os.environ.get("AGENT_URL", "http://localhost:8080/chat")
REQUEST_TIMEOUT = float(os.environ.get("AGENT_TIMEOUT", "120"))

# Demo credentials can be overridden when starting Chainlit. Set
# CHAINLIT_AUTH_SECRET for any deployment where the UI is reachable by others.
USERS = {
    "sales-analyst": os.environ.get("SALES_ANALYST_PASSWORD", "sales-analyst"),
    "support-associate": os.environ.get("SUPPORT_ASSOCIATE_PASSWORD", "support-associate"),
}
PERSONA_LABELS = {
    "sales-analyst": "Sales Analyst",
    "support-associate": "Support Associate",
}


@cl.password_auth_callback
def authenticate(username: str, password: str) -> cl.User | None:
    """Authenticate one of the two static demo users."""
    expected_password = USERS.get(username)
    if expected_password is None or password != expected_password:
        return None

    return cl.User(
        identifier=username,
        metadata={"persona": username, "persona_label": PERSONA_LABELS[username]},
    )


@cl.on_chat_start
async def start_chat() -> None:
    cl.user_session.set("session_id", f"ui-{uuid.uuid4()}")
    user = cl.user_session.get("user")
    persona = user.metadata.get("persona") if user else None
    label = PERSONA_LABELS.get(persona, "Agent user")
    await cl.Message(
        content=(
            f"Signed in as **{label}**. Ask a question and I’ll send it to the Strands agent."
        )
    ).send()


@cl.on_message
async def chat(message: cl.Message) -> None:
    user = cl.user_session.get("user")
    actor_id = user.identifier if user else "anonymous"
    payload = {
        "query": message.content,
        "session_id": cl.user_session.get("session_id"),
        "actor_id": actor_id,
    }
    answer = cl.Message(content="")
    received_answer = False

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async with client.stream("POST", AGENT_URL, json=payload) as response:
                response.raise_for_status()
                done = False
                async for line in response.aiter_lines():
                    # Drain the HTTP response after [DONE]. Breaking here closes
                    # HTTPX's async body iterator while it's suspended at a
                    # yield, which can produce "async generator ignored
                    # GeneratorExit" during cleanup.
                    if done:
                        continue
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        done = True
                        continue
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    # The FastAPI server emits answer deltas as {"token": ...}.
                    token = event.get("token")
                    if isinstance(token, str) and token:
                        received_answer = True
                        await answer.stream_token(token)

        if received_answer:
            await answer.send()
        else:
            await cl.Message(content="The agent returned no answer.").send()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500]
        await cl.Message(
            content=f"The agent returned HTTP {exc.response.status_code}: `{detail}`"
        ).send()
    except httpx.RequestError as exc:
        await cl.Message(
            content=f"Could not reach the agent at `{AGENT_URL}`: {exc}"
        ).send()
