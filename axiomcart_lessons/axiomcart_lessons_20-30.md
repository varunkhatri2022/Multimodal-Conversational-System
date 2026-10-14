# AxiomCart: Lessons 20–29

These lessons continue the Week 4 travel-planner lessons (1–15). New to Week 4? Start with [week4_recap/](week4_recap/README.md). They bridge from the **Multi-Agent Travel Planner notebook** to **`axiomcart-ai-assistant/src`**. Like the Week 4 lessons, they are small and local: scripted rules stand in for LLM calls, so you need no API keys, the output is the same on every run, and nothing costs money.

Run them with any environment that has `langgraph` and `langchain-core` (the Week 4 `.venv` works):

```bash
python axiomcart_lessons/axiomcart_20.py
```

| Lesson | Concept | Where it lives in `src/` |
| --- | --- | --- |
| [20](axiomcart_20.py) | Why tool loops inside a `Send` fan-out break (the notebook's design) | Motivation for `nodes.py` subgraphs |
| [21](axiomcart_21.py) | Agent = compiled model ⇄ tools **subgraph** called inside one node | `product_subgraph`, `product_agent()` |
| [22](axiomcart_22.py) | `Command(update=..., goto=[Send...])` instead of conditional edges | `orchestrator_node`, `graph.py` (only 2 edges) |
| [23](axiomcart_23.py) | Custom reducer that resets between turns | `agent_results_reducer` in `state.py` |
| [26](axiomcart_26.py) | `interrupt()` / `Command(resume=...)` basics, node re-execution | `support_model`, `main.py` resume loop |
| [27](axiomcart_27.py) | HITL inside a subgraph inside a parallel branch | `support_subgraph` + `support_agent()` |
| [29](axiomcart_29.py) | Voice as an adapter: STT → graph → TTS ([speech models and pricing](axiomcart_29_speech_models.md)) | `voice.py`, `voice_loop()` |

After lesson 29, move to the real project in `axiomcart-ai-assistant/src` (reading order below). To try it, use [axiomcart_sample_questions.md](axiomcart_sample_questions.md).

## Concept map: notebook → AxiomCart

| Travel Planner notebook | AxiomCart `src/` | Why it changed |
| --- | --- | --- |
| `classify_query_parallel` + `dispatch_to_agents` (conditional edge) | `orchestrator_node` returns `Command(goto=[Send...])` | Routing and state update in one place |
| `search_agent_node` ⇄ `search_tool_node` wired into the main graph | `product_subgraph` invoked inside `product_agent` | Private history per task; whole loop runs in one main-graph step |
| `search_messages`, `planner_messages` channels | none: each subgraph has its own `messages` | No cross-task collisions, no leaks between turns |
| `agent_results: operator.add` | `agent_results_reducer` (empty list = reset) | Stops old turns' results leaking into new ones |
| Tavily web search, SerpAPI | Chroma vector search over a local catalog | Answers grounded in your own data (RAG) |
| none | `interrupt()` + `Command(resume=...)` | Ask the customer for missing info mid-run |
| none | Whisper STT + TTS | Multimodal input and output |

## Reading order for `src/`

1. `data.py`: the world the agents can see (4 orders, ~10 products, policies).
2. `config.py`: one shared `llm` (`gpt-4o`, temp 0.3) and embeddings. Note it calls `sys.exit(1)` at import when the key is missing.
3. `state.py`: `AxiomCartState`, `WorkerInput`, the reducer.
4. `tools.py` → `rag.py`: what the agents can *do*. `rag.py` embeds the catalog **at import time**.
5. `nodes.py`: the core. Read the subgraphs first, then `orchestrator_node`, the agents, and `synthesizer_node`.
6. `graph.py`: just 2 edges, because `Command` supplies the rest.
7. `main.py`: the session, `thread_id`, and the interrupt/resume loop.
8. `voice.py`: the I/O adapter.

## Verified behaviors worth knowing (expert notes)

Each was confirmed by running the real `nodes.py`/`graph.py` with a stubbed LLM, or by the lesson named.

1. **Code before `interrupt()` runs twice.** On resume, `support_agent` restarts, re-invokes the subgraph, and `support_model` calls the LLM again before `interrupt()` returns. The question the customer saw and the `AIMessage` kept in history come from different LLM calls (lesson 27).
2. **Parallel siblings are not re-run on resume.** `product_agent` finished in the same step, so LangGraph kept its write. Only the interrupted branch re-executes (lesson 27).
3. **The HITL trigger is a guess.** "No tool call and no tool used yet" is treated as "asking the customer". A support answer that needs no tool (for example, a shipping-policy question) is shown as `Agent asks: ...` and blocks the turn. The guess re-fires after every reply until a tool is called (`nodes.py`, `support_model`). A sturdier design is an explicit `ask_customer` tool.
4. **Memory holds only customer turns.** Nothing appends the assistant's answer to `messages`. Also, the orchestrator classifies `user_query` with no history, although the README says it sees prior context (`nodes.py`, `build_context()`).
5. **`Send("synthesizer", {})` gives the synthesizer an empty state.** That works here only because "no results" is the intended outcome (`nodes.py`, `orchestrator_node`).
6. **The reset reducer is order-sensitive.** Any worker that returns `agent_results: []` wipes the results of its siblings (`state.py`, `agent_results_reducer`).
7. **Price filters do not work through semantic search.** "Under ₹5,000" ranks expensive headphones first. Price is stored as metadata but never filtered on (`rag.py`, `tools.py`).
8. **Docstrings are prompts.** `escalate_to_human` says it sends an email, but that code is commented out. `normalise_order_id("order 101")` returns `ORDER 101` (`tools.py`).
9. **Stale docs.** The docstrings in the `nodes.py` header and `support_agent` describe the older "answer arrives on the next turn" design, not `interrupt()`. The orchestrator's fallback comment says "defaulting to support_agent", but the code routes to the synthesizer.
10. **Checkpoint serialization.** `tasks: list[AgentTask]` stores Pydantic objects in the checkpoint. LangGraph 1.x warns "Deserializing unregistered type…" and says a future version will block it. Store `model_dump()` dicts instead (`state.py`).
11. **Voice details.** Whisper returns `"Goodbye."`, which does not match the exit check `"goodbye"`. `main.py` imports `voice.py` at the top level, so text mode also needs `sounddevice` (lesson 29).

## Check your understanding

Try to answer each question before opening it.

<details><summary>1. Why can the notebook's synthesizer run twice, but AxiomCart's runs once?</summary>
In the notebook, each agent's tool loop is a series of main-graph steps. A branch that finishes early triggers the synthesizer while the other branch is still looping. In AxiomCart each loop runs inside one node call, so both agents finish in the same step and trigger the synthesizer together.
</details>

<details><summary>2. A Send payload contains <code>user_query = task.user_query</code>. Which <code>user_query</code> does the notebook's search agent see on its second call?</summary>
The original query from the main state. A Send payload is the input for that one task. When the tool node loops back, the agent node is triggered by an edge and reads the main state.
</details>

<details><summary>3. What does <code>Command[Literal["synthesizer"]]</code> in a return annotation do?</summary>
It tells LangGraph which nodes this node may jump to. LangGraph uses it to draw the graph and to validate it, because there are no edges declared for those hops.
</details>

<details><summary>4. On resume after an interrupt, which code runs again?</summary>
The interrupted node, from its first line. That includes the outer `support_agent` node and the inner `support_model`, so the LLM call before `interrupt()` repeats. Nodes that finished in the same step are not re-run.
</details>

<details><summary>5. Why does <code>orchestrator_node</code> write <code>agent_results: []</code>?</summary>
To clear last turn's results, which the checkpointer would otherwise keep. With `operator.add` (Week 4), they would accumulate. The custom reducer treats `[]` as a reset.
</details>

<details><summary>6. Why can't you resume an interrupted graph that has no checkpointer?</summary>
The paused state must be saved somewhere under a `thread_id`. Without a checkpointer, `invoke()` still reports `__interrupt__`, but `Command(resume=...)` raises a RuntimeError.
</details>

<details><summary>7. A customer says "show me the cheaper one" after a product answer. What context does each node have?</summary>
The orchestrator has only the current sentence. The product agent gets `build_context(messages)`, which holds the customer's earlier lines (including this one, twice) and none of the assistant's replies, so it doesn't know which products were shown.
</details>

<details><summary>8. Where would you add a price filter, and how does the LLM supply the number?</summary>
Add a `max_price: int | None` argument to `search_product_catalog`, and pass `filter={"price": {"$lte": max_price}}` to Chroma. The LLM fills `max_price` from the tool schema, the same way it fills `query`.
</details>

<details><summary>9. Why is <code>support_subgraph.invoke()</code> inside a node still checkpointed?</summary>
A subgraph invoked inside a node picks up the parent's run config, including the checkpointer and namespace. That is what lets `interrupt()` inside it pause and later resume the whole graph.
</details>

<details><summary>10. How would you test the multi-agent routing without paying for LLM calls?</summary>
Do what these lessons do: replace `llm` with a scripted object that has `bind_tools` / `with_structured_output` / `invoke`, then assert on routes, tool calls, and `agent_results`. Put that in pytest with fixed inputs.
</details>
