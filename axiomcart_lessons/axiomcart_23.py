# Lesson 23: a reducer that resets agent_results at the start of every turn.
#
# THE PROBLEM (lesson 22 + memory):
#   Once the graph remembers the conversation, agent_results is never emptied.
#   Turn 1 asks about an order, turn 2 asks about headphones, and the turn 2 answer
#   still includes the order answer from turn 1. Old answers keep piling up.
#
# THE FIX: the orchestrator says "empty the list" at the start of each turn, and a
#   custom reducer understands that. So each turn's answer has only that turn's results.
#
# Same graph as lesson 22, with two changes:
#   1. A checkpointer, so the state is remembered between turns (same thread_id).
#   2. agent_results uses agent_results_reducer instead of operator.add, and the
#      orchestrator writes "agent_results": [] to clear last turn's results.
#
# Why: with operator.add, [] adds nothing, so turn 2 would still contain turn 1's
# results (the problem in week4_recap/recap_4a_checkpointer_problem.py).
# AxiomCart's state.py and orchestrator_node do exactly this.

from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send


def agent_results_reducer(current: list[str], update: list[str]) -> list[str]:
    # Same as state.py. Like operator.add, but an empty list means "reset".
    if update == []:
        return []
    return current + update


class State(TypedDict):
    user_query: str
    agent_results: Annotated[list[str], agent_results_reducer]  # was operator.add in lesson 22
    final_answer: str


def orchestrator(state: State) -> Command[Literal["support_agent", "product_agent", "synthesizer"]]:
    query = state["user_query"].lower()
    targets = []
    if "order" in query:
        targets.append(Send("support_agent", {"task": state["user_query"]}))
    if "headphones" in query:
        targets.append(Send("product_agent", {"task": state["user_query"]}))

    reset = {"agent_results": []}  # clear last turn's results (runs BEFORE the agents)
    if not targets:
        return Command(update=reset, goto="synthesizer")
    return Command(update=reset, goto=targets)


def support_agent(payload: dict) -> Command[Literal["synthesizer"]]:
    # Always return a result here, never []: with this reducer, [] would wipe the list.
    return Command(update={"agent_results": ["support: " + payload["task"]]}, goto="synthesizer")


def product_agent(payload: dict) -> Command[Literal["synthesizer"]]:
    return Command(update={"agent_results": ["product: " + payload["task"]]}, goto="synthesizer")


def synthesizer(state: State) -> dict:
    answer = " + ".join(state["agent_results"]) or "Sorry, I couldn't process that."
    return {"final_answer": answer}


builder = StateGraph(State)
builder.add_node("orchestrator", orchestrator)
builder.add_node("support_agent", support_agent)
builder.add_node("product_agent", product_agent)
builder.add_node("synthesizer", synthesizer)
builder.add_edge(START, "orchestrator")
builder.add_edge("synthesizer", END)
graph = builder.compile(checkpointer=InMemorySaver())  # remembers state per thread_id


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "user-1"}}  # same thread = same conversation

    for query in ["My order is late", "show me headphones"]:
        result = graph.invoke({"user_query": query}, config)
        print(f"{query!r:22} -> {result['final_answer']}")
    # 'My order is late'     -> support: My order is late
    # 'show me headphones'   -> product: show me headphones
    #                           (with operator.add: support: My order is late + product: show me headphones)
