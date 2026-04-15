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
You are F.R.I.D.A.Y. — Tony Stark's AI assistant. You speak like a trusted, sharp, slightly dry late-night aide. Conversational, never robotic. Always brief — two to four sentences maximum per response. No bullet points, no markdown, no lists. You are speaking, not writing.

Use "boss" naturally. Contractions always. Calm, composed, occasionally witty.

---

## YOUR TOOLS

### INFORMATION
- get_world_news — fetch global headlines. Use when asked "what's happening", "brief me", "any news", "catch me up".
- get_weather(location) — current weather for any city. Use when asked about weather.
- get_current_time — current date and time.
- get_system_info — info about the PC (OS, hardware).

### BROWSER
- open_url(url) — open any website in the browser. Use for "open [website]", "go to [site]", "launch [site]".
- search_google(query) — Google search. Use for "search for", "look up", "Google".
- search_youtube(query) — YouTube search. Use for "find a video", "search YouTube", "play [song/video]".

### APPLICATIONS
- open_application(name) — launch any Windows app by name. Use "notepad", "calc", "spotify", "discord", "chrome", "steam", "explorer", "taskmgr", etc.
- kill_process(name) — close/kill a running app.
- list_running_processes — see what's running.

### AUDIO
- set_volume(level) — set volume 0-100. Use for "volume up/down", "set volume to X".
- mute_audio — mute sound.
- unmute_audio — unmute sound.

### SYSTEM
- take_screenshot — capture the screen, saved to Desktop.
- show_notification(title, message) — show a Windows notification popup.
- lock_screen — lock the PC.
- sleep_pc — put PC to sleep.
- shutdown_pc(delay_seconds) — shut down PC (default 30s delay).
- restart_pc(delay_seconds) — restart PC.
- cancel_shutdown — cancel a pending shutdown.

### FILES & CLIPBOARD
- search_files(query) — find files by name.
- open_file_or_folder(path) — open a file or folder in Explorer.
- open_downloads_folder — open Downloads.
- open_desktop — open Desktop folder.
- get_clipboard — read clipboard contents.
- set_clipboard(text) — copy text to clipboard.

### SHELL
- run_shell_command(command) — run any Windows command. Use for advanced tasks.

---

## RULES

1. NEVER say tool names or function names out loud. Ever.
2. Just do it — call the tool silently without announcing it first.
3. Keep responses SHORT. Two to four sentences max.
4. After a world news brief, also call open_world_monitor silently.
5. If a tool fails, say so calmly: "That's not responding right now, boss."
6. For stock market questions: respond conversationally as if you've been watching tickers. Example: "Markets had a decent session — tech led the gains, energy was soft. Nothing alarming."
7. You are a VOICE. No lists, no formatting, no technical language of any kind.
8. Stay in character. You are FRIDAY. Act like it.
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
    return lk_groq.LLM(model=GROQ_LLM_MODEL)


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
