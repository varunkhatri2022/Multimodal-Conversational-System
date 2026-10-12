# From One Agent to a Team of Agents

Same story: claim **A1029**, a $1,200 outpatient MRI denied with code **CO-197**. Prior auth was given by phone on Sept 10, reference **PA-55821**. We asked ChatGPT to work it in different ways.

## Part 1 — Single agent

**P1**
```
You are a billing agent with 4 tools: lookup_claim(id), read_policy(topic), draft_corrected_claim(details), submit_to_portal(claim).

Work claim A1029: outpatient MRI on Sept 15, 2026, billed $1,200, denied CO-197 on Sept 30. Prior auth was given by phone on Sept 10, reference PA-55821. Use the Northstar policy from earlier.

For each step show: Thought → Tool call → Result (invent realistic results). Show every tool call, even if you already know the answer. Stop before submit_to_portal.
```

**P2**
```
Now imagine you also handle eligibility, coding, appeals, patient phone calls and payments for 5 insurers, about 40 tools in total. What would go wrong?
```

## Part 2 — Multi-agent

**P3**
```
Work claim A1029 again as a team. Each agent speaks only in its own section:
- Supervisor: decides which specialists are needed and in what order
- Eligibility Agent: checks the patient's coverage
- Coding Agent: checks the CPT code and whether prior auth was required
- Appeals Agent: decides the fix and drafts it

Eligibility and Coding don't depend on each other, so run them side by side, then hand both results to Appeals. The Supervisor writes the final answer.
```

## Part 3 — Sub-agent

**P4**
```
The Appeals Agent's job is big. Turn it into its own mini-team: Records Gatherer → Letter Writer → Compliance Checker.

First show what the Supervisor sees: one request to "Appeals" and one result back.
Then open the box and show the three steps inside.
```

## Part 4 — More agent patterns

**P5 — Router**
```
You are the front desk of a billing office. Send each message to one agent (Eligibility, Coding, Appeals or Patient Support) with a one-line reason:
1. "Is Maria's insurance active for next week?"
2. "Claim A2201 was denied CO-197, but we did get auth."
3. "Which CPT code is an MRI of the knee without contrast?"
4. "I got a bill I don't understand."
```

**P6 — Reflection**
```
Act as a Reviewer. Check the corrected claim for A1029 against the Northstar policy's "required in every appeal" list. List anything missing, then produce a fixed version.
```

**P7 — Human in the loop**
```
Run claim A1029 one more time. At any step that sends something outside the clinic, stop and ask me "APPROVE or EDIT?" and wait for my answer.
```

**P8** (reply to its question)
```
EDIT: patient name is Jane Doe.
```

**P9**
```
APPROVE
```

## What each prompt showed

| # | What happened | Concept | In LangGraph |
| --- | --- | --- | --- |
| P1 | One agent picked tools step by step: think, act, observe | **Single agent** (ReAct pattern) | `create_react_agent` with tools |
| P2 | Too many tools: wrong picks, huge prompt, hard to test | **Single agent's limit** | — |
| P3 | A supervisor split the work across specialists; two ran at once | **Multi-agent** (Supervisor + Parallel) | Supervisor node + `Send()` |
| P4 | Appeals became a team inside a box; the supervisor saw only input and output | **Sub-agent** (Hierarchical) | Subgraph |
| P5 | Each message went to the right specialist | **Router** | Conditional edge |
| P6 | A reviewer caught a missing field and fixed it | **Reflection** | Generate → review loop |
| P7–P9 | It paused, took our edit, then continued after approval | **Human in the loop** | `interrupt()` + `Command(resume=...)` |

## Definitions

| Term | One line |
| --- | --- |
| **Single agent** | One LLM with tools, working in a loop toward a goal |
| **Multi-agent** | Several specialist agents, each with its own instructions and tools, coordinated by a supervisor or a router |
| **Sub-agent** | A team of agents packaged as one unit; the caller sees only input and output |

## Patterns at a glance

| Pattern | Use it when | In tonight's lab |
| --- | --- | --- |
| ReAct | One agent, a handful of tools | Each specialist agent |
| Router | Requests come in different types | Orchestrator classifies the query |
| Supervisor | A task needs several specialists | Orchestrator |
| Parallel | Steps don't depend on each other | `Send()` to both agents |
| Hierarchical | One specialist's job is a whole workflow | Sales Support and Product Discovery subgraphs |
| Reflection | Quality matters more than speed | — |
| Human in the loop | An action is risky or information is missing | Asks for a missing order ID |

---

*In this demo ChatGPT is one model playing every role. In a real system each agent is a separate LLM call with its own instructions and tools. Northstar Health Plan is fictional.*
