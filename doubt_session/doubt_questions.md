# Doubt session: questions and answers

## Q1. A user asks a question and we start 6 agents to answer it. While they are working, the user types more. How does LangGraph handle that?

**A.** The LangGraph library does **not** merge the new message into the run that is already going.
You decide what happens, and there are 4 choices:

1. **Reject**: "please wait", and ignore the new message until the answer is ready.
2. **Enqueue**: finish answer 1, then answer the new message as the next turn.
3. **Cancel and restart**: stop the run, start again with both messages.
4. **Do nothing** (the trap): both runs go ahead and the user gets 2 answers.

LangGraph's paid **Agent Server** calls this **"double texting"** and builds the 4 choices in
(`multitask_strategy`). With the plain library you build them yourself.

In AxiomCart this cannot happen: `main.py` waits for the answer before the user can type again
(choice 1).

Examples of all 4 server strategies (one notebook each):
[github.com/jameskanyiri/double_texting](https://github.com/jameskanyiri/double_texting)

---

## Q2. How does LangGraph remember facts about a user across different conversations?

**A.** LangGraph has two kinds of memory:

| | Checkpointer | Store |
|---|---|---|
| Think of it as | the **chat history** of one conversation | a **notebook about the user** |
| Lasts for | one `thread_id` | every conversation of that user |
| Saved | automatically | only when your code saves a fact |

A new conversation means a new `thread_id`, so the chat history starts empty. The Store is still
there, so the agent can still look up what it saved about the user.

**Example**

- Monday, conversation 1: "Remember, I live in Pune." The agent saves `address = Pune` in the
  user's notebook.
- Tuesday, conversation 2 (new thread): "Where is my order going?" The chat history is empty, but the
  agent reads the notebook and knows the address is Pune.
- Another user asks the same thing: their notebook is empty, so the agent does not know.

**In pseudo code**

```
graph = compile(checkpointer = chat history, store = user notebook)   # both saved in a database

# Monday, thread "mon", user u42:   "I live in Pune"
notebook[u42].save("address", "Pune")

# Tuesday, thread "tue", user u42:  "Where is my order going?"
chat history  -> empty (new thread)
notebook[u42].read("address")   -> "Pune"

# Any day, user u99:  "Where is my order going?"
notebook[u99].read("address")   -> nothing
```

**Things to remember**

- The Store does not decide what is worth saving. Your code (usually an LLM call) does.
- Put the `user_id` in the notebook name, or one user can read another user's facts.
- Use a store backed by a database (SQLite, Postgres) so the notebook survives a restart. The
  in-memory one used in the lessons is lost when the program stops.

AxiomCart does not use a Store yet. It would hold customer facts such as their address or
favourite brand.
