# Multimodal Conversational System

This repository contains the Week 5 learning materials and **AxiomCart**, a
multi-agent shopping assistant built with Python and LangGraph. It is organized
so you can study the graph concepts with small offline examples before looking
at the larger assistant.

## What is here

| Folder or file | Contents |
| --- | --- |
| `axiomcart_lessons/` | Small, scripted LangGraph lessons about agents, tools, subgraphs, routing, memory, interrupts, and voice. The lesson examples do not need an API key. |
| `axiomcart-ai-assistant/` | The full AxiomCart assistant: product search (RAG), order support, parallel agents, human-in-the-loop, and optional voice input/output. |
| `Agents-ChatGPT-Demo/` | Agent and prompt-pattern learning notes, examples, and images. |
| [Live class slides](Live%20Class%20Slides_Multimodal%20Conversational%20System.pdf) | The accompanying Week 5 class slides. |

The assistant's basic flow is:

```text
customer message
       |
  orchestrator
    /       \
product   support       (either or both agents may run)
    \       /
   synthesizer
       |
  final answer
```

Each specialist uses its own model-and-tools subgraph. The support agent can
pause to ask the customer for missing information and resume after the customer
replies.

## Run an offline lesson

The lesson scripts use fixed examples instead of live model calls, so they are a
good place to start. From the repository root, create an environment and install
the lesson dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\axiomcart_lessons\requirements.txt
python .\axiomcart_lessons\axiomcart_21.py
```

Lesson 21 demonstrates a tool loop inside a subgraph. Other lessons and recap
notes are in `axiomcart_lessons/` and `axiomcart_lessons/week4_recap/`.

## Run the AxiomCart assistant

The assistant makes real OpenAI API calls for language, embeddings, and voice
features. These calls may incur charges. Voice mode also requires a working
microphone and speakers.

```powershell
cd .\axiomcart-ai-assistant
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `axiomcart-ai-assistant/.env` in your editor and add your own
`OPENAI_API_KEY`. Do not put the key in source files or commit `.env`. The
repository ignores `.env` and virtual environments; `.env.example` contains
only a placeholder.

Run a single text query:

```powershell
python -m src.main --query "Where is order ORD102?"
```

For an interactive text session, run `python -m src.main`. For voice mode, run
`python -m src.main --voice`.

## Project notes

- The assistant uses an in-memory checkpointer for conversation state. Its
  checkpoint data is lost when the process exits.
- The product catalog and orders in `src/data.py` are demonstration data, not a
  production database.
- The assistant requires an OpenAI API key; the offline lessons do not.
- The two Python projects have separate dependency files. Install dependencies
  from the folder for the part you plan to run.