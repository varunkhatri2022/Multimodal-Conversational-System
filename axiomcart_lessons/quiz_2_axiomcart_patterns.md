# Quiz 2: AxiomCart Patterns

---

### Question 1: `Command` (lesson 22)

```python
class State(TypedDict):
    user_query: str
    agent_results: Annotated[list[str], operator.add]
    final_answer: str

def orchestrator(state: State) -> Command[Literal["support_agent", "product_agent", "synthesizer"]]:
    targets = []
    if "order" in state["user_query"].lower():
        targets.append(Send("support_agent", {"task": state["user_query"]}))
    if "headphones" in state["user_query"].lower():
        targets.append(Send("product_agent", {"task": state["user_query"]}))
    if not targets:
        return Command(goto="synthesizer")
    return Command(goto=targets)

builder.add_edge(START, "orchestrator")       # the only two edges
builder.add_edge("synthesizer", END)
```

What does `Command[Literal["support_agent", "product_agent", "synthesizer"]]` in the return type do?

- A) Lists the *possible* next nodes (used to draw and check the graph); `goto=` picks the actual ones at run time
- B) Runs all three nodes after the orchestrator, every time
- C) Lists the state keys the orchestrator is allowed to update
- D) Nothing; it is only a comment for the reader

<details>
<summary><b>Show answer</b></summary>

**A) It lists the possible next nodes.**
It plays the same role as the third argument of `add_conditional_edges`. It is not three fixed edges: `goto=` decides at run time where the graph actually goes. That is why the graph needs only two edges. (L22)

</details>

---

### Question 2: What reruns on resume (lessons 26, 27)

```python
class State(TypedDict):
    results: Annotated[list[str], operator.add]

# Subgraph used by support_agent: START -> ask_customer -> look_up -> END
def ask_customer(state: SupportState) -> dict:
    order_id = interrupt("Could you share your order ID?")
    return {"order_id": order_id}

def product_agent(payload: dict) -> dict:
    return {"results": [payload["task"] + " -> Sony XM5"]}

def support_agent(payload: dict) -> dict:
    result = support_subgraph.invoke({"order_id": "", "answer": ""})
    return {"results": [payload["task"] + " -> " + result["answer"]]}

# dispatch sends to product_agent AND support_agent (same step), both then go to synthesizer
graph = builder.compile(checkpointer=InMemorySaver())
```

The first `invoke` pauses at `interrupt()`. The app then calls:

```python
graph.invoke(Command(resume="ORD102"), config)
```

What runs again?

- A) The whole graph, from `START`
- B) `support_agent` from its first line, which re-enters the subgraph at `ask_customer` (also from its first line); `product_agent` does **not** rerun
- C) Only the line after `interrupt()` in `ask_customer`
- D) Both agents, from their first lines

<details>
<summary><b>Show answer</b></summary>

**B) `support_agent` from its first line; `product_agent` does not rerun.**
On resume, every node on the path to the `interrupt()` reruns from its first line: the outer node `support_agent` and the paused node `ask_customer` inside the subgraph. `product_agent` finished in the same step, so its result was saved and it is not run again. Any expensive work *before* `interrupt()` runs twice. (L26, L27)

</details>

---

### Question 3: Adding voice (lesson 29)

AxiomCart already works in text mode:

```python
while True:
    text = input("You: ")                       # read the customer's message
    answer = assistant.query(text)              # runs the whole graph
    print("Assistant:", answer)
```

Voice mode replaces it with:

```python
while True:
    text = listen()                             # microphone + speech-to-text (Whisper)
    answer = assistant.query(text)              # runs the whole graph
    speak(answer)                               # text-to-speech + speaker
```

What changes **inside the graph** to support voice?

- A) A new `voice_node` is added between `START` and the orchestrator
- B) The state gets an `audio` key that every agent reads
- C) Nothing: `listen()` and `speak()` wrap the same graph, which only ever sees text
- D) Each agent gets a speech tool

<details>
<summary><b>Show answer</b></summary>

**C) Nothing changes in the graph.**
Voice is a wrapper: speech-to-text before the graph, text-to-speech after it. In AxiomCart the interrupt question is spoken too, and the answer is heard. The graph only ever sees text. (L29)

</details>
