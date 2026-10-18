# Quiz 2: AxiomCart Patterns

Four questions on lessons 20–29. Pick one answer for each. Click **Show answers** at the bottom to reveal them.

---

### Question 1: Why the synthesizer runs twice (lessons 20, 21)

**Lesson 20:** the trip agent's tool loop is wired into the main graph.

```python
class State(TypedDict):
    results: Annotated[list[str], operator.add]
    trip_messages: Annotated[list[str], operator.add]

def dispatch(state: State) -> list[Send]:
    return [Send("hotel_agent", {"task": "hotels in Jaipur"}),
            Send("trip_agent", {"task": "3-day Jaipur plan"})]

builder.add_conditional_edges(START, dispatch, ["hotel_agent", "trip_agent"])
builder.add_edge("hotel_agent", "synthesizer")                                # 1 step
builder.add_conditional_edges("trip_agent", route_trip, ["tool", "synthesizer"])
builder.add_edge("tool", "trip_agent")                                        # loop: 3 steps
```

Result: `synthesizer` runs **twice**, the first time with only the hotel result.

**Lesson 21:** the same agents, but `trip_agent` runs its loop inside a subgraph:

```python
def trip_agent(payload: dict) -> dict:
    trip_subgraph.invoke({"task": payload["task"], "messages": []})   # think -> tool -> think
    return {"results": ["trip_agent: " + payload["task"]]}

builder.add_edge("hotel_agent", "synthesizer")
builder.add_edge("trip_agent", "synthesizer")
```

Result: `synthesizer` runs **once**, with both results. Why?

- A) Lesson 21 uses a join edge: `add_edge(["hotel_agent", "trip_agent"], "synthesizer")`
- B) The synthesizer checks whether all results have arrived before running
- C) The whole tool loop runs inside one main-graph node, so both agents finish in the same step
- D) A checkpointer makes the graph wait for the slow agent

---

### Question 2: `Command` (lesson 22)

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

---

### Question 3: What reruns on resume (lessons 26, 27)

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

---

### Question 4: Adding voice (lesson 29)

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

---

<details>
<summary><b>Show answers</b></summary>

**1. C) The loop runs inside one node.**
The synthesizer runs once for each branch that reaches it, and branches of different lengths reach it at different times. Moving the tool loop into a subgraph makes `trip_agent` one main-graph step, the same as `hotel_agent`, so both finish together. A join edge (A) does not work with `Send`, because you do not know in advance which agents will run. (L20, L21)

**2. A) It lists the possible next nodes.**
It plays the same role as the third argument of `add_conditional_edges`. It is not three fixed edges: `goto=` decides at run time where the graph actually goes. That is why the graph needs only two edges. (L22)

**3. B) `support_agent` from its first line; `product_agent` does not rerun.**
On resume, every node on the path to the `interrupt()` reruns from its first line: the outer node `support_agent` and the paused node `ask_customer` inside the subgraph. `product_agent` finished in the same step, so its result was saved and it is not run again. Any expensive work *before* `interrupt()` runs twice. (L26, L27)

**4. C) Nothing changes in the graph.**
Voice is a wrapper: speech-to-text before the graph, text-to-speech after it. In AxiomCart the interrupt question is spoken too, and the answer is heard. The graph only ever sees text. (L29)

</details>
