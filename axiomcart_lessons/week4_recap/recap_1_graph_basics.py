# Recap 1: state, nodes, reducers, conditional edges, parallel join, in one graph.
#
#   state   = a TypedDict shared by every node
#   node    = function(state) -> dict of ONLY the keys it changes
#   reducer = Annotated[type, fn]: how several writes to one key are combined
#   edges   = fixed (add_edge), conditional (add_conditional_edges), join (list of sources)

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class TripState(TypedDict):
    request: str
    results: Annotated[list[str], operator.add]  # parallel writes are appended, not overwritten
    summary: str


def route(state: TripState) -> list[str]:
    # A router returns WHERE TO GO (one name or a list); it does not change state.
    # Returning two names starts both nodes in parallel in the same step.
    return ["flights", "hotels"] if "trip" in state["request"] else ["chat"]


def flights(state: TripState) -> dict:
    return {"results": ["flight: $450"]}


def hotels(state: TripState) -> dict:
    return {"results": ["hotel: $160/night"]}


def chat(state: TripState) -> dict:
    return {"summary": "Happy to help!"}


def combine(state: TripState) -> dict:
    return {"summary": " + ".join(state["results"])}


builder = StateGraph(TripState)

builder.add_node("flights", flights)
builder.add_node("hotels", hotels)
builder.add_node("chat", chat)
builder.add_node("combine", combine)

builder.add_conditional_edges(START, route, ["flights", "hotels", "chat"])
builder.add_edge(["flights", "hotels"], "combine")  # join: waits for BOTH
builder.add_edge("combine", END)
builder.add_edge("chat", END)
graph = builder.compile()


if __name__ == "__main__":
    for request in ["plan a trip to Paris", "hello"]:
        print(f"{request!r:24} -> {graph.invoke({'request': request, 'results': [], 'summary': ''})['summary']}")
    # Remove the operator.add reducer and run again: two parallel writes to "results"
    # raise InvalidUpdateError ("Can receive only one value per step").
