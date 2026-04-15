# F.R.I.D.A.Y. — Tony Stark Demo

A Tony Stark-inspired AI assistant with two components:

1. **MCP Server** (`server.py`) — A FastMCP server that exposes tools (news, web search, system info) over SSE at `http://0.0.0.0:8000/sse`
2. **Voice Agent** (`agent_friday.py`) — A LiveKit Agents voice pipeline that listens to the microphone, reasons with Gemini 2.5 Flash, and responds with OpenAI TTS

## Architecture

```
Microphone ──► STT (Sarvam Saaras v3)
                    │
                    ▼
             LLM (Gemini 2.5 Flash)  ◄──────► MCP Server (FastMCP / SSE on :8000)
                    │                              ├─ get_world_news
                    ▼                              ├─ open_world_monitor
             TTS (OpenAI nova)                     ├─ search_web
                    │                              └─ …more tools
                    ▼
             Speaker / LiveKit room
```

## Project Structure

```
friday-tony-stark-demo/
├── server.py           # MCP server entry point (uv run friday)
├── agent_friday.py     # LiveKit voice agent entry point (uv run friday_voice)
├── pyproject.toml      # Project dependencies and script definitions
├── .env.example        # Environment variable template
└── friday/             # MCP server package
    ├── config.py       # Environment variable loading
    ├── tools/          # MCP tools (web.py, system.py, utils.py)
    ├── prompts/        # MCP prompt templates
    └── resources/      # MCP resources
```

## Tech Stack

- **Language**: Python 3.11+
- **Package Manager**: uv
- **MCP Framework**: FastMCP
- **Voice Pipeline**: LiveKit Agents
- **STT**: Sarvam Saaras v3
- **LLM**: Google Gemini 2.5 Flash
- **TTS**: OpenAI TTS (nova voice)

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Purpose |
|----------|----------|---------|
| `LIVEKIT_URL` | ✅ | LiveKit Cloud project URL |
| `LIVEKIT_API_KEY` | ✅ | LiveKit Cloud API key |
| `LIVEKIT_API_SECRET` | ✅ | LiveKit Cloud API secret |
| `SARVAM_API_KEY` | ✅ | Sarvam STT API key |
| `OPENAI_API_KEY` | ✅ | OpenAI TTS API key |
| `GOOGLE_API_KEY` | ✅ | Google Gemini LLM API key |
| `GROQ_API_KEY` | optional | Groq LLM (alternative provider) |
| `DEEPGRAM_API_KEY` | optional | Deepgram STT (alternative provider) |
| `SUPABASE_URL` | optional | Supabase for ticketing tool |
| `SUPABASE_API_KEY` | optional | Supabase API key |

## Running the Project

The **MCP server** runs via the configured workflow (`uv run friday`) on port 8000.

To run the **voice agent** (in a separate terminal):
```bash
uv run friday_voice
```

Then connect via the [LiveKit Agents Playground](https://agents-playground.livekit.io).

## Switching AI Providers

Edit the constants at the top of `agent_friday.py`:
```python
STT_PROVIDER = "sarvam"   # "sarvam" | "whisper"
LLM_PROVIDER = "gemini"   # "gemini" | "openai"
TTS_PROVIDER = "openai"   # "openai" | "sarvam"
```
