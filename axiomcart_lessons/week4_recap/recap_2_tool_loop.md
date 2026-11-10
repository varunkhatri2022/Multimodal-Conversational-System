# Recap 2: tool loop, visualized

[recap_2_tool_loop.py](recap_2_tool_loop.py) for the input `"Where is order ORD102?"`.

## The loop

```
   START ──► model ──should_continue──► END        (no tool_calls)
               ▲            │
               │            ▼                      (has tool_calls)
               └─────────  tools
                  fixed edge: tools → model  (this is the LOOP)
```
