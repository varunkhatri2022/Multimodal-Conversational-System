# Lesson 28: which answer goes to which interrupt?
#
# THE PROBLEM: lesson 26 had one question and one answer. Real agents can ask more:
#   A. one node asks two questions in a row ("Order ID?", then "Email?")
#   B. two agents running in parallel ask at the same time
#   How does Command(resume=...) know which question it answers?
#
# THE FIX:
#   A. In a row: answers are matched BY ORDER. Only one question waits at a time.
#      Each resume reruns the node from its first line; earlier answers are replayed
#      from the checkpoint. Rule: always call the interrupts in the same order.
#   B. At the same time: each pending interrupt has an id. Resume with a dict
#      {interrupt_id: answer}. A plain value raises an error.
#
# AxiomCart: only support_agent interrupts, so main.py answers __interrupt__[0]
# with a plain value. If two agents could ask at once, it would need case B.

import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    answers: Annotated[list[str], operator.add]


# ── A. Two questions in a row, in one node ──
def support(state: State) -> dict:
    print("  support starts")                    # runs again on every resume
    order_id = interrupt("Order ID?")
    print("  order_id =", order_id)
    email = interrupt("Email?")
    print("  email    =", email)
    return {"answers": [order_id + " / " + email]}


builder_a = StateGraph(State)
builder_a.add_node("support", support)
builder_a.add_edge(START, "support")
builder_a.add_edge("support", END)
graph_a = builder_a.compile(checkpointer=InMemorySaver())


# ── B. Two agents in parallel, both ask ──
def support_agent(state: State) -> dict:
    order_id = interrupt("support: Order ID?")
    return {"answers": ["support got " + order_id]}


def product_agent(state: State) -> dict:
    budget = interrupt("product: What budget?")
    return {"answers": ["product got " + budget]}


builder_b = StateGraph(State)
builder_b.add_node("support_agent", support_agent)
builder_b.add_node("product_agent", product_agent)
builder_b.add_edge(START, "support_agent")       # both start in the same step
builder_b.add_edge(START, "product_agent")
builder_b.add_edge("support_agent", END)
builder_b.add_edge("product_agent", END)
graph_b = builder_b.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    print("A. Two questions in a row")
    config = {"configurable": {"thread_id": "a"}}
    result = graph_a.invoke({"answers": []}, config)
    print("Asks:", result["__interrupt__"][0].value)
    result = graph_a.invoke(Command(resume="ORD102"), config)
    print("Asks:", result["__interrupt__"][0].value)
    result = graph_a.invoke(Command(resume="priya@example.com"), config)
    print("Done:", result["answers"])

    print("\nB. Two agents ask at the same time")
    config = {"configurable": {"thread_id": "b"}}
    result = graph_b.invoke({"answers": []}, config)
    for pending in result["__interrupt__"]:
        print("Asks:", pending.value, "  (has its own pending.id) ", pending.id)

    try:
        graph_b.invoke(Command(resume="ORD102"), config)   # plain value: which question?
    except RuntimeError as error:
        print("Plain resume fails:", str(error).split(".")[0])

    # Scripted customer replies, keyed by question.
    replies = {"support: Order ID?": "ORD102", "product: What budget?": "Rs 5,000"}
    answers = {}
    for pending in result["__interrupt__"]:
        answers[pending.id] = replies[pending.value]       # ex: {"629b...": "ORD102", ...}
    result = graph_b.invoke(Command(resume=answers), config)
    print("Done:", result["answers"])
