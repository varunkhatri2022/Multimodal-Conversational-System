# Lesson 22: Command = update the state AND choose the next node, in one return.
#
# THE PROBLEM (recap 3 style):
#   One decision is split across two functions. orchestrator() decides the tasks and
#   saves them in the state. Then a separate dispatch() function reads them back from
#   the state just to decide where to go. Plus graph.py needs an add_conditional_edges
#   line for every routing node, so the routing is spread across three places.
#
# THE FIX: the node that makes the decision also says where to go next.
#
#   Before:  a node returns {...}  +  a conditional edge function picks the next node
#   Now:     a node returns Command(update={...}, goto=...)
#
# Command[Literal[...]] on the return type lists the POSSIBLE next nodes, like the third
# argument of add_conditional_edges. It is only used to draw and check the graph.
# goto= picks the ACTUAL next node(s) at run time: a name, or a list of Sends.
# Because every node says where to go next, the graph needs only 2 edges.
# AxiomCart's nodes.py and graph.py are built this way.

import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send


class State(TypedDict):
    user_query: str
    agent_results: Annotated[list[str], operator.add]
    final_answer: str


def orchestrator(state: State) -> Command[Literal["support_agent", "product_agent", "synthesizer"]]:
    query = state["user_query"].lower()
    targets = []
    if "order" in query:
        targets.append(Send("support_agent", {"task": state["user_query"]}))
    if "headphones" in query:
        targets.append(Send("product_agent", {"task": state["user_query"]}))

    if not targets:
        return Command(goto="synthesizer")  # no agent needed
    return Command(goto=targets)  # e.g. [Send("support_agent", {"task": "My order is late"})]


def support_agent(payload: dict) -> Command[Literal["synthesizer"]]:
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
builder.add_edge(START, "orchestrator")  # the only 2 edges:
builder.add_edge("synthesizer", END)  # everything in between comes from goto=
graph = builder.compile()


if __name__ == "__main__":
    for query in ["My order is late", "show me headphones", "hello there"]:
        result = graph.invoke({"user_query": query, "agent_results": [], "final_answer": ""})
        print(f"{query!r:40} -> {result['final_answer']}")
