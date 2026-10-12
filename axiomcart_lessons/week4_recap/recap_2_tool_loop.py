# Recap 2: how an LLM uses tools. Every agent in Week 4 and Week 5 is this loop.
#
#   1. bind_tools(tools) sends each tool's name/docstring/arg schema to the model.
#   2. The model replies with AIMessage(content="", tool_calls=[{name, args, id}]).
#   3. YOUR code runs the tool and appends ToolMessage(content, tool_call_id=id).
#   4. Call the model again. No tool_calls in the reply = final answer, stop.
# A scripted model stands in for the LLM so this runs offline.
#
# How messages grow: a node never edits the list. It returns {"messages": [one_new_message]}
# and the operator.add reducer appends it:  old_list + [one_new_message].

import operator
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph


@tool
def get_order_status(order_id: str) -> str:
    """Look up an order's delivery status by ID, e.g. ORD102."""
    return f"{order_id}: delayed by weather, new ETA Feb 15"


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]  # returned lists are APPENDED


def model(state: AgentState) -> dict:
    # Real code: reply = llm.bind_tools([get_order_status]).invoke(state["messages"])
    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):
        # 2nd visit: the tool result is in, so write the final answer.
        reply = AIMessage(content="Sorry for the wait. " + last_message.content + ".")
    else:
        # 1st visit: only the user's question so far, so ask for a tool.
        tool_call = {"name": "get_order_status", "args": {"order_id": "ORD102"}, "id": "call-1"}
        reply = AIMessage(content="", tool_calls=[tool_call])

    return {"messages": [reply]}  # appended to the end of state["messages"]


def tools(state: AgentState) -> dict:
    last_message = state["messages"][-1]  # the AIMessage that asked for a tool
    tool_call = last_message.tool_calls[0]  # this example only ever asks for one

    result = get_order_status.invoke(tool_call["args"])  # "ORD102: delayed by weather, ..."
    tool_message = ToolMessage(content=result, tool_call_id=tool_call["id"])

    return {"messages": [tool_message]}  # appended to the end of state["messages"]


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]  # the reply model() just added
    if last_message.tool_calls:  # non-empty list = the model wants a tool
        return "tools"
    return END


builder = StateGraph(AgentState)
builder.add_node("model", model)
builder.add_node("tools", tools)
builder.add_edge(START, "model")
builder.add_conditional_edges("model", should_continue, ["tools", END])
builder.add_edge("tools", "model")
agent = builder.compile()
# Shortcuts that build this same loop for you: langgraph.prebuilt.ToolNode +
# tools_condition, or langchain.agents.create_agent(model, tools, system_prompt=...).


if __name__ == "__main__":
    question = HumanMessage(content="Where is order ORD102?")
    final_state = agent.invoke({"messages": [question]})

    for i, message in enumerate(final_state["messages"]):
        print(f"[{i}] {message.type:5} | {message.content or message.tool_calls}")



  
