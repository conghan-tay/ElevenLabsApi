"""Text-to-Dialogue WebSocket sample driven by audio tags.

Mirrors the message flow of text-to-dialogue-websocket.py, but sends a tag-heavy
line and exposes the model/voice as CLI flags so other models can be tried
without editing the file.
"""

import argparse
import asyncio
import base64
import json
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
import websockets

load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

DEFAULT_VOICE_ID = "emSmWzY0c0xtx5IFMCVv"
DEFAULT_MODEL_ID = "eleven_v4_turbo"  # TTD requires eleven_v3* or eleven_v4*

# Sent verbatim. Most of these tags are not in the documented vocabulary
# ([chuckles], [long pause], [laughs], ...), so the model may interpret them
# loosely, ignore them, or read them aloud. That is what this sample tests.
DIALOGUE = (
    "[cheerful][innocent][lighthearted] You know... "
    "[pause][whimsical] when I was four months old... "
    "[pause slightly longer][confessional][soft chuckle] I had balls too... "
    "[awkward pause][nervous giggle][trail off]"
)

OUTPUT_DIR = Path(__file__).parent / "output"


async def stream_dialogue(voice_id: str, model_id: str, out_path: Path) -> int:
    uri = (
        "wss://api.elevenlabs.io/v1/text-to-dialogue/stream-input"
        f"?model_id={model_id}&output_format=mp3_44100_128"
    )

    total_bytes = 0
    async with websockets.connect(uri) as websocket:
        await websocket.send(
            json.dumps(
                {
                    "voices": [voice_id],
                    "xi_api_key": ELEVENLABS_API_KEY,
                }
            )
        )

        await websocket.send(
            json.dumps(
                {
                    "inputs": [
                        {"text": DIALOGUE, "voice_id": voice_id, "new_turn": False},
                    ],
                }
            )
        )

        # Flushes any buffered text, emits the remaining audio, then is_final.
        await websocket.send(json.dumps({"close_socket": True}))

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as audio_file:
            while True:
                raw = await websocket.recv()
                msg = json.loads(raw)
                if msg.get("error"):
                    raise RuntimeError(msg)
                if msg.get("audio"):
                    chunk = base64.b64decode(msg["audio"])
                    audio_file.write(chunk)
                    total_bytes += len(chunk)
                if msg.get("is_final"):
                    break

    return total_bytes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL_ID, help="TTD model id")
    parser.add_argument("--voice", default=DEFAULT_VOICE_ID, help="voice id")
    parser.add_argument("--play", action="store_true", help="play the result via ffplay")
    args = parser.parse_args()

    if not ELEVENLABS_API_KEY:
        raise SystemExit("ELEVENLABS_API_KEY is not set (expected in .env)")

    out_path = OUTPUT_DIR / f"dialogue-audio-tags_{args.model}.mp3"

    try:
        total_bytes = asyncio.run(stream_dialogue(args.voice, args.model, out_path))
    except websockets.exceptions.ConnectionClosed as exc:
        raise SystemExit(f"socket closed before the stream finished: {exc}")

    # An empty file would otherwise look like a clean run.
    if total_bytes == 0:
        raise SystemExit(f"stream finished but no audio was returned ({out_path})")

    print(f"Wrote {out_path} ({total_bytes:,} bytes, model={args.model})")

    if args.play:
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", str(out_path)])


if __name__ == "__main__":
    main()
