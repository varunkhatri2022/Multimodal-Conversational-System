# Recap 4b: the fix for recap 4a's trap: a reducer where [] means "reset".
#
# Same graph as recap_4a_checkpointer_problem.py. Only the reducer on agent_results changes.
# AxiomCart uses this idea (Week 5 lesson 23).

from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


def reset_or_add(current: list, update: list) -> list:
    if update == []:
        return []  # a node returned [] -> clear the list
    return current + update  # otherwise append, like operator.add


class State(TypedDict):
    user_query: str
    agent_results: Annotated[list[str], reset_or_add]  # the only change from 4a


def orchestrator(state: State) -> dict:
    return {"agent_results": []}  # now this really clears last turn's results


def agent(state: State) -> dict:
    return {"agent_results": ["answer to " + state["user_query"]]}


builder = StateGraph(State)
builder.add_node("orchestrator", orchestrator)
builder.add_node("agent", agent)
builder.add_edge(START, "orchestrator")
builder.add_edge("orchestrator", "agent")
builder.add_edge("agent", END)
graph = builder.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "user-1"}}

    turn1 = graph.invoke({"user_query": "plan Jaipur"}, config)
    print("turn 1 agent_results:", turn1["agent_results"])
    # ['answer to plan Jaipur']

    turn2 = graph.invoke({"user_query": "hotels there"}, config)
    print("turn 2 agent_results:", turn2["agent_results"])
    # ['answer to hotels there']   <- only this turn's answer

    # Memory is only as good as what nodes READ. A router that sees only the current
    # query cannot resolve "there". In AxiomCart, build_context() in nodes.py
    # passes the history to the agents.
