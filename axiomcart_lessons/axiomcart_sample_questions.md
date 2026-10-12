# AxiomCart: Sample Questions

Four examples, each adding one layer: a greeting, one agent with a tool, two agents in parallel with a human-in-the-loop question, and voice.

```powershell
cd axiomcart-ai-assistant
python -m src.main            # examples 1-3 (text)
python -m src.main --voice    # example 4 (voice)
```

Keep an eye on the log lines `Orchestrator query=...`, `routing=[...]` and `HITL interrupt: ...`: they show the path each question takes through the graph.

## Example 1: Greeting (no tool, no specialist work)

| Type | `Hi there!` |
| --- | --- |
| Log | `routing=['product_agent']` |
| What happens | The orchestrator sends greetings and small talk to the product agent, which answers directly without calling a tool. |
| Concept | Orchestrator routing with `Command` + `Send` (lesson 22) |
| Code | `main.py` → `graph.py` (2 edges) → `orchestrator_node` in `nodes.py` |

## Example 2: One agent, with a tool

| Type | `Do you have noise-cancelling headphones?` |
| --- | --- |
| Log | `routing=['product_agent']` |
| What happens | The product agent's subgraph calls `search_product_catalog`, which searches the catalog, then answers with the Bose QC45 and Sony WH-1000XM5 and their prices. |
| Concept | An agent is a model ⇄ tools subgraph called inside one node (lesson 21) |
| Code | `product_agent` → `product_subgraph` in `nodes.py` → `tools.py` → `rag.py` |

## Example 3: Two agents in parallel, with an interrupt

| Type | `My order is late, also show me some earbuds` |
| --- | --- |
| Log | `routing=['support_agent', 'product_agent']`, then `HITL interrupt: ...` |
| What happens | Both agents start at the same time. The support agent needs an order ID, so it pauses and asks: **"Agent asks: ... order ID?"** |
| Reply | `ORD102` |
| Then | The graph resumes. The support agent reports ORD102 is delayed by bad weather, the product agent suggests earbuds, and the synthesizer merges both into one reply. |
| Concepts | Parallel agents with `Send` (lesson 22), reset of `agent_results` each turn (lesson 23), `interrupt()` + `Command(resume=...)` (lessons 26, 27) |
| Code | `orchestrator_node` → `support_agent` → `support_model` (`interrupt`) → the `while "__interrupt__"` loop in `main.py` → `synthesizer_node` |

> The answers come from a real LLM, so wording changes between runs. "My order is late" (with no ID) is what makes the support agent ask. Rehearse it once before class.

**Optional follow-up (memory, lesson 28):** after example 3, type `Which of those earbuds is cheapest?` The agents receive the earlier conversation through `build_context()`.

## Example 4: Voice mode

Start with `python -m src.main --voice`. The assistant speaks a welcome, then records 5 seconds at a time.

| Say | What happens |
| --- | --- |
| *"Hi there"* | Same as example 1, but heard by Whisper (speech-to-text) and spoken back (text-to-speech) |
| *"Do you have noise-cancelling headphones?"* | Same as example 2, answer spoken aloud |
| *"My order is late"* | The interrupt question is **spoken**, and your answer is **recorded**. Say *"O R D one zero two"* and check the printed transcript. |

| Concept | Voice is a wrapper: `listen()` → the same graph → `speak()` (lesson 29) |
| --- | --- |
| Code | `voice.py` (`VoiceRecorder`, `VoiceSpeaker`) and `voice_loop()` + the voice branch of `query()` in `main.py` |

> Speak right after the countdown; each recording is only 5 seconds. Whisper adds punctuation ("Goodbye."), which may not end the session; press `Ctrl+C` to stop.

## More questions to try

**Products**

- `Show me phones under 1,00,000`
- `Compare the iPhone 15 Pro Max and the Samsung Galaxy S24 Ultra`
- `I need a laptop for college`
- `Any budget earbuds?`

**Orders**

- `Where is order ORD103?`
- `What is the status of the order for priya.patel@example.com?`
- `I want to talk to a human about ORD102` (escalation)

**Mixed (both agents)**

- `Track ORD101 and recommend headphones`
- `My order ORD102 is delayed. Can you suggest a cheaper alternative?`

## For discussion: questions that show limitations

Use these after the examples, and ask the class *why* the result looks the way it does.

| Type this | What happens | Why |
| --- | --- | --- |
| `Wireless headphones under 5000` | Expensive headphones come first | Similarity search matches words and meaning, not prices. The price is stored but never used as a filter. |
| `What is your shipping policy?` | The answer may be shown as a question, and the assistant waits for your reply | The assistant treats "no tool call yet" as "asking the customer a question". |
| `Tell me more about the second one` (right after a product list) | It may not know which product you mean | The agents see the customer's earlier messages, but not the assistant's earlier answers. |
| `order 101` | Order not found | The order-ID cleanup turns "order 101" into "ORDER 101". |
