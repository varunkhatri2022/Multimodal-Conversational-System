# Recap 5: subgraphs, in simple language

## What is a subgraph?

A subgraph is a small graph used inside a node of a larger graph. It has its own
nodes, edges, and state. The main graph can treat the whole subgraph like one
piece of work: call it, wait for it to finish, then continue.

Think of the main graph as a team manager and a subgraph as one specialist's
private checklist. The manager gives the specialist a task. The specialist can
complete several internal steps without exposing every step to the whole team.

## In this lesson

In [axiomcart_21.py](../axiomcart_21.py), the main graph sends work to two agents:

```text
Main graph
START → hotel_agent ───────────────┐
       trip_agent → trip subgraph ─┴→ synthesizer → END

Trip subgraph (runs inside trip_agent)
START → think → tool → think → END
```

The `trip_agent` calls the compiled subgraph with its task and a fresh message
list:

```python
trip_subgraph.invoke({"task": payload["task"], "messages": []})
```

Inside the subgraph, both visits to `think` can still see the task because
`task` is part of the subgraph's own state. Its `messages` list is private too.
When the loop finishes, `trip_agent` returns one result to the main graph.

## Why use a subgraph?

Without a subgraph, the tool loop would be spread across several main-graph
steps. In the earlier design in [axiomcart_20.py](../axiomcart_20.py), this
caused problems:

- The trip agent's task was in its `Send` input, not in the shared main state.
  When the tool loop returned to the agent through a normal edge, the task was
  no longer available there.
- The synthesizer could run as soon as the hotel agent finished, before the
  trip agent had finished its tool loop.
- Working messages from one agent's tool loop lived in the main state, where
  they could mix with other work.

With the subgraph, the whole `think → tool → think` loop runs during one
`trip_agent` call. The main graph uses an explicit join edge to wait for both
agents:

```python
builder.add_edge(["hotel_agent", "trip_agent"], "synthesizer")
```

Only after both main-graph nodes finish does the synthesizer run with both
results. Each subgraph also keeps its working messages separate from the main
graph's state.

## Main graph state and subgraph state

```text
Main graph state:       results = [hotel result, trip result]

Trip subgraph state:    task = "3-day Jaipur plan"
                        messages = ["need tool", "tool result", "done"]
```

The subgraph's state is not automatically the main graph's state. The outer
`trip_agent` chooses what to return; in this lesson it returns the trip result
in the main state's `results` field.

## Where AxiomCart uses this

In [nodes.py](../../axiomcart-ai-assistant/src/nodes.py),
`product_subgraph` and `support_subgraph` each contain a model-and-tools loop.
The outer `product_agent()` or `support_agent()` calls its subgraph, gets the
finished answer, then returns that answer to the main graph for synthesis.

## Remember

- A **node** is one step in a graph.
- A **subgraph** is a graph used as part of a larger graph's node work.
- Its internal nodes can loop and use their own state.
- The outer node decides what result to pass back to the main graph.
- Use a subgraph when a task has its own multi-step workflow that should stay
  together and separate from the rest of the graph.