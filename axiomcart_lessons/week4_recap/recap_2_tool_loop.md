# Recap 2: tool loop, visualized

[recap_2_tool_loop.py](recap_2_tool_loop.py), unrolled for the input `"Where is order ORD102?"`.
Each node box (`╔═╗`) shows the code it runs, using the same variable names as the `.py` file.
Each state box (`┌─┐`) shows the full `state["messages"]` after that node.

A node never edits the list. It returns `{"messages": [one_new_message]}` and the
`operator.add` reducer appends it (`old_list + [one_new_message]`), marked `+ NEW` below.

```
                                  START
                                    │
                                    │  agent.invoke({"messages": [HumanMessage(...)]})
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ STATE (input)                                                                            │
│  [0] HumanMessage  content="Where is order ORD102?"                         + NEW (input) │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ╔═══════════════════════════════════════════════════════════╗
                    ║  model(state)   — 1st visit                               ║
                    ║  last_message = [0] HumanMessage  (not a ToolMessage)     ║
                    ║  → else branch:                                           ║
                    ║    tool_call = {name, args: {order_id: "ORD102"}, id}     ║
                    ║    reply = AIMessage(content="", tool_calls=[tool_call])  ║
                    ║  return {"messages": [reply]}                             ║
                    ╚═══════════════════════════════════════════════════════════╝
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ STATE after model                                                                        │
│  [0] HumanMessage  content="Where is order ORD102?"                                      │
│  [1] AIMessage     content=""                                                    + NEW   │
│                    tool_calls=[{name: "get_order_status",                                │
│                                 args: {order_id: "ORD102"}, id: "call-1"}]               │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                    should_continue: last_message = [1] AIMessage
                                     last_message.tool_calls is non-empty
                                    │  → return "tools"
                                    ▼
                    ╔═══════════════════════════════════════════════════════════╗
                    ║  tools(state)                                             ║
                    ║  last_message = [1] AIMessage                             ║
                    ║  tool_call    = last_message.tool_calls[0]                ║
                    ║  result       = get_order_status.invoke({order_id:ORD102})║
                    ║  tool_message = ToolMessage(content=result,               ║
                    ║                             tool_call_id="call-1")        ║
                    ║  return {"messages": [tool_message]}                      ║
                    ╚═══════════════════════════════════════════════════════════╝
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ STATE after tools                                                                        │
│  [0] HumanMessage  content="Where is order ORD102?"                                      │
│  [1] AIMessage     content=""  tool_calls=[get_order_status(order_id="ORD102"), call-1]  │
│  [2] ToolMessage   content="ORD102: delayed by weather, new ETA Feb 15"          + NEW   │
│                    tool_call_id="call-1"                                                 │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │  fixed edge: tools → model   (this is the LOOP)
                                    ▼
                    ╔═══════════════════════════════════════════════════════════╗
                    ║  model(state)   — 2nd visit                               ║
                    ║  last_message = [2] ToolMessage                           ║
                    ║  → if branch:                                             ║
                    ║    reply = AIMessage(content="Sorry for the wait. "       ║
                    ║                      + last_message.content + ".")        ║
                    ║  return {"messages": [reply]}                             ║
                    ╚═══════════════════════════════════════════════════════════╝
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ STATE after model (final)                                                                │
│  [0] HumanMessage  content="Where is order ORD102?"                                      │
│  [1] AIMessage     content=""  tool_calls=[get_order_status(order_id="ORD102"), call-1]  │
│  [2] ToolMessage   content="ORD102: delayed by weather, new ETA Feb 15"                  │
│                    tool_call_id="call-1"                                                 │
│  [3] AIMessage     content="Sorry for the wait. ORD102: delayed by weather,      + NEW   │
│                             new ETA Feb 15."                                             │
│                    tool_calls=[]                                                         │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                    should_continue: last_message = [3] AIMessage
                                     last_message.tool_calls is empty []
                                    │  → return END
                                    ▼
                                   END
```

## The graph itself (before unrolling)

```
   START ──► model ──should_continue──► END        (no tool_calls)
               ▲            │
               │            ▼                      (has tool_calls)
               └─────────  tools
```
