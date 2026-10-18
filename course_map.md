# Course Map

## Where we are going: AxiomCart

Every part of this picture is built in one of the lessons. **R** = Week 4 recap file, **L** = AxiomCart lesson.

```text
  voice in ──► main.py ───────────────────────────────────────────────► voice out     [L29]
               │  ▲
               │  └── pauses to ask the customer, then resumes                        [L26, L27]
               ▼
  START ──► orchestrator ── Command + Send ───────┬──► product_agent ┐                [R3, L22]
            resets results every turn             │    model ⇄ tools │                [R4, L23]
                                                  └──► support_agent ┤                [R2, L20, L21]
                                                       model ⇄ tools │
                                                       + interrupt() ▼
  state + memory (checkpointer, thread_id)                     synthesizer ──► END    [R1, R4]
```

## How we get there

```text
WEEK 4 RECAP: the building blocks
  R1   state, nodes, edges, reducers
  R2   the tool loop: model <-> tools
  R3   orchestrator -> Send -> synthesizer
  R4   memory with a checkpointer (4a problem -> 4b fix)

AXIOMCART PATTERNS: how the real app uses them
  L20 -> L21   tool loops in a fan-out break  ->  fix: subgraphs
  L22 -> L23   Command routing  ->  reset results every turn
  L26 -> L27   interrupt / resume  ->  inside a subgraph, in parallel
  L29          voice: speech-to-text -> graph -> text-to-speech

AXIOMCART: everything together
  greeting -> product -> product + support with interrupt -> voice
```

## Files

| Step | Files |
| --- | --- |
| Week 4 recap | [R1](axiomcart_lessons/week4_recap/recap_1_graph_basics.py) · [R2](axiomcart_lessons/week4_recap/recap_2_tool_loop.py) · [R3](axiomcart_lessons/week4_recap/recap_3_orchestrator_send.py) · [R4a](axiomcart_lessons/week4_recap/recap_4a_checkpointer_problem.py) · [R4b](axiomcart_lessons/week4_recap/recap_4b_checkpointer_fix.py) |
| AxiomCart patterns | [L20](axiomcart_lessons/axiomcart_20.py) · [L21](axiomcart_lessons/axiomcart_21.py) · [L22](axiomcart_lessons/axiomcart_22.py) · [L23](axiomcart_lessons/axiomcart_23.py) · [L26](axiomcart_lessons/axiomcart_26.py) · [L27](axiomcart_lessons/axiomcart_27.py) · [L29](axiomcart_lessons/axiomcart_29.py) |
| AxiomCart | [axiomcart-ai-assistant/](axiomcart-ai-assistant/) with the [sample questions](axiomcart_lessons/axiomcart_sample_questions.md) |
