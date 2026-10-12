# What Is an Agent?

A clinic's $1,200 MRI claim was denied with code **CO-197**. We asked ChatGPT six questions.

## The six questions

**Q1**
```
A medical claim was denied with code CO-197. In 3 short bullets: what does it mean, and what should the billing team do next?
```

**Q2**
```
What is the status of claim A1029 right now?
```

**Q3** (with the Northstar policy attached)
```
Using only the attached policy: does an outpatient MRI need prior authorization, and how long do we have to appeal a CO-197 denial?
```

**Q4**
```
Are there any recent federal rule changes on prior authorization that could affect how fast insurers must answer requests?
```

**Q5** (with the Northstar policy attached)
```
Claim A1029: outpatient MRI on Sept 15, 2026, billed $1,200, denied CO-197 on Sept 30. Our notes show prior auth was given by phone on Sept 10, reference PA-55821. Using the attached policy, decide what we should do and prepare it. Show your plan first, then do each step.
```

**Q6**
```
Great. Now submit this on the Northstar provider portal.
```

## What each question showed

| # | What happened | Agent part |
| --- | --- | --- |
| Q1 | Answered from what it learned in training | **Brain (LLM)** |
| Q2 | Couldn't answer: no access to our systems | **Brain's limit** |
| Q3 | Answered from the document we gave it | **Knowledge (RAG)** |
| Q4 | Decided on its own to search the web | **Tools + decision** |
| Q5 | Planned, checked the policy, chose a corrected claim, prepared it | **The loop** |
| Q6 | Couldn't submit without access and approval, but knew what "this" meant | **Permissions + Memory** |

## Definition

> **An agent is an LLM that uses knowledge and tools in a loop, remembers what it has done, and works toward a goal within the permissions you give it.**

**Agent = Brain + Knowledge + Tools + Loop + Memory, within guardrails**

---

*Northstar Health Plan is fictional and was created for this demo. CO-197 is a real standard denial code: prior authorization absent.*



Q:
You are a billing agent with 4 tools: lookup_claim(id), read_policy(topic), draft_corrected_claim(details), submit_to_portal(claim).


Work claim A1029: outpatient MRI on Sept 15, 2026, billed $1,200, denied CO-197 on Sept 30. Prior auth was given by phone on Sept 10, reference PA-55821. Use the Northstar policy from earlier.

For each step show: Thought → Tool call → Result (invent realistic results). Show every tool call, even if you already know the answer. Stop before submit_to_portal.


Keypoint =>  agent loop step by step

Q:
Now imagine you also handle eligibility, coding, appeals, patient phone calls and payments for 5 insurers, about 40 tools in total. What would go wrong?

Keypoint => The point is that the answer is not "add more tools". 

Q:
Work claim A1029 again as a team. Each agent speaks only in its own section:
- Supervisor: decides which specialists are needed and in what order
- Eligibility Agent: checks the patient's coverage
- Coding Agent: checks the CPT code and whether prior auth was required
- Appeals Agent: decides the fix and drafts it

Eligibility and Coding don't depend on each other, so run them side by side, then hand both results to Appeals. The Supervisor writes the final answer.

Keypoint => multi-agent pattern