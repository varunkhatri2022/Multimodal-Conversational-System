# Quiz 1: Week 4 Recap

Four questions on recap files R1–R4. Pick one answer for each. Click **Show answers** at the bottom to reveal them.

---

### Question 1: Keys a node does not return

```python
class State(TypedDict):
    user_query: str
    tasks: list[dict]
    final_answer: str

def orchestrator(state: State) -> dict:
    return {"tasks": [{"agent": "search_agent", "query": "hotels"}]}
```

Before `orchestrator` runs, the state is:

```python
{"user_query": "Find hotels in Paris", "tasks": [], "final_answer": ""}
```

After `orchestrator` runs, what are `user_query` and `final_answer`?

- A) Both are set to `None`
- B) Both are cleared: `""` and `""`
- C) They stay exactly as they were: `"Find hotels in Paris"` and `""`
- D) LangGraph raises an error because they are missing from the return value

---

### Question 2: Two parallel writes, no reducer

```python
class State(TypedDict):
    user_query: str
    tasks: list[dict]            # no reducer

def search_agent(state: State) -> dict:
    return {"tasks": [{"from": "search"}]}

def planner_agent(state: State) -> dict:
    return {"tasks": [{"from": "planner"}]}
```

A router sends the graph to **both** agents, so they run in the **same step**.

What happens?

- A) LangGraph raises `InvalidUpdateError`
- B) The second write wins: `tasks = [{"from": "planner"}]`
- C) The first write wins: `tasks = [{"from": "search"}]`
- D) The two lists are joined: `tasks = [{"from": "search"}, {"from": "planner"}]`

---

### Question 3: The tool loop

```python
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

def should_continue(state: AgentState) -> str:
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

builder.add_conditional_edges("model", should_continue, ["tools", END])
builder.add_edge("tools", "model")
```

After the `model` node runs, the state is:

```python
{"messages": [
    HumanMessage(content="Where is order ORD102?"),
    AIMessage(content="", tool_calls=[{"name": "get_order_status", "args": {"order_id": "ORD102"}, "id": "call-1"}]),
    ToolMessage(content="ORD102: delayed by weather", tool_call_id="call-1"),
    AIMessage(content="Your order is delayed by weather.", tool_calls=[]),
]}
```

Where does the graph go next?

- A) `tools`
- B) `END`
- C) back to `model`
- D) It crashes, because `tool_calls` is empty

---

### Question 4: Memory with `operator.add`

```python
class State(TypedDict):
    user_query: str
    agent_results: Annotated[list[str], operator.add]

def orchestrator(state: State) -> dict:
    return {"agent_results": []}                         # meant as "start this turn fresh"

def agent(state: State) -> dict:
    return {"agent_results": [state["user_query"]]}      # adds this turn's answer

# orchestrator -> agent -> END
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "user-1"}}

graph.invoke({"user_query": "A"}, config)               # turn 1 ends with agent_results = ["A"]
turn2 = graph.invoke({"user_query": "B"}, config)       # turn 2, same thread_id
```

What is `turn2["agent_results"]`?

- A) `["B"]`
- B) `[]`
- C) `["A", [], "B"]`
- D) `["A", "B"]`

---

<details>
<summary><b>Show answers</b></summary>

**1. C) They stay exactly as they were.**
A node returns only the keys it changes. Every key it does not return is left untouched. (R1)

**2. A) `InvalidUpdateError`.**
`tasks` has no reducer, so LangGraph has no rule for combining two values written in the same step. It stops with an error instead of guessing. Adding a reducer such as `Annotated[list[dict], operator.add]` would give answer D. (R1, R3)

**3. B) `END`.**
The last message is the `AIMessage` with `tool_calls=[]`. An empty list counts as false, so `should_continue` returns `END`: no tool calls means the model has given its final answer. (R2)

**4. D) `["A", "B"]`.**
`operator.add` does `old + new`, and `["A"] + []` is still `["A"]`. Returning `[]` cannot clear the list, so turn 1's answer leaks into turn 2. The fix is a reducer where `[]` means "reset" (R4b). (R4a)

</details>
