# Project: Persistent Context System

## What we're building
**Personal context ownership layer.**

The core problem: Context is fragmented. You talk to ChatGPT about chores, Claude about groceries, another tool about health - none of them know about each other. Each conversation is an island.

The vision: A user-owned, non-proprietary store where:
- You accumulate context across your life (projects, chores, health, groceries, whatever)
- Any LLM from any tool can access what's relevant
- You control what's shared with what

This is bigger than "LLM memory" - it's about owning your context so it's portable across tools, models, and time.

## What the tool IS and ISN'T

**It's the "file system" for context.**
- Organizes and namespaces context (projects, domains, "main")
- Standardized, portable storage format (user owns data)
- MCP server that exposes it to any model
- Hooks to plug in existing tools (Mem0, LightRAG, etc.) for smart operations

**It's NOT replicating what existing tools do.**
- Not building memory extraction (Mem0 does that)
- Not building knowledge graphs (LightRAG does that)
- Not building context window management (Letta does that)

The tool handles **organization and ownership**. Other tools handle **intelligence**.

Constraint: One person, weekends/weeknights. Must leverage existing solutions heavily.

## Core insight
The goal isn't storing static facts about the user. It's preserving the model's evolved understanding of things - understanding that gets refined through corrections and dialogue.

## Key analogy
We're building a part of a brain (memory/hippocampus) that connects to other parts (LLM as reasoning). The LLM + this system + future parts = the "assistant" that interacts with the user.

## What triggers memory storage? (exploring)
- Explicit instruction ("remember this")
- Corrections (high signal - user fixing model's misconception)
- Emotional/emphasis signals ("I really like this," "this is important")
- Still unclear: who decides what to store - model, tool, or user? Likely a hybrid.

## Important distinction
Two types of knowledge worth persisting:
1. **Domain understanding** - how things work, what a feature does (more durable)
2. **Conversational state** - where we are in thinking, what we've explored/ruled out (about not losing thread)

## Brain analogy - what can we learn?
- Filtering: not everything makes it to long-term memory
- Consolidation: short-term graduates to long-term (or fades)
- Retrieval is associative, not database-like
- Emotional weight affects what sticks
- Emotional significance = mechanism for instinctual/unconscious parts of brain to influence storage decisions
- Association = for better retrieval
- Repetition = prediction method (if it came up before, it'll come up again)

## Sleep / background consolidation (set aside for now)
- Could be a separate tool that uses the MCP server to continuously refine memory
- Not core to the initial project - the storage/retrieval system needs to exist first
- Revisit later as a layer on top

## Constraints identified
- Models using the tool are outside our control (could be bad/old)
- Don't want to require complex behavior from the model
- Don't want high token cost or lots of back-and-forth
- Tool interface limited to what MCP offers

## Open items (to revisit)
- How does filtering actually work? What role does sleep play? Is there a tool equivalent?
- Short-term vs long-term: is context window the short-term, or is there another layer?
- Would vector DB solve associative retrieval? Does it *truly* in this context?
- Where does emotional weight detection happen - in tool or model?
- The three architectures (model decides / tool decides / user decides) - probably a hybrid but need to figure out the mix

## Existing solutions (research conducted)

### Mem0
- "Universal memory layer for AI agents"
- Two-phase pipeline: Extraction (pulls candidate memories from conversation) and Update (compares to existing, handles conflicts)
- Uses hybrid storage: vector DB + key-value + graph DB
- Has conflict detection and resolution (add/merge/invalidate/skip)
- Claims 26% better accuracy than OpenAI memory, 90% token savings
- The tool itself uses an LLM to decide what to extract/store
- Has MCP server available

### Letta (formerly MemGPT)
- OS-inspired architecture: treats context window as RAM, external storage as disk
- Key insight: the LLM itself manages its own memory via tool calls
- Memory hierarchy: core memory (in-context, always visible) vs archival (out-of-context, retrieved on demand)
- Agent autonomously decides what to remember/update using tools like `core_memory_append`, `archival_memory_insert`
- "Heartbeat" mechanism for multi-step reasoning
- Emphasizes self-editing memory - agent actively maintains its state

### OpenMemory
- Local-first, open source
- Treats time as first-class: valid_from/valid_to for facts
- Auto-evolution: new facts automatically close old ones
- Has MCP server built-in

### LightRAG
- Graph-based RAG - builds knowledge graph from documents
- Dual-level retrieval: local (entities) and global (relationships)
- Handles multimodal via RAG-Anything integration
- Focus: document understanding and retrieval, not conversational memory
- More about "what's in the documents" than "what did we discuss"

### RAG-Anything
- Multimodal document processing (images, tables, equations)
- Built on LightRAG
- Specialized processors for different content types
- Focus: making diverse document formats queryable

### Key patterns across solutions
1. **Hybrid storage** - vector for semantic search, structured for facts/relationships
2. **LLM-in-the-loop for extraction** - something intelligent decides what's worth keeping
3. **Conflict/contradiction handling** - what happens when new info conflicts with old
4. **Temporal awareness** - facts change over time, need validity windows
5. **Hierarchy** - in-context (fast, limited) vs out-of-context (unlimited, requires retrieval)

### Open questions from research
- Most solutions focus on personal assistants / chatbots. Does the project-scoped use case differ significantly?
- Letta's approach (model manages its own memory) vs Mem0's approach (separate extraction layer) - which fits better?
- None of these seem to solve the "corrections are high signal" insight we discussed - they're more generic

## Tool positioning (where it sits)

Existing tools mapped:
| Tool | Storage | Adding | Reading | Where it sits |
|------|---------|--------|---------|---------------|
| Mem0 | Internal (vector+KV+graph) or hosted | Extracts from conversations via LLM | Semantic search | Between app and LLM |
| Letta | Internal (SQLite/Postgres) | LLM calls tools to write | LLM calls tools to read | Wraps the LLM entirely |
| LightRAG | Configurable backends | User inserts documents | Query modes | Beside LLM, fed docs |
| OpenMemory | Local files | Via MCP tools | Via MCP tools | Pure storage layer via MCP |

Key distinction:
- Mem0/Letta: opinionated about *what* to store
- LightRAG: opinionated about *how* to organize
- OpenMemory: dumb pipe (store/retrieve on command)

Our tool: TBD - needs to figure out where it sits and what it uses underneath

## Repo/project use case (concrete scenario)

User wants:
- "Local" memory per project that can later sync/merge with "main" memory
- Ability to "erase" all memories of a dropped project
- Manual querying of memories
- Manual appending to memories
- Dropping files (PDFs, etc.) for the model to ingest
- Versioning (unclear how this would work)

Key principle: User owns and controls the data. Granular control over what exists, what's shared, what's deleted.

## Open questions we haven't resolved yet
**The memory/storage layer should be swappable/replaceable.**
- This is a life-long usage tool - can't afford to get locked into tech that becomes outdated
- Memory/RAG is an active area of research - making final architecture decisions based on current solutions is risky
- Existing solutions (Mem0, LightRAG, etc.) might be USED WITHIN the final solution, not replaced by it
- The tool should define interfaces that can be implemented by different backends as technology evolves

## Current thread
Discussed research findings. User emphasized that existing solutions could be components, and that the architecture needs to be future-proof with swappable implementations.