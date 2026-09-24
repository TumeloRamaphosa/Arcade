# OpenInterpreter + Team Mode (VS Code)
## Agents Collaborate. Auto-commit Every 30min.

```yaml
Setup:
  - OpenInterpreter (local code execution)
  - Herdr agents (team orchestration)
  - Git auto-commit (every 30 min)
  - VS Code (IDE + debugging)

Result:
  - Agents write code
  - Code auto-commits
  - Teams collaborate
  - Zero internet
```

## Quick Start

```bash
# 1. Install OpenInterpreter
pip install open-interpreter

# 2. Configure for local execution
echo 'interpreter.offline = True' >> ~/.open_interpreter_config

# 3. Start team mode
interpreter --team-mode --agents 5 --port 3001

# 4. Auto-commit hook
git config --global core.hooksPath .githooks
mkdir -p .githooks
chmod +x .githooks/post-commit

# 5. Every 30min:
# Agents work → auto-commit → push
```

**That's it. Agents code autonomously.**

---

