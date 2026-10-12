# Recap 3: orchestrator → Send fan-out → synthesizer, graph path

[recap_3_orchestrator_send.py](recap_3_orchestrator_send.py)

## The graph

```
                              START
                                │
                                ▼
                    ┌───────────────────────┐
                    │     orchestrator      │   decides the tasks
                    │  → {tasks: [...]}     │
                    └───────────┬───────────┘
                                │
                        dispatch(state)          conditional edge: one Send per task
                                │
              ┌─────────────────┴──────────────────┐
              │ Send("search_agent", {query})      │ Send("planner_agent", {query})
              ▼                                    ▼
   ┌───────────────────────┐            ┌───────────────────────┐
   │     search_agent      │            │     planner_agent     │
   │  (payload)            │            │  (payload)            │
   │  → agent_results +=   │            │  → agent_results +=   │
   └───────────┬───────────┘            └───────────┬───────────┘
               │      same step, run in parallel     │
               └──────────────────┬──────────────────┘
                                  ▼
                    ┌───────────────────────┐
                    │      synthesizer      │   joins agent_results with " | "
                    │  → {final_answer}     │
                    └───────────┬───────────┘
                                ▼
                               END
```

## Which path each input takes

```
"Find hotels in Paris"          ("hotel" only)

  START → orchestrator ──Send──► search_agent ──► synthesizer → END

  final_answer: search: results for 'find hotels/flights'
```

```
"Plan Paris and find hotels"    ("hotel" and "plan")

                       ┌─Send──► search_agent ──┐
  START → orchestrator ┤                        ├──► synthesizer → END
                       └─Send──► planner_agent ─┘

  final_answer: search: results for 'find hotels/flights' | planner: 3-day plan for 'build itinerary'
```

```
"Hi there"                      (no "hotel"/"flight"/"plan" → planner by default)

  START → orchestrator ──Send──► planner_agent ──► synthesizer → END

  final_answer: planner: 3-day plan for 'build itinerary'
```
