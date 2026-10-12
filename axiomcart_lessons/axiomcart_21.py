# Lesson 21: the FIX, each agent's loop runs as a private subgraph.
#
# Same scenario as axiomcart_20.py. The only change: trip_agent's loop
# (think -> tool -> think) moves into its own SUBGRAPH, called with .invoke()
# inside ONE main-graph node.
#   1. The task is stored in the subgraph's own state, so every call in the loop sees it.
#   2. The whole loop finishes inside one main-graph step, so synthesizer runs ONCE.

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


# ── The subgraph: trip_agent's private loop ──
class TripState(TypedDict):
    task: str
    messages: Annotated[list[str], operator.add]  # private: never in the main state


def think(state: TripState) -> dict:
    print("    think sees task =", repr(state["task"]))
    if not state["messages"]:  # 1st call: ask for the tool
        return {"messages": ["need tool"]}
    return {"messages": ["done"]}


def tool(state: TripState) -> dict:
    return {"messages": ["tool result"]}


def route_think(state: TripState) -> str:
    if state["messages"][-1] == "need tool":
        return "tool"
    return END


sub = StateGraph(TripState)
sub.add_node("think", think)
sub.add_node("tool", tool)
sub.add_edge(START, "think")
sub.add_conditional_edges("think", route_think, ["tool", END])
sub.add_edge("tool", "think")  # the loop lives in the SUBGRAPH now
trip_subgraph = sub.compile()


# ── The main graph: one node per agent, no loop here ──
class State(TypedDict):
    results: Annotated[list[str], operator.add]  # no trip_messages: the loop history stays private


def dispatch(state: State) -> list[Send]:
    return [
        Send("hotel_agent", {"task": "hotels in Jaipur"}),
        Send("trip_agent", {"task": "3-day Jaipur plan"}),
    ]


def hotel_agent(payload: dict) -> dict:
    return {"results": ["hotel_agent: " + payload["task"]]}


def trip_agent(payload: dict) -> dict:
    print("  trip_agent starts its subgraph")
    trip_subgraph.invoke({"task": payload["task"], "messages": []})  # runs the WHOLE loop here
    return {"results": ["trip_agent: " + payload["task"]]}


def synthesizer(state: State) -> dict:
    print("  synthesizer runs with", state["results"])
    return {}


builder = StateGraph(State)
builder.add_node("hotel_agent", hotel_agent)
builder.add_node("trip_agent", trip_agent)
builder.add_node("synthesizer", synthesizer)
builder.add_conditional_edges(START, dispatch, ["hotel_agent", "trip_agent"])
builder.add_edge(["hotel_agent", "trip_agent"], "synthesizer")  # join: wait for both agents
builder.add_edge("synthesizer", END)
graph = builder.compile()


if __name__ == "__main__":
    graph.invoke({"results": []})
    # Expected:
    #   trip_agent starts its subgraph
    #     think sees task = '3-day Jaipur plan'
    #     think sees task = '3-day Jaipur plan'                          <- still knows its task
    #   synthesizer runs with ['hotel_agent: ...', 'trip_agent: ...']    <- once, with both
