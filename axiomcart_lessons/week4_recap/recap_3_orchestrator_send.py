# Recap 3: the multi-agent pattern: orchestrator -> Send fan-out -> synthesizer.
# This is the Week 4 notebook's architecture, and AxiomCart's.
#
#   - The orchestrator decides which agents to run. Simple rules stand in for the LLM here.
#     (With a real LLM you would use llm.with_structured_output(SomePydanticModel) to get
#     a validated answer; that is covered when we switch to a real model.)
#   - Send(node, payload) starts one node run per task. The payload is that run's
#     input only; what the node RETURNS is merged into the main state via reducers.
#   - The synthesizer merges agent_results into one answer.
#
# WHY Send? The orchestrator hands out one job per task, with the task attached:
#
#   Customer asks                          Jobs handed out
#   "Show me headphones"                   Send("search_agent", {"query": "headphones"})
#   "Plan Paris and find hotels"           Send("search_agent", {"query": "hotels"})
#                                          Send("planner_agent", {"query": "itinerary"})
#   "Find hotels AND flights"              Send("search_agent", {"query": "hotels"})
#                                          Send("search_agent", {"query": "flights"})
#
#   - The number of jobs depends on the question, not on the graph.
#   - Each agent gets only its own task (the payload), so it knows what to do.
#   - Last row: the SAME agent gets two jobs, and both run at the same time.
#     Returning plain node names can't do this: ["search_agent", "search_agent"]
#     runs search_agent only once, and that run sees every task in the state.

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


class State(TypedDict):
    user_query: str
    tasks: list[dict]
    agent_results: Annotated[list[str], operator.add]
    final_answer: str


def orchestrator(state: State) -> dict:
    q = state["user_query"].lower()
    tasks = []
    if "hotel" in q or "flight" in q:
        tasks.append({"agent": "search_agent", "query": "find hotels/flights"})
    if "plan" in q or not tasks:
        tasks.append({"agent": "planner_agent", "query": "build itinerary"})
    # ex: tasks = [{"agent": "search_agent", "query": "find hotels/flights"}]
    return {"tasks": tasks}  # stored in state["tasks"]


def dispatch(state: State) -> list[Send]:
    # ex: state["tasks"] = [{"agent": "search_agent", "query": "find hotels/flights"},
    #                       {"agent": "planner_agent", "query": "build itinerary"}]
    sends = []
    for task in state["tasks"]:
        node_name = task["agent"]  # which node to run, e.g. "search_agent"
        payload = {"query": task["query"]}  # that run's input, e.g. {"query": "find hotels/flights"}
        sends.append(Send(node_name, payload))
    # ex: sends = [Send("search_agent", {"query": "find hotels/flights"}),
    #              Send("planner_agent", {"query": "build itinerary"})]
    return sends  # LangGraph starts one run per Send, all in the same step


def search_agent(payload: dict) -> dict:
    return {"agent_results": [f"search: results for '{payload['query']}'"]}


def planner_agent(payload: dict) -> dict:
    return {"agent_results": [f"planner: 3-day plan for '{payload['query']}'"]}


def synthesizer(state: State) -> dict:
    # Real version: if more than one result, one more LLM call merges them.
    return {"final_answer": " | ".join(state["agent_results"])}


builder = StateGraph(State)
for name, fn in [("orchestrator", orchestrator), ("search_agent", search_agent),
                 ("planner_agent", planner_agent), ("synthesizer", synthesizer)]:
    builder.add_node(name, fn)
builder.add_edge(START, "orchestrator")
builder.add_conditional_edges("orchestrator", dispatch, ["search_agent", "planner_agent"])
builder.add_edge("search_agent", "synthesizer")
builder.add_edge("planner_agent", "synthesizer")
builder.add_edge("synthesizer", END)
graph = builder.compile()


if __name__ == "__main__":
    for q in ["Find hotels in Paris", "Plan Paris and find hotels"]:
        print(f"{q!r:30} -> {graph.invoke({'user_query': q, 'agent_results': []})['final_answer']}")
