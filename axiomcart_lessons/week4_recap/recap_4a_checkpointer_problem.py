# Recap 4a: checkpointer + thread_id = conversation memory, and its classic trap.
#
#   graph = builder.compile(checkpointer=InMemorySaver())
#   graph.invoke(new_input, {"configurable": {"thread_id": "user-1"}})
# State is saved after every step under thread_id. The next invoke on the same thread
# starts from the saved state, and the new input is merged in THROUGH THE REDUCERS.
#
# Trap: an operator.add list is never cleared. Returning [] adds nothing, so last turn's
# results stay. (This is how the Week 4 notebook "remembered" turn 1 by accident.)
# The fix is in recap_4b_checkpointer_fix.py.

import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    user_query: str
    agent_results: Annotated[list[str], operator.add]  # old + new, never cleared


def orchestrator(state: State) -> dict:
    return {"agent_results": []}  # meant as "start this turn fresh", but old + [] = old


def agent(state: State) -> dict:
    return {"agent_results": ["answer to " + state["user_query"]]}


builder = StateGraph(State)
builder.add_node("orchestrator", orchestrator)
builder.add_node("agent", agent)
builder.add_edge(START, "orchestrator")
builder.add_edge("orchestrator", "agent")
builder.add_edge("agent", END)
graph = builder.compile(checkpointer=InMemorySaver())  # saves state after every step


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "user-1"}}  # same thread = same memory

    turn1 = graph.invoke({"user_query": "plan Jaipur"}, config)
    print("turn 1 agent_results:", turn1["agent_results"])
    # ['answer to plan Jaipur']

    turn2 = graph.invoke({"user_query": "hotels there"}, config)
    print("turn 2 agent_results:", turn2["agent_results"])
    # ['answer to plan Jaipur', 'answer to hotels there']   <- turn 1's answer leaked in
