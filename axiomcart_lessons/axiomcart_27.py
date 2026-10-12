# Lesson 27: interrupt() inside an agent's subgraph, while another agent runs in parallel.
#
# THE QUESTION: lesson 26 paused a simple node. In AxiomCart, interrupt() sits inside the
#   support agent's SUBGRAPH (lesson 21), and product_agent may run beside it (Send).
#   Does it still work, and what runs again on resume?
#
# THE ANSWER (watch the call counters at the end):
#   - It works: a subgraph called inside a node uses the parent's checkpointer.
#   - product_agent finished in the same step, so its result is kept. It does NOT run again.
#   - support_agent reruns from its first line and calls its subgraph again.
#   - Inside the subgraph, ask_customer reruns from its first line too (lesson 26 rule),
#     so any LLM call before interrupt() would be paid for twice.

import operator
from collections import Counter
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send, interrupt

CALLS = Counter()  # how many times each node ran


# ── The support agent's subgraph: ask for the order ID, then look it up ──
class SupportState(TypedDict):
    order_id: str
    answer: str


def ask_customer(state: SupportState) -> dict:
    CALLS["ask_customer"] += 1
    print("support_agent called subgraph")
    order_id = interrupt("Could you share your order ID?")  # pauses the WHOLE graph
    return {"order_id": order_id}


def look_up(state: SupportState) -> dict:
    CALLS["look_up"] += 1
    return {"answer": state["order_id"] + " is delayed by weather"}


sub = StateGraph(SupportState)
sub.add_node("ask_customer", ask_customer)
sub.add_node("look_up", look_up)
sub.add_edge(START, "ask_customer")
sub.add_edge("ask_customer", "look_up")
sub.add_edge("look_up", END)
support_subgraph = sub.compile()


# ── The main graph: two agents in parallel, then the synthesizer ──
class State(TypedDict):
    results: Annotated[list[str], operator.add]


def dispatch(state: State) -> list[Send]:
    return [
        Send("product_agent", {"task": "show me headphones"}),
        Send("support_agent", {"task": "where is my order?"}),
    ]


def product_agent(payload: dict) -> dict:
    CALLS["product_agent"] += 1
    return {"results": [payload["task"] + " -> Sony XM5"]}


def support_agent(payload: dict) -> dict:
    CALLS["support_agent"] += 1
    print("support_agent called with task:", payload["task"])
    result = support_subgraph.invoke({"order_id": "", "answer": ""})
    return {"results": [payload["task"] + " -> " + result["answer"]]}


def synthesizer(state: State) -> dict:
    CALLS["synthesizer"] += 1
    return {}


builder = StateGraph(State)
builder.add_node("product_agent", product_agent)
builder.add_node("support_agent", support_agent)
builder.add_node("synthesizer", synthesizer)
builder.add_conditional_edges(START, dispatch, ["product_agent", "support_agent"])
builder.add_edge("product_agent", "synthesizer")
builder.add_edge("support_agent", "synthesizer")
builder.add_edge("synthesizer", END)
graph = builder.compile(checkpointer=InMemorySaver())  # needed to pause and resume


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "customer-1"}}
    result = graph.invoke({"results": []}, config)

    while "__interrupt__" in result:  # same loop as main.py: keep answering until done
        question = result["__interrupt__"][0].value
        answer = "ORD102"  # main.py asks the real customer here
        print("Agent asks:", question)
        print("Customer:  ", answer)
        result = graph.invoke(Command(resume=answer), config)

    print("Results:", result["results"])
    print("Calls:  ", dict(CALLS))
    # product_agent=1  finished before the pause, NOT run again
    # support_agent=2  reran from its first line on resume
    # ask_customer=2   reran too (lesson 26 rule), this time interrupt() returned "ORD102"
    # look_up=1, synthesizer=1
