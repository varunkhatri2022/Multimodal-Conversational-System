# Lessons 20 & 21: tool loop inside a `Send` fan-out, the problem and the fix

Same scenario in both files: `hotel_agent` answers right away, `trip_agent` needs a tool first.
The only difference is **where `trip_agent`'s loop lives**. Each `STATE` box is the shared state
after that step.

## Lesson 20: loop in the MAIN graph ([axiomcart_20.py](axiomcart_20.py))

```
                                         START
                                           │ dispatch → 2 Sends
                   ┌───────────────────────┴───────────────────────┐
                   │ Send {"task": "hotels in Jaipur"}             │ Send {"task": "3-day Jaipur plan"}
                   ▼                                               ▼
            ┌─────────────┐                                 ┌─────────────┐
  STEP 1    │ hotel_agent │                                 │ trip_agent  │  sees task = "3-day Jaipur plan" ✓
            └──────┬──────┘                                 └──────┬──────┘
                   │                                               │
┌──────────────────┴───────────────────────────────────────────────┴──────────────────┐
│ STATE after step 1                                                                  │
│   results       = ["hotel_agent: hotels in Jaipur"]                                 │
│   trip_messages = ["need tool"]                                                     │
│   (no "task" key: the task was only in trip_agent's Send payload)                   │
└──────────────────┬───────────────────────────────────────────────┬──────────────────┘
                   │                                               │ route_trip → "tool"
                   ▼                                               ▼
            ┌─────────────┐                                 ┌─────────────┐
  STEP 2    │ synthesizer │                                 │    tool     │
            └──────┬──────┘                                 └──────┬──────┘
                   │  ✗ PROBLEM 1: runs EARLY,                     │
                   │     sees only the hotel result                │
                   ▼                                               │
                  END  (hotel branch done)                         │
┌──────────────────────────────────────────────────────────────────┴──────────────────┐
│ STATE after step 2                                                                  │
│   results       = ["hotel_agent: hotels in Jaipur"]                                 │
│   trip_messages = ["need tool", "tool result"]                                      │
└──────────────────────────────────────────────────────────────────┬──────────────────┘
                                                                   │ normal edge tool → trip_agent
                                                                   │ (NO payload: gets the main state)
                                                                   ▼
                                                            ┌─────────────┐
  STEP 3                                                    │ trip_agent  │
                                                            └──────┬──────┘
                                                                   │  ✗ PROBLEM 2: sees task = None
                                                                   │    (main state has no "task")
┌──────────────────────────────────────────────────────────────────┴──────────────────┐
│ STATE after step 3                                                                  │
│   results       = ["hotel_agent: hotels in Jaipur", "trip_agent: None"]             │
│   trip_messages = ["need tool", "tool result", "done"]                              │
│   ✗ PROBLEM 3: the loop's working messages sit in the main state                    │
└──────────────────────────────────────────────────────────────────┬──────────────────┘
                                                                   │ route_trip → "synthesizer"
                                                                   ▼
                                                            ┌─────────────┐
  STEP 4                                                    │ synthesizer │
                                                            └──────┬──────┘
                                                                   │  ✗ runs AGAIN, sees "trip_agent: None"
                                                                   ▼
                                                                  END
```

## Lesson 21: loop in a SUBGRAPH ([axiomcart_21.py](axiomcart_21.py))

```
                                         START
                                           │ dispatch → 2 Sends
                   ┌───────────────────────┴───────────────────────┐
                   │ Send {"task": "hotels in Jaipur"}             │ Send {"task": "3-day Jaipur plan"}
                   ▼                                               ▼
            ┌─────────────┐            ┌───────────────────────────────────────────────────────┐
  STEP 1    │ hotel_agent │            │ trip_agent                                            │
            └──────┬──────┘            │   trip_subgraph.invoke(...)   ← whole loop runs HERE  │
                   │                   │  ┌────────────────────────────────────────────────┐   │
                   │                   │  │ PRIVATE state (never in the main state)        │   │
                   │                   │  │ start  task="3-day Jaipur plan" messages=[]    │   │
                   │                   │  │ think  ✓ sees task → ["need tool"]             │   │
                   │                   │  │ tool   → ["need tool", "tool result"]          │   │
                   │                   │  │ think  ✓ sees task → [..., "done"]             │   │
                   │                   │  └────────────────────────────────────────────────┘   │
                   │                   └───────────────────────────┬───────────────────────────┘
                   │                                               │
┌──────────────────┴───────────────────────────────────────────────┴──────────────────┐
│ STATE after step 1                                                                  │
│   results = ["hotel_agent: hotels in Jaipur", "trip_agent: 3-day Jaipur plan"]      │
│   ✓ both agents finished in ONE step   ✓ no trip_messages in the main state         │
└──────────────────────────────────────────┬──────────────────────────────────────────┘
                                           ▼
                                    ┌─────────────┐
  STEP 2                            │ synthesizer │
                                    └──────┬──────┘
                                           │  ✓ runs ONCE, sees both results
                                           ▼
                                         END
```
