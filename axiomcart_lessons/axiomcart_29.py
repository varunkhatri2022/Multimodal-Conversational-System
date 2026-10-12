# Lesson 29: voice is a wrapper around the text assistant: STT -> graph -> TTS.
#
# The graph never knows voice exists. Only the loop around it changes:
#   text mode:   input()  -> graph -> print()
#   voice mode:  listen() -> graph -> speak()
#     listen() = microphone + Whisper (speech-to-text, STT)
#     speak()  = OpenAI TTS (text-to-speech) + speaker
# The HITL question from lesson 26/27 is spoken too, and the answer is heard.
# AxiomCart: voice.py has the real listen/speak; main.py's voice_loop() is this loop.
# Fake listen/speak below, so it runs without a microphone or an API key.
# Which real speech models AxiomCart uses, other options and prices: axiomcart_29_speech_models.md

what_the_customer_says = ["Where is my order?", "ORD102", "Any headphones?", "Goodbye."]


def listen() -> str:
    # Real version: record 5 seconds from the mic, send the audio to Whisper.
    text = what_the_customer_says.pop(0)
    print(f"  [mic]     {text}")
    return text


def speak(text: str) -> None:
    # Real version: send the text to OpenAI TTS, play the audio file.
    print(f"  [speaker] {text}")


def assistant(text: str, ask_customer) -> str:
    # Stands in for graph.invoke(...), including one HITL question (interrupt/resume).
    if "order" in text.lower():
        order_id = ask_customer("Could you tell me your order ID?")
        return f"Order {order_id} is delayed by weather."
    return "We have Sony and Bose headphones."


def ask_customer_by_voice(question: str) -> str:
    speak(question)  # the interrupt question is spoken...
    return listen()  # ...and the answer is heard


if __name__ == "__main__":
    speak("Hello! I'm your AxiomCart assistant. How can I help you today?")
    while True:
        text = listen()  # STT
        if text.lower().strip(" .!") in ("goodbye", "bye"):  # Whisper adds punctuation: "Goodbye."
            speak("Goodbye! Have a great day.")
            break
        speak(assistant(text, ask_customer_by_voice))  # graph -> TTS

    # Real-world notes:
    # - Each turn waits for: recording (5 s) + Whisper + the whole graph + TTS.
    # - Answers are written for screens (bullets, prices); TTS reads them as-is.
