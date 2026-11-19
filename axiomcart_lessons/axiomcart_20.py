# Lesson 20: the PROBLEM with tool loops inside a Send fan-out.
#
# Two agents run in parallel (Send):
#   hotel_agent -> answers right away         (1 step)
#   trip_agent  -> calls a tool, then answers (a loop: trip_agent -> tool -> trip_agent)
#
# The loop is wired into the MAIN graph, and a join edge waits for both agents.
# Watch for two problems:
#   A. synthesizer runs too EARLY, with only the hotel result. The join waits for
#      trip_agent to RUN once, not for its loop to FINISH.
#   B. trip_agent's 2nd call has lost its task (the Send payload is for the 1st call only).
# axiomcart_21.py is the same scenario, fixed with a subgraph.

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


class State(TypedDict):
    results: Annotated[list[str], operator.add]
    trip_messages: Annotated[list[str], operator.add]  # trip_agent's loop history, in the MAIN state


def dispatch(state: State) -> list[Send]:
    return [
        Send("hotel_agent", {"task": "hotels in Jaipur"}),
        Send("trip_agent", {"task": "3-day Jaipur plan"}),
    ]


def hotel_agent(payload: dict) -> dict:
    return {"results": ["hotel_agent: " + payload["task"]]}


def trip_agent(state: dict) -> dict:
    task = state.get("task")  # 1st call: from the Send payload. 2nd call: main state has no "task".
    history = state.get("trip_messages", [])
    print("  trip_agent sees task =", repr(task))

    if not history:  # 1st call: ask for the tool
        return {"trip_messages": ["need tool"]}
    return {"trip_messages": ["done"], "results": ["trip_agent: " + str(task)]}


def tool(state: State) -> dict:
    return {"trip_messages": ["tool result"]}


def route_trip(state: State) -> str:
    if state["trip_messages"][-1] == "need tool":
        return "tool"
    return END  # loop done (the join edge below already sent us to synthesizer)


def synthesizer(state: State) -> dict:
    print("  synthesizer runs with", state["results"])
    return {}


builder = StateGraph(State)
builder.add_node("hotel_agent", hotel_agent)
builder.add_node("trip_agent", trip_agent)
builder.add_node("tool", tool)
builder.add_node("synthesizer", synthesizer)
builder.add_conditional_edges(START, dispatch, ["hotel_agent", "trip_agent"])
builder.add_edge(["hotel_agent", "trip_agent"], "synthesizer")  # join: wait for both agents
builder.add_conditional_edges("trip_agent", route_trip, ["tool", END])
builder.add_edge("tool", "trip_agent")  # the loop lives in the main graph
builder.add_edge("synthesizer", END)
graph = builder.compile()


if __name__ == "__main__":
    final = graph.invoke({"results": [], "trip_messages": []})
    print("  final results:", final["results"])
    # Expected:
    #   trip_agent sees task = '3-day Jaipur plan'
    #   synthesizer runs with ['hotel_agent: hotels in Jaipur']     <- too early, half the answer
    #   trip_agent sees task = None                                 <- forgot its task
    #   final results: ['hotel_agent: ...', 'trip_agent: None']     <- trip result came AFTER the answer
