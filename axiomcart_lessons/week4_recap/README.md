# Week 4 Recap (for Week 5 learners)

A fast refresher on the Week 4 multi-agent concepts that AxiomCart builds on. It assumes you know Python, have called an LLM API, and know roughly what an "agent" is.

- **Did Week 4?** Skim this page (5 min), then go to lesson 20.
- **Skipped Week 4?** Read this page and run the five files (30–45 min), then go to lesson 20.

All five files run offline: `python recap_1_graph_basics.py`

| File | What it covers | Used in AxiomCart as |
| --- | --- | --- |
| [recap_1_graph_basics.py](recap_1_graph_basics.py) | State, nodes, reducers, routing, parallel + join | `AxiomCartState`, `graph.py` |
| [recap_2_tool_loop.py](recap_2_tool_loop.py) | The model ⇄ tools loop that every agent runs | `product_subgraph`, `support_subgraph` |
| [recap_3_orchestrator_send.py](recap_3_orchestrator_send.py) | Orchestrator → `Send` fan-out → synthesizer | `orchestrator_node`, `synthesizer_node` |
| [recap_4a_checkpointer_problem.py](recap_4a_checkpointer_problem.py) | `thread_id` memory and the "results never clear" trap | `MemorySaver` |
| [recap_4b_checkpointer_fix.py](recap_4b_checkpointer_fix.py) | The fix: a reducer where `[]` means reset | `agent_results_reducer` |

For the bigger picture, see [agent_frameworks_ecosystem.md](agent_frameworks_ecosystem.md): where LangChain, LangGraph and LangSmith fit, and how Microsoft Agent Framework, Semantic Kernel, AutoGen, CrewAI and others compare.

## The 8 ideas to keep

1. **A LangGraph app is a state machine.** State is a `TypedDict`. Nodes are functions that return only the keys they change. `compile()` makes it runnable, and `invoke()` / `stream()` run it.
2. **Reducers decide how writes combine.** `Annotated[list, operator.add]` appends. Without a reducer, the last write wins, and two writes in the same step raise `InvalidUpdateError`.
3. **Routing is a function that returns where to go.** `add_conditional_edges(node, router, [...targets])`. It can return several names to run nodes in parallel. A list of sources in `add_edge([a, b], c)` waits for both.
4. **Tool calling is a loop you own.** The model returns `AIMessage.tool_calls` → you run the tool → you append `ToolMessage(tool_call_id=...)` → you call the model again → no tool calls means done. `ToolNode` and `create_agent` just build this loop for you.
5. **A tool's name, docstring, and argument schema are its prompt.** The LLM sees only those, never your code (`@tool`, optionally with a Pydantic `args_schema`).
6. **The router returns structured data.** `llm.with_structured_output(PydanticModel)` turns the routing decision into a validated object: a list of tasks, each naming an agent.
7. **`Send(node, payload)` creates one run per task.** The payload is that run's input only. What the node *returns* is merged into the main state through the reducers.
8. **Checkpointer + `thread_id` = memory.** State is saved per thread, and the next `invoke` continues from it. Lists with `operator.add` are never cleared, so add a reset or old results leak into new turns.

## The Week 4 architecture in one picture

```
START → orchestrator ──Send──┬─► search agent  (model ⇄ tools loop) ──┐
         (structured output)  └─► planner agent (model ⇄ tools loop) ──┴─► synthesizer → END
```

AxiomCart keeps this shape and changes three things:

| Week 4 notebook | AxiomCart (Week 5) |
| --- | --- |
| Each tool loop wired into the main graph, with shared `search_messages` / `planner_messages` | Each agent's loop is a **private subgraph** run inside one node (lesson 21) |
| `add_conditional_edges` + a dispatch function | The orchestrator returns `Command(goto=[Send...])` (lesson 22) |
| `operator.add` results pile up across turns | A reducer where `[]` resets (lesson 23) |

Then Week 5 adds what's new: RAG over a product catalog, human-in-the-loop with `interrupt()`, and voice I/O.
