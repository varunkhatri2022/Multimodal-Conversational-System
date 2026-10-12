# Lesson 28: saved conversation is useful only when nodes read it.
#
# THE PROBLEM:
#   Turn 1: "Show me noise-cancelling headphones"
#   Turn 2: "Is the second one in stock?"
#   On turn 2, the latest message alone does not say what "the second one" means.
#   A router that checks only that message cannot know this is a product question;
#   in this example it would route to "unclear".
#
# A checkpointer can restore earlier state for the same thread_id, but it does not
# automatically make every node use that history. The app must save useful turns
# AND pass/read them where needed. Below, the customer turns and assistant replies
# are added to messages, and the orchestrator checks the full history. It therefore
# finds "headphones" from turn 1 and routes the follow-up to product_agent.
# (Plain strings keep this lesson short; real apps commonly store message objects.)
# Earlier lessons explain that a checkpointer saves state; lesson 28 teaches the missing piece: saving conversation history doesn’t mean the graph automatically uses it.
# Nodes must read and use that history to understand follow-ups like “Is the second one in stock?”
import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    messages: Annotated[list[str], operator.add]  # the conversation, grows every turn
    route: str
    answer: str


def orchestrator(state: State) -> dict:
    current = state["messages"][-1].lower()  # turn 2 alone: "is the second one in stock?"
    history = " ".join(state["messages"]).lower()  # includes turn 1's "headphones" (the fix)

    if "order" in current:
        route = "support_agent"
    elif "headphones" in history:  # current has no product name; history supplies the context
        route = "product_agent"
    else:
        route = "unclear"
    return {"route": route}


def agent(state: State) -> dict:
    question = state["messages"][-1].removeprefix("Customer: ")
    return {"answer": f"[{state['route']}] reply to {question!r}"}


def synthesizer(state: State) -> dict:
    return {"messages": ["Assistant: " + state["answer"]]}  # store our reply (fix 1)


builder = StateGraph(State)
builder.add_node("orchestrator", orchestrator)
builder.add_node("agent", agent)
builder.add_node("synthesizer", synthesizer)
builder.add_edge(START, "orchestrator")
builder.add_edge("orchestrator", "agent")
builder.add_edge("agent", "synthesizer")
builder.add_edge("synthesizer", END)
graph = builder.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "shopper-1"}}

    for text in ["Show me noise-cancelling headphones", "Is the second one in stock?"]:
        result = graph.invoke({"messages": ["Customer: " + text]}, config)
        print(f"{text!r:40} -> routed to {result['route']}")
    # Turn 2 -> product_agent because history contains "headphones" from turn 1.
    # If the router checked only the latest message, turn 2 would route to "unclear".

    print("\nStored conversation:")
    for line in graph.get_state(config).values["messages"]:
        print("  " + line)
