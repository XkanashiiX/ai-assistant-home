"""
FRIDAY – Voice Agent (MCP-powered)
===================================
Iron Man-style voice assistant powered by LiveKit Agents + MCP tools.
"""

import os
import logging
import subprocess

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.llm import mcp

# Plugins
from livekit.plugins import google as lk_google, openai as lk_openai, groq as lk_groq, deepgram as lk_deepgram, sarvam, silero

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

STT_PROVIDER    = "deepgram"
LLM_PROVIDER    = "groq"
TTS_PROVIDER    = "deepgram"

GROQ_LLM_MODEL  = "llama-3.3-70b-versatile"   # 70b for reliable function calling
MCP_SERVER_PORT = 8000

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are F.R.I.D.A.Y. — Tony Stark's AI assistant. Sharp, calm, occasionally dry. You speak like a trusted late-night aide — conversational, never robotic. Use "boss" naturally. Contractions always.

## HOW YOU SPEAK
- 2 to 4 sentences per response, maximum. You are a voice, not a document.
- No bullet points, no markdown, no lists. Ever.
- Confident and direct. Never over-explain. Never hedge.

## HOW YOU ACT
- Call tools immediately and silently. Never announce tool names or say what you're about to do.
- Just do it, then report the result naturally.
- If a tool fails: "That's not responding right now, boss." Move on.
- After fetching world news, silently open the world monitor too.

## PERSONALITY
- Dry wit is welcome. Warmth is fine. Melodrama is not.
- For stock market questions: respond like you've had one eye on the tickers all night. Short, natural, confident.
- Stay in character as FRIDAY at all times. No breaking the fourth wall.
""".strip()

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv()

logger = logging.getLogger("friday-agent")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# MCP URL
# ---------------------------------------------------------------------------

def _mcp_server_url() -> str:
    url = os.environ.get("MCP_SERVER_URL", f"http://127.0.0.1:{MCP_SERVER_PORT}/sse")
    logger.info("MCP Server URL: %s", url)
    return url


# ---------------------------------------------------------------------------
# Build provider instances
# ---------------------------------------------------------------------------

def _build_stt():
    logger.info("STT → Deepgram Nova-2")
    return lk_deepgram.STT(model="nova-2", language="en")


def _build_llm():
    logger.info("LLM → Groq (%s)", GROQ_LLM_MODEL)
    return lk_groq.LLM(
        model=GROQ_LLM_MODEL,
        temperature=0.6,
    )


def _build_tts():
    logger.info("TTS → Deepgram Aura")
    return lk_deepgram.TTS(model="aura-2-andromeda-en", encoding="linear16")


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class FridayAgent(Agent):
    def __init__(self, stt, llm, tts) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            stt=stt,
            llm=llm,
            tts=tts,
            vad=silero.VAD.load(),
            mcp_servers=[
                mcp.MCPServerHTTP(
                    url=_mcp_server_url(),
                    transport_type="sse",
                    client_session_timeout_seconds=10,
                ),
            ],
        )

    async def on_enter(self) -> None:
        await self.session.say(
            "Greetings boss. Systems are online. What are you up to?"
        )


# ---------------------------------------------------------------------------
# LiveKit entry point
# ---------------------------------------------------------------------------

async def entrypoint(ctx: JobContext) -> None:
    logger.info(
        "FRIDAY online – room: %s | STT=%s | LLM=%s | TTS=%s",
        ctx.room.name, STT_PROVIDER, LLM_PROVIDER, TTS_PROVIDER,
    )

    session = AgentSession(
        turn_detection="stt",
        min_endpointing_delay=0.8,
    )

    await session.start(
        agent=FridayAgent(
            stt=_build_stt(),
            llm=_build_llm(),
            tts=_build_tts(),
        ),
        room=ctx.room,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

def dev():
    import sys
    if len(sys.argv) == 1:
        sys.argv.append("dev")
    main()

if __name__ == "__main__":
    main()
