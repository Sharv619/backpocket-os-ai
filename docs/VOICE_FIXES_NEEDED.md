# Voice System — Issues & Required Fixes

**Date:** 2026-04-30  
**Status:** 3 active issues blocking demo quality

---

## Overview

The voice pipeline has three layers:

```
User speaks
  → AudioRecorder (Flutter) captures mic
  → POST /api/voice/command (transcript + screen context)
  → Backend: intent classifier → action handler → speech_response
  → TtsService.speak() → POST /api/voice/tts → ElevenLabs → AudioPlayer
  → User hears response
```

All three layers exist in the codebase. But there are gaps that break the experience.

---

## Issue 1 — Mic Does Not Auto-Start When Screen Opens

### What should happen
User taps the mic FAB → screen opens → microphone starts recording immediately.

### What actually happens
Screen opens. User sees a static "Say something or type a command" empty state. Nothing records until they manually tap the mic icon inside the screen.

### Why
`VoiceInputScreen.initState()` does not call `_startRecording()`. The `_isRecording` flag starts `false` so the waveform animation is never shown and `AudioRecorder` is never started.

### Files to fix
- `flutter_prototype/backpocket_mobile/lib/screens/voice_input_screen.dart`

### Fix
Add `_autoStart()` call inside `initState()`:

```dart
@override
void initState() {
  super.initState();
  _waveController = AnimationController(...);
  _voiceService = VoiceCommandService(...);
  _voiceService.setScreenContext(widget.screenContext);
  
  // Auto-start mic on open (non-web only — web needs user gesture first)
  if (!kIsWeb) {
    WidgetsBinding.instance.addPostFrameCallback((_) => _startRecording());
  } else {
    setState(() => _showTextInput = true); // web falls back to text immediately
  }
}
```

---

## Issue 2 — Chat-Based Invoice Flow Is Broken (Conversational Invoice Creation)

### What should happen
The original flow was a back-and-forth chatbot style:

```
User: "Invoice the Penrith job"
Pip:  "What's the client's name?"
User: "John Smith"
Pip:  "How many hours?"
User: "4 hours, $120 materials"
Pip:  "Got it. Creating invoice for John Smith — 4hrs + $120 materials. Confirm?"
User: taps Confirm
Pip:  "Invoice sent."
```

### What actually happens
The voice screen collects a single command, and the "Invoice" button only appears after the conversation has at least one message. The `_InvoiceSheet` then tries to parse the entire conversation transcript at once — which only works if the user said everything in one sentence. Multi-turn guided questioning is not triggered.

### Why
The `VoiceCommandService.sendTranscript()` does return a `followUpPrompt` field and the screen does render `_buildFollowUpHint()` — the backend multi-turn session system exists. But:

1. The backend intent `construction.quote.invoice` handler is not sending `needs_info = true` with a `follow_up_prompt` asking for missing fields one at a time
2. `_buildFollowUpHint()` only shows a text hint — it does not pre-fill the text box or auto-focus the input, so users don't know they need to answer
3. The `session_id` from the first response needs to be sent back on every follow-up message so the backend can track state — currently `VoiceCommandService._sessionId` is set but `VoiceInputScreen._handleTextSubmit()` does not call `sendTranscript` through the service (it calls `_voiceService.sendTranscript()` which does include session_id — this part is OK)

### Files to fix
- `routes/voice_handlers_construction.py` — make invoice handler ask for missing fields one at a time
- `flutter_prototype/backpocket_mobile/lib/screens/voice_input_screen.dart` — auto-focus text input when follow-up prompt appears

### Fix outline

**Backend** (`routes/voice_handlers_construction.py`) — invoice handler should check for missing params and return a follow-up question:

```python
# Pseudo-logic in handle_invoice_intent()
required = ['client_name', 'labor_hours', 'materials_cost']
missing = [f for f in required if not params.get(f)]

if missing:
    prompts = {
        'client_name':     "What's the client's name?",
        'labor_hours':     "How many hours did the job take?",
        'materials_cost':  "Any materials cost? Say zero if none.",
    }
    return {
        'speech_response':  prompts[missing[0]],
        'follow_up_prompt': prompts[missing[0]],
        'needs_confirmation': False,
        'session_state': {'is_collecting': True, 'collecting_field': missing[0]},
    }
```

**Flutter** — when `followUpPrompt` arrives, auto-focus the text field:

```dart
// In _buildFollowUpHint or after setState sets _response
if (_response?.followUpPrompt != null) {
  FocusScope.of(context).requestFocus(_textFocusNode);
}
```

---

## Issue 3 — AI Does Not Talk Back (TTS Not Called in VoiceInputScreen)

### What should happen
After every AI response, Pip's reply should be spoken aloud using the ElevenLabs voice. The user should be able to have a hands-free conversation.

### What actually happens
The AI response appears as a chat bubble only. No audio plays. The user has to read the screen.

### Why
`VoiceInputScreen` uses `_voiceService.sendTranscript()` and `_voiceService.sendConfirmation()` directly — but it does NOT call `_tts.speak()` after receiving the response. The `TtsService` is instantiated inside `VoiceCommandService` and `_speakResponse()` is called automatically there — but `VoiceInputScreen` bypasses this by calling the service methods and then only doing `setState()` to update the UI.

The `VoiceCommandService._speakResponse()` **is** called at line 95 inside `sendTranscript()` — but only when the call goes through `processAudio()`. The text-path (`sendTranscript()`) does call `_speakResponse()` at line 93–95 but the `_tts.speak()` call is blocked because `TtsService._fetchAudio()` requires `ELEVENLABS_API_KEY` to be set in `.env`, and `services/elevenlabs.py:is_configured()` returns `false` when the key is missing.

### Two-part fix

**Part A — Backend fallback TTS** (`routes/utilities.py` line 264, `/api/voice/tts`):  
When ElevenLabs is not configured, return a fallback using `pyttsx3` (offline) or `gTTS` (free Google TTS) instead of returning an error. This way TTS works even without an ElevenLabs key.

```python
@router.post("/api/voice/tts")
async def text_to_speech(body: dict):
    text = body.get("text", "")
    if elevenlabs.is_configured():
        audio_bytes = await elevenlabs.synthesize(text, voice=body.get("voice", "male"))
        return Response(content=audio_bytes, media_type="audio/mpeg")
    else:
        # Fallback: gTTS (pip install gTTS)
        from gtts import gTTS
        import io
        tts = gTTS(text=text, lang='en', slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        return Response(content=buf.getvalue(), media_type="audio/mpeg")
```

**Part B — Flutter system TTS fallback** (`flutter_prototype/.../tts_service.dart`):  
If the `/api/voice/tts` call fails (no network, no key), fall back to `flutter_tts` package for on-device speech:

```dart
// pubspec.yaml: add flutter_tts: ^4.0.2
import 'package:flutter_tts/flutter_tts.dart';

// In TtsService:
final FlutterTts _flutterTts = FlutterTts();

Future<void> speak(String text, {String voice = 'male'}) async {
  final bytes = await _fetchAudio(text, voice: voice);
  if (bytes != null) {
    await _playBytes(bytes);          // ElevenLabs / backend TTS
  } else {
    await _flutterTts.speak(text);    // on-device fallback
  }
}
```

---

## Fix Priority

| # | Issue | Impact | Effort |
|---|-------|--------|--------|
| 1 | Mic auto-starts on open | High — demo feels broken without it | 5 min — 3 lines in initState |
| 3 | AI talks back (TTS fallback) | High — core "voice OS" claim | 1 hr — gTTS backend + flutter_tts package |
| 2 | Conversational invoice flow | High — was working before | 2 hrs — backend handler + Flutter focus |

---

## What "Done" Looks Like

```
User taps mic FAB
  → Screen opens, mic starts recording immediately (waveform animates)
  → "Listening…" shown, stop button visible

User speaks: "Invoice the Lane Cove job"
  → AI speaks back: "What's the client's name?"  ← TTS plays audio
  → Text box auto-focuses for response

User types or speaks: "Sarah Webb"
  → AI speaks: "Got it. How many hours on the job?"

User: "Six hours, two-fifty in materials"
  → AI speaks: "Creating invoice for Sarah Webb — 6 hours at $150/hr plus $250 materials. That's $1,150 plus GST. Confirm?"
  → Confirm / Cancel bar appears

User taps Confirm
  → AI speaks: "Invoice sent to Sarah."
  → Screen returns to construction screen, leads refreshed
```

---

## Dependencies Needed

| Package | Where | Purpose |
|---|---|---|
| `gTTS` | `requirements.txt` | Backend TTS fallback (no ElevenLabs key) |
| `flutter_tts: ^4.0.2` | `pubspec.yaml` | Flutter on-device TTS fallback |

ElevenLabs key (`ELEVENLABS_API_KEY`) in `.env` gives the best voice quality — Adam voice, ~400ms latency. Without the key both fallbacks still work.
