# ElevenLabsApi

A minimal quickstart for the [ElevenLabs](https://elevenlabs.io) text-to-speech API in Python.
`example.py` synthesizes a short line of speech and plays it through your speakers.

## QuickStart

Verified on macOS (Apple Silicon, Darwin 24.6) with Python 3.14.2.

### 1. Prerequisites

- **Python 3.8+** — check with `python3 --version`
- **ffmpeg** — required at runtime, see step 4

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Keeps the project's packages isolated from your system/pyenv Python. On Windows the
activate command is `.venv\Scripts\activate`.

### 3. Install the Python dependencies

```bash
pip install --upgrade pip
pip install elevenlabs python-dotenv
```

Versions this was verified against:

| Package | Version |
| --- | --- |
| `elevenlabs` | 2.70.0 |
| `python-dotenv` | 1.2.4 |

### 4. Install ffmpeg

`elevenlabs.play()` does not decode audio itself — it shells out to **`ffplay`**, which
ships with ffmpeg. Without it the script fails at the `play(audio)` call with:

```
ValueError: ffplay from ffmpeg not found, necessary to play audio.
```

Note this error is raised *after* the API request has been made and billed, so install
ffmpeg before your first run.

```bash
# macOS
brew install ffmpeg

# Debian / Ubuntu
sudo apt install ffmpeg

# Windows
winget install ffmpeg
```

Confirm it is on your PATH:

```bash
which ffplay   # → /opt/homebrew/bin/ffplay
```

### 5. Add your API key

Create a `.env` file in the project root:

```bash
ELEVENLABS_API_KEY=your-api-key-here
```

Get a key from [elevenlabs.io](https://elevenlabs.io) → Profile → API Keys.
`load_dotenv()` reads this file at startup. The `.env` file is gitignored — never commit it.

### 6. Run it

```bash
python example.py
```

Expected result: exit code 0, no terminal output, and the line *"The first move is what
sets everything in motion."* plays through your speakers.

If you did not activate the venv in step 2, call the interpreter directly instead:

```bash
.venv/bin/python example.py
```

## How example.py works

```python
audio = elevenlabs.text_to_speech.convert(
    text="The first move is what sets everything in motion.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",  # "George"
    model_id="eleven_v4",
    output_format="mp3_44100_128",
)
play(audio)
```

- **`convert()` returns a lazy iterator of bytes.** The HTTP request does not actually fire
  until something consumes it — here, `play()`. If you are debugging, note that an
  exception raised on the `convert()` line is rarely the API; force the call with
  `b"".join(audio)`.
- **`voice_id`** — `JBFqnCBsd6RMkjVDRZzb` is the stock "George" voice. Browse others at
  [elevenlabs.io/app/voice-library](https://elevenlabs.io/app/voice-library).
- **`model_id`** — `eleven_v4`. See `.agents/skills/text-to-speech/` for notes on voice
  settings and streaming.

### Saving to a file instead of playing

This path needs no ffmpeg at all:

```python
with open("output.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
```

## Second sample: dialogue with audio tags

`example-text-to-dialogue-websocket/` holds two Text-to-Dialogue WebSocket samples.
`text-to-dialogue-websocket.py` is the minimal reference. `dialogue-audio-tags.py` drives the same
endpoint with a tag-heavy line and exposes the model and voice as flags:

```bash
python example-text-to-dialogue-websocket/dialogue-audio-tags.py --play
python example-text-to-dialogue-websocket/dialogue-audio-tags.py --model eleven_v4
```

| Flag | Default | Purpose |
| --- | --- | --- |
| `--model` | `eleven_v4_turbo` | TTD model id. Must start with `eleven_v3` or `eleven_v4`. |
| `--voice` | `emSmWzY0c0xtx5IFMCVv` | Voice id to register on the socket. |
| `--play` | off | Play the result through `ffplay` after writing. |

Output is written next to the script at `example-text-to-dialogue-websocket/output/`, with the model
name in the filename so runs don't overwrite each other.

### Notes on the dialogue WebSocket

- **Buffering.** TTD holds text until it has roughly 40 characters and 8 words before emitting audio.
  Short lines appear to hang. Send more text per frame, or `{"flush": true}`. This is why the
  minimal sample pads with a long filler line. `close_socket` flushes whatever is still buffered.
- **Voice count by model.** `eleven_v4_turbo` registers exactly one voice; `eleven_v4` allows up to 10.
- **Audio tags.** ElevenLabs documents a vocabulary (`[chuckles]`, `[laughs]`, `[whispers]`,
  `[sighs]`, `[excited]`, `[short pause]`, `[long pause]`, …), but non-standard phrasings like
  `[nervous giggle]` or `[awkward pause]` are interpreted rather than read aloud in practice. The
  docs do warn a tag "can occasionally be interpreted as a request for a sound effect rather than a
  delivery instruction" — if a tag ever leaks into the speech, rephrase it to a documented one.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'elevenlabs'` | venv not activated, or deps installed into a different interpreter | Re-run step 2, or use `.venv/bin/python` |
| `ValueError: ffplay from ffmpeg not found` | ffmpeg missing from PATH | Step 4 |
| `401 Unauthorized` | `.env` missing, misnamed key, or invalid key | Check `ELEVENLABS_API_KEY` in `.env` |
| Runs with exit 0 but no sound | Audio played to a muted or non-default output device | Check system volume and output device |

## Project layout

```
.
├── .agents/skills/text-to-speech/   # reference docs: voice settings, streaming, install
├── .env                             # your API key (gitignored)
├── .gitignore
├── .venv/                           # virtual environment (gitignored)
├── example.py                       # simplest case: text to speech, played aloud
├── example-text-to-dialogue-websocket/
│   ├── text-to-dialogue-websocket.py   # minimal TTD WebSocket reference
│   ├── dialogue-audio-tags.py          # TTD with audio tags, --model / --voice / --play
│   └── output/                         # generated mp3s (gitignored)
└── README.md
```
