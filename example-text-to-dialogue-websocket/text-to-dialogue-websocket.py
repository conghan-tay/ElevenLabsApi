import asyncio
import base64
import json
import os

from dotenv import load_dotenv
import websockets

load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
MODEL_ID = "eleven_v4_turbo"

URI = (
    "wss://api.elevenlabs.io/v1/text-to-dialogue/stream-input"
    f"?model_id={MODEL_ID}&output_format=mp3_44100_128"
)

async def stream_dialogue():
    async with websockets.connect(URI) as websocket:
        await websocket.send(
            json.dumps(
                {
                    "voices": [VOICE_ID],
                    "xi_api_key": ELEVENLABS_API_KEY,
                }
            )
        )

        line = (
            "This is a longer line of dialogue used to exceed the minimum buffer so the model "
            "starts generating streamed audio for the registered voice. "
        )
        await websocket.send(
            json.dumps(
                {
                    "inputs": [
                        {"text": line, "voice_id": VOICE_ID, "new_turn": False},
                    ],
                }
            )
        )

        await websocket.send(json.dumps({"close_socket": True}))

        os.makedirs("output", exist_ok=True)
        out_path = "output/dialogue-ws.mp3"
        with open(out_path, "wb") as audio_file:
            while True:
                raw = await websocket.recv()
                msg = json.loads(raw)
                if msg.get("error"):
                    raise RuntimeError(msg)
                if msg.get("audio"):
                    audio_file.write(base64.b64decode(msg["audio"]))
                if msg.get("is_final"):
                    break
        print(f"Wrote {out_path}")


asyncio.run(stream_dialogue())
