# Lesson summary: pause a graph with interrupt() and continue it with Command(resume=...).
# AxiomCart connection: support_model() calls interrupt(question); main.py sees
# result["__interrupt__"], asks the customer, then calls invoke(Command(resume=answer)).
#
# Rules to remember:
#   1. Resuming needs a checkpointer. The paused state is saved under the thread_id.
#   2. invoke() does not raise. It returns early, with an "__interrupt__" key.
#   3. On resume the interrupted node runs again FROM ITS FIRST LINE. Code before
#      interrupt() executes twice; this time interrupt() returns the resume value.
#
# What happens:
#   interrupt(question)    Saves the graph's state under the thread_id (that's why it
#                          needs a checkpointer), stops the run, and returns the question
#                          to your app in result["__interrupt__"].
#   (meanwhile)            Nothing runs. The app shows the question and waits for the
#                          user's reply, however long it takes.
#   invoke(Command(resume="ORD102"), config)
#                          Loads the saved state and reruns the paused node from its
#                          first line. This time interrupt() returns "ORD102".
#
# In one line: interrupt is "save and stop until the human replies"; resume is "load,
# rerun the paused node from its start, and interrupt() returns the human's answer".
# It's needed because the human's reply arrives later, as a separate request, not
# while the code is running.

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

calls_to_expensive_step = 0


class SupportState(TypedDict):
    question: str
    order_id: str
    answer: str


def support_node(state: SupportState) -> dict:
    print("support_node called")
    global calls_to_expensive_step
    # Stands in for sales_llm.invoke(...) in support_model(): it runs before the
    # interrupt, so it runs again on resume. A real LLM may word it differently.
    calls_to_expensive_step += 1
    question = f"Could you share your order ID? (generated on call #{calls_to_expensive_step})"

    order_id = interrupt(question)  # pause here on the first run; returns the answer on resume
    return {"order_id": order_id, "answer": f"Looking up {order_id}..."}


builder = StateGraph(SupportState)
builder.add_node("support", support_node)
builder.add_edge(START, "support")
builder.add_edge("support", END)


if __name__ == "__main__":
    graph = builder.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "customer-1"}}

    first = graph.invoke({"question": "Where is my order?", "order_id": "", "answer": ""}, config)
    pending = first["__interrupt__"][0]
    print("Paused. Question shown to customer:", pending.value)
    print("Graph's next node:", graph.get_state(config).next)

    resumed = graph.invoke(Command(resume="ORD102"), config)
    print("Resumed. Answer:", resumed["answer"])
    print("Expensive step ran", calls_to_expensive_step, "times")

    # Without a checkpointer the pause is reported, but nothing is saved, so it
    # cannot be resumed. (Behavior checked on langgraph 1.2.)
    no_memory = builder.compile()
    print("\nWithout checkpointer, keys returned:", list(no_memory.invoke({"question": "x", "order_id": "", "answer": ""})))
    try:
        no_memory.invoke(Command(resume="ORD102"))
    except RuntimeError as error:
        print("Resume fails:", error)

    # Design rule: keep work before interrupt() cheap and repeatable, or move it
    # into its own node so the checkpoint saves its result.
