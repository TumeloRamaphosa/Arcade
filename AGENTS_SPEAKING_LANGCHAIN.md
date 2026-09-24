# Agents Speaking to Each Other (LangChain)
## Naledi ↔ Kev ↔ EDDIE ↔ Charlie (Autonomous Dialogue)

```python
from langchain.agents import AgentExecutor, Tool, initialize_agent
from langchain.llms import Ollama

# Agents register themselves
agents = {
    "naledi": AgentExecutor.from_agent_and_tools(...),
    "kev": AgentExecutor.from_agent_and_tools(...),
    "eddie": AgentExecutor.from_agent_and_tools(...),
    "charlie": AgentExecutor.from_agent_and_tools(...)
}

# Agent communication
naledi_asks_kev = """
Naledi to Kev: "Should I publish this 500-word founder insight?"
Kev responds: "Yes (92% confidence). Blog + social platforms."
"""

# LangChain Memory (shared)
shared_memory = ConversationBufferMemory(k=10)

# Continuous dialogue
while True:
    # Each agent speaks
    naledi_output = agents["naledi"].run("Write content")
    kev_decision = agents["kev"].run(f"Gate: {naledi_output}")
    eddie_analysis = agents["eddie"].run(f"Optimize spend based on: {kev_decision}")
    
    # Log to shared memory
    shared_memory.save_context(
        {"input": "naledi wrote"},
        {"output": naledi_output}
    )
    
    sleep(1800)  # Every 30 min
```

**Result:** Agents collaborate autonomously. No human in loop.

---
