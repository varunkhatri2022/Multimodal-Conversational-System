# Lesson 29 extra: Speech models and what they cost

Optional reading for curious learners. Lesson 29 uses fake `listen()` / `speak()` functions; this page explains the real models behind them in AxiomCart, and what else is available.

## 1. What AxiomCart uses

AxiomCart uses a **cascaded pipeline**: three separate models, one after another.

```
your voice ──► whisper-1 ──► text ──► LangGraph agents (gpt-4o) ──► text ──► tts-1 ──► spoken answer
               (STT)                  (the LLM)                              (TTS, voice "nova")
```

| Step | Model | Where in the code | Settings |
| --- | --- | --- | --- |
| Speech-to-text (STT) | OpenAI **`whisper-1`** | `voice.py`, `VoiceRecorder.transcribe()` | 5-second recordings, 16 kHz mono, English |
| Reasoning | OpenAI **`gpt-4o`** | `config.py`, used by every agent | temperature 0.3 |
| Text-to-speech (TTS) | OpenAI **`tts-1`** | `voice.py`, `VoiceSpeaker.speak()` | voice `nova`, speed 1.0, MP3 output |

Only the middle step is an LLM. Whisper and TTS are **speech models**: one turns audio into text, the other turns text into audio.

### What one voice turn costs (speech parts only)

| Part | Price | One turn |
| --- | --- | --- |
| `whisper-1` | $0.006 per minute of audio | 5 s recording ≈ **$0.0005** |
| `tts-1` | $15 per 1M characters | ~400-character answer ≈ **$0.006** |

So the speech parts cost well under one cent per turn. The `gpt-4o` calls made by the agents usually cost more than the speech.

## 2. Speech-to-text (STT) options

| Model / service | Provider | Price (approx.) | Notes |
| --- | --- | --- | --- |
| **whisper-1** *(AxiomCart)* | OpenAI | $0.006 / min | The classic; good accuracy, many languages |
| gpt-4o-transcribe | OpenAI | $0.006 / min | Newer, usually more accurate than Whisper |
| gpt-4o-mini-transcribe | OpenAI | $0.003 / min | Half the price; good enough for most apps |
| Nova-3 | Deepgram | ~$0.0043 / min (batch), ~$0.0077 / min (streaming) | Built for real-time, low latency |
| Universal | AssemblyAI | from ~$0.0025 / min | Low price; extras like speaker labels |
| Chirp | Google Cloud | ~$0.016 / min (cheaper at very high volume) | Fits Google Cloud projects |
| Whisper (open source) | Run it yourself | Free (you pay for the computer) | Runs offline; needs a decent CPU, ideally a GPU |

## 3. Text-to-speech (TTS) options

| Model / service | Provider | Price (approx.) | Notes |
| --- | --- | --- | --- |
| **tts-1** *(AxiomCart)* | OpenAI | $15 / 1M characters | Fast, natural, 6+ preset voices |
| tts-1-hd | OpenAI | $30 / 1M characters | Higher quality, a bit slower |
| gpt-4o-mini-tts | OpenAI | $0.60 / 1M text tokens in + $12 / 1M audio tokens out | You can **instruct** the voice: "sound calm and friendly" |
| Neural voices | Google Cloud | ~$16 / 1M characters (standard voices ~$4) | Free tier: 4M standard characters / month |
| Neural voices | Microsoft Azure | ~$15 / 1M characters (HD ~$22) | Free tier: 500K characters / month |
| Polly | Amazon | $4 (standard) to $30 (generative) / 1M characters | Free tier for the first 12 months |
| ElevenLabs | ElevenLabs | Monthly plans, from a free tier to ~$99+ / month | Most realistic voices; voice cloning |
| Piper, Kokoro (open source) | Run them yourself | Free | Run offline; lower quality than the best cloud voices |

**How long is 1M characters?** About 15–20 hours of speech. At $15 per 1M, one hour of spoken answers costs under $1.

## 4. The other option: one native speech-to-speech model

Instead of three models, a single model **hears audio and speaks audio directly**. This is what you get in ChatGPT's Advanced Voice Mode or Gemini Live.

| Model | Provider | Price (approx.) |
| --- | --- | --- |
| gpt-realtime-2.1 | OpenAI (Realtime API) | $32 / 1M audio tokens in, $64 / 1M out (roughly $0.06–0.11 per minute of conversation) |
| gpt-realtime-2.1-mini | OpenAI (Realtime API) | $10 / 1M audio tokens in, $20 / 1M out |
| Gemini Live (native audio) | Google (Live API) | ~$0.005 / min audio in, ~$0.018 / min audio out |

## 5. Cascaded vs native: why AxiomCart chose cascaded

| | Cascaded (AxiomCart) | Native speech-to-speech |
| --- | --- | --- |
| Speed | Slower: three steps in a row | Fast, close to a human |
| Interrupting it mid-sentence | Hard | Natural |
| Hears your tone (upset, laughing) | No, the tone is lost in the text | Yes |
| Works with tools, agents, `interrupt()` | Easily: everything in the middle is text | Possible, but harder to control |
| Swap one part (cheaper STT, different voice) | Yes | No, it's one model |
| Debugging | Easy: log what was heard and what was said | Harder: it's audio end to end |

AxiomCart's real work happens in the middle (routing, parallel agents, tools, memory, human-in-the-loop), and all of it works on text. A cascaded pipeline lets voice be a thin wrapper around that, which is the point of lesson 29.

---

*Prices checked in October 2026 from the providers' pricing pages and price-comparison sites; they change often, so check the provider before relying on them. Approximate figures are rounded.*

**Sources:**
[OpenAI API pricing](https://developers.openai.com/api/docs/pricing) ·
[Deepgram pricing breakdown (Cekura)](https://www.cekura.ai/blogs/deepgram-pricing) ·
[Speech-to-text pricing 2026 (convertaudiototext)](https://convertaudiototext.com/blog/speech-to-text-api-pricing-2026) ·
[TTS pricing comparison 2026 (TextToLab)](https://texttolab.com/pricing) ·
[Azure TTS pricing (TextToLab)](https://texttolab.com/blog/azure-text-to-speech-pricing) ·
[Gemini Live API pricing (TokenKarma)](https://tokenkarma.app/blog/gemini-live-api-pricing-voice-agents-2026/) ·
[OpenAI Realtime API pricing (Forasoft)](https://www.forasoft.com/article/openai-realtime-api-pricing)
