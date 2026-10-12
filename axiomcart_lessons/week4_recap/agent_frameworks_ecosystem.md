# The LangChain / LangGraph Ecosystem, and How Other Agent Frameworks Compare

A short map of where the tools we use fit, and what the alternatives look like.

## 1. The LangChain family

| Piece | What it is | Where we used it |
| --- | --- | --- |
| **LangChain** | Building blocks for LLM apps: chat models, messages, prompts, tools (`@tool`), retrievers, structured output. Also a ready-made agent (`create_agent`). | `HumanMessage`, `AIMessage`, `@tool`, `bind_tools`, `with_structured_output` |
| **LangGraph** | Low-level orchestration: your app is a **graph** of nodes over a shared **state**. Adds the things production agents need: checkpoints, memory per `thread_id`, `interrupt()` / resume, parallel branches, streaming. | Every recap file and lessons 20–29 |
| **Integration packages** | One package per provider: `langchain-openai`, `langchain-anthropic`, `langchain-chroma`, ... | `ChatOpenAI`, `OpenAIEmbeddings`, Chroma in AxiomCart |
| **LangSmith** | Tracing, debugging and evaluation: see every LLM call, tool call and node, with inputs, outputs, latency and cost. Also hosts and deploys LangGraph apps. | Not used here, but the first thing to add in a real project |
| **LangGraph Studio** | A visual view of a running graph: watch nodes execute, inspect state, step through interrupts. | |
| **Deep Agents** | A higher-level "agent harness" on top of LangGraph, with planning, sub-agents and a scratch file system built in. | |

**How LangChain and LangGraph relate:** LangChain gives you the *parts* (models, tools, messages). LangGraph decides *how they run*: which step comes next, what is remembered, when to pause. LangChain's `create_agent` is itself built on LangGraph; you write the graph yourself when you need more control, as in AxiomCart.

```
LangChain  (parts: models, tools, messages, retrievers)
    │
LangGraph  (control: state, nodes, edges, checkpoints, interrupts)
    │
LangSmith  (visibility: traces, evaluations, deployment)
```

## 2. Other agent frameworks

### Microsoft Agent Framework (MAF)

Microsoft's current agent framework for **Python and .NET**, created by bringing together **Semantic Kernel** and **AutoGen**. It has two parts: *agents* (an LLM with tools, instructions and memory) and *workflows* (graph-based, typed steps with checkpointing and human-in-the-loop). Strong fit for teams on **Azure** and **Azure AI Foundry**.
**Closest to LangGraph** in idea: workflows are graphs with explicit control.

### Semantic Kernel

Microsoft's earlier SDK (C#, Python, Java) for adding LLMs to existing enterprise apps. Built around **plugins** (functions the model can call) and a central **kernel** that manages models and services. Popular in .NET shops. New projects are pointed toward MAF.

### AutoGen

Microsoft Research's framework where agents solve a task by **talking to each other** (for example, an assistant agent and a code-executor agent in a group chat). Great for research and quick multi-agent experiments, harder to control step by step. Its ideas now live in MAF; **AG2** is a community-maintained continuation of the original AutoGen.

### CrewAI

**Role-based** teams. You describe each agent like a job: *role*, *goal*, *backstory*. You give the crew *tasks* and a *process* (sequential, or hierarchical with a manager agent). Very quick to get a multi-agent demo running. For more control there are **Flows**, which are event-driven and more deterministic.
**Closest to** the "Supervisor + specialists" idea from the ChatGPT demo, written as job descriptions instead of a graph.

### Others worth knowing by name

| Framework | One line |
| --- | --- |
| **OpenAI Agents SDK** | Lightweight: agents, tools, **handoffs** between agents, guardrails, built-in tracing. |
| **Google ADK** (Agent Development Kit) | Google's framework; works best with Gemini and Google Cloud (Vertex AI). |
| **LlamaIndex** | Started as the RAG / data framework; now also has agents and event-driven workflows. |
| **Pydantic AI** | Type-safe agents in plain Python, from the Pydantic team. |
| **Claude Agent SDK** | Anthropic's SDK for building agents on the same harness as their coding agent. |
| **Strands Agents** | AWS's open-source, model-driven agent SDK. |

## 3. Side by side

| | LangGraph | MAF | Semantic Kernel | AutoGen / AG2 | CrewAI |
| --- | --- | --- | --- | --- | --- |
| **Main idea** | Graph of nodes over shared state | Agents + graph-based workflows | Kernel + plugins | Agents in conversation | Crew of role-based agents |
| **Control** | High: you write every step and edge | High (workflows) | Medium | Low: agents decide in chat | Low to medium (crews), higher with Flows |
| **Languages** | Python, JavaScript | Python, .NET | C#, Python, Java | Python (.NET in AutoGen) | Python |
| **Memory / resume** | Checkpointer + `thread_id` | Built into workflows | Through services | Chat history | Built-in memory options |
| **Human in the loop** | `interrupt()` + `Command(resume=...)` | Built into workflows | Through your app code | A "human" agent in the chat | Human input on tasks |
| **Best for** | Production agents needing exact control | Microsoft / Azure stacks | Adding AI to existing enterprise .NET apps | Research, prototypes | Fast multi-agent demos |

## 4. Same ideas, different names

What you learned in LangGraph exists in every serious framework; only the names change.

| LangGraph (what we used) | Same idea elsewhere |
| --- | --- |
| `StateGraph`, nodes, edges | MAF *workflow* with *executors* and *edges*; CrewAI *Flow*; LlamaIndex *Workflow* |
| Orchestrator + `Send` to specialists | CrewAI *hierarchical process* (manager agent); OpenAI SDK *handoffs*; AutoGen *group chat manager* |
| Agent subgraph (model ⇄ tools loop) | An "agent" object in any framework: CrewAI `Agent`, MAF `ChatAgent`, OpenAI SDK `Agent` |
| `@tool` | Semantic Kernel *plugin function*; CrewAI *tool*; OpenAI SDK *function tool* |
| Checkpointer + `thread_id` | MAF workflow checkpoints; *sessions* / *threads* in most SDKs |
| `interrupt()` / resume | MAF *request / response* in workflows; CrewAI human input; AutoGen human proxy agent |

## 5. Two standards that connect them all

- **MCP (Model Context Protocol):** a standard way to plug **tools and data** into an agent. Write a tool server once, and any MCP-aware framework (LangGraph, MAF, OpenAI SDK, ...) can use it.
- **A2A (Agent2Agent protocol):** a standard way for **agents built in different frameworks** to talk to each other.

Together they mean the framework choice matters less over time: tools and agents can be shared across them.

## 6. How to choose (rule of thumb)

- **Need exact control, memory, human approval and production reliability?** → LangGraph (or MAF on Azure).
- **Company runs on .NET / Azure?** → Microsoft Agent Framework.
- **Want a multi-agent demo running today?** → CrewAI.
- **Exploring research ideas where agents debate or collaborate freely?** → AutoGen / AG2.
- **Already deep in one cloud?** → that cloud's SDK (Google ADK, AWS Strands, OpenAI Agents SDK).

The concepts from this course (state, routing, tool loops, parallel agents, memory, human-in-the-loop) transfer to all of them.

> These frameworks change quickly. Check each project's documentation for the current status before choosing one.
