# Local Offline Agent Stack
## Kev + MiniCPM + Hermes — No Internet Required

**Setup:** Fully local, self-contained, runs on your Mac in VS Code

---

## Architecture (Offline)

```
┌─────────────────────────────────────────────────┐
│   Your Mac (M1 Max, 32GB RAM)                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌────────────────────────────────────────┐   │
│  │  Docker Desktop (Local Containers)     │   │
│  ├────────────────────────────────────────┤   │
│  │  • Kev-4B (:8009)                      │   │
│  │    Decision model, local inference     │   │
│  │                                        │   │
│  │  • MiniCPM (:8888)                     │   │
│  │    Vision + multimodal, 3B model       │   │
│  │                                        │   │
│  │  • Hermes Agent (:3000)                │   │
│  │    Agent orchestrator, local runtime   │   │
│  │                                        │   │
│  │  • Ollama (:11434)                     │   │
│  │    DeepSeek-R1, Qwen, Phi              │   │
│  └────────────────────────────────────────┘   │
│                                                 │
│  ┌────────────────────────────────────────┐   │
│  │  VS Code (Dev Environment)             │   │
│  ├────────────────────────────────────────┤   │
│  │  • Extensions:                         │   │
│  │    - Dev Containers (Docker)           │   │
│  │    - Python                            │   │
│  │    - Node.js                           │   │
│  │    - REST Client                       │   │
│  │  • Workspace: ~/studex-local-stack     │   │
│  │  • Debug: All models logged locally    │   │
│  └────────────────────────────────────────┘   │
│                                                 │
│  ┌────────────────────────────────────────┐   │
│  │  Local Storage (No Cloud)              │   │
│  ├────────────────────────────────────────┤   │
│  │  • SQLite (not Supabase)               │   │
│  │  • Obsidian vault (local)              │   │
│  │  • Models cache (~30GB)                │   │
│  └────────────────────────────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘
       ↓
NO INTERNET REQUIRED ✓
```

---

## Step 1: Docker Setup (All Local)

**docker-compose-offline.yml:**

```yaml
version: '3.8'

services:
  # Kev Decision Model (Local)
  kev:
    image: python:3.11-slim
    volumes:
      - ~/.cache/huggingface:/root/.cache
      - ./models/kev:/models
    working_dir: /app
    command: |
      bash -c "
        pip install -q typesafe-sdk torch transformers huggingface-hub &&
        python -m kev.serve --run jaredpalmer/kev-4b --port 8009 --device cpu
      "
    ports:
      - "8009:8009"
    environment:
      - HF_HOME=/root/.cache
      - TRANSFORMERS_CACHE=/root/.cache
    networks:
      - offline-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8009/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MiniCPM Vision Model (Local)
  minicpm:
    image: python:3.11-slim
    volumes:
      - ~/.cache/huggingface:/root/.cache
      - ./models/minicpm:/models
    working_dir: /app
    command: |
      bash -c "
        pip install -q fastapi uvicorn torch transformers pillow &&
        python minicpm_server.py
      "
    ports:
      - "8888:8888"
    environment:
      - HF_HOME=/root/.cache
      - DEVICE=cpu
    networks:
      - offline-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8888/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Hermes Agent (Local Orchestrator)
  hermes:
    image: node:20-alpine
    volumes:
      - ./hermes-agent:/app
      - ./models:/models
    working_dir: /app
    command: npm run dev
    ports:
      - "3000:3000"
    environment:
      - KEV_BASE_URL=http://kev:8009
      - MINICPM_BASE_URL=http://minicpm:8888
      - OLLAMA_BASE_URL=http://ollama:11434
      - NODE_ENV=development
    networks:
      - offline-network
    depends_on:
      kev:
        condition: service_healthy
      minicpm:
        condition: service_healthy

  # Ollama (Local LLMs)
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
      - ./models/ollama:/models
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    networks:
      - offline-network
    command: serve

  # SQLite (Local DB, no cloud)
  sqlite-admin:
    image: graphiteapp/graphite:latest
    ports:
      - "8080:8080"
    volumes:
      - ./data/sqlite.db:/app/data/app.db
    networks:
      - offline-network

networks:
  offline-network:
    driver: bridge

volumes:
  ollama_data:
    driver: local
```

---

## Step 2: MiniCPM Server (Vision Model)

**minicpm_server.py:**

```python
"""
MiniCPM Vision Server
Local multimodal model for image understanding
"""

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
import io
import torch
from transformers import AutoModel, AutoTokenizer
import uvicorn

app = FastAPI()

# Load MiniCPM (3B model, fits M1)
model = AutoModel.from_pretrained(
    "openbmb/MiniCPM-V",
    trust_remote_code=True,
    device_map="cpu"
)
tokenizer = AutoTokenizer.from_pretrained(
    "openbmb/MiniCPM-V",
    trust_remote_code=True
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """
    Send image to MiniCPM for analysis
    """
    # Read image
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    
    # Prepare prompt
    prompt = "Analyze this image and describe what you see."
    
    # Inference
    with torch.no_grad():
        response = model.chat(
            image=image,
            msgs=[{"role": "user", "content": prompt}],
            tokenizer=tokenizer
        )
    
    return {
        "image_analysis": response,
        "model": "MiniCPM-V",
        "local": True
    }

@app.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    """
    OCR via MiniCPM (local, no cloud)
    """
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    
    prompt = "Extract all text from this image."
    
    with torch.no_grad():
        response = model.chat(
            image=image,
            msgs=[{"role": "user", "content": prompt}],
            tokenizer=tokenizer
        )
    
    return {
        "extracted_text": response,
        "model": "MiniCPM-V",
        "offline": True
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8888,
        log_level="info"
    )
```

---

## Step 3: Hermes Agent (Connects Everything)

**hermes-agent/src/index.ts:**

```typescript
/**
 * Hermes Agent
 * Orchestrates Kev + MiniCPM + Local models
 * Zero internet, fully local
 */

import express from 'express';
import axios from 'axios';
import { TypeSafeClient } from 'typesafe-sdk';

const app = express();
app.use(express.json());

// Local service endpoints
const KEV_URL = process.env.KEV_BASE_URL || 'http://localhost:8009';
const MINICPM_URL = process.env.MINICPM_BASE_URL || 'http://localhost:8888';
const OLLAMA_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';

// Initialize Kev client (local)
const kev = new TypeSafeClient({
  api_key: 'local',
  base_url: KEV_URL,
  model: 'kev-4b'
});

class HermesAgent {
  async decide(input: string, questions: any) {
    /**
     * Ask Kev to decide (local inference)
     */
    try {
      const response = await axios.post(`${KEV_URL}/v1/systemone`, {
        state: input,
        model: 'kev-4b',
        questions: questions
      });

      return response.data;
    } catch (error) {
      console.error('[Hermes] Kev decision failed:', error);
      throw error;
    }
  }

  async analyzeImage(imagePath: string) {
    /**
     * Send image to MiniCPM (local)
     */
    const formData = new FormData();
    formData.append('file', fs.createReadStream(imagePath));

    const response = await axios.post(
      `${MINICPM_URL}/analyze-image`,
      formData,
      {
        headers: formData.getHeaders()
      }
    );

    return response.data;
  }

  async generateText(prompt: string, model: string = 'deepseek-r1') {
    /**
     * Generate text via Ollama (local)
     * No internet, no API key
     */
    const response = await axios.post(`${OLLAMA_URL}/api/generate`, {
      model: model,
      prompt: prompt,
      stream: false
    });

    return response.data.response;
  }

  async orchestrate(task: string) {
    /**
     * Full orchestration loop:
     * 1. Decide (Kev)
     * 2. Analyze (MiniCPM if image)
     * 3. Generate (Ollama)
     * 4. Execute
     */
    console.log(`[Hermes] Task: ${task}`);

    // Step 1: Kev decides
    const decision = await this.decide(task, {
      action_type: {
        type: 'choice',
        criteria: {
          generate: 'Generate content',
          analyze: 'Analyze image',
          decide: 'Make decision',
          execute: 'Execute action'
        }
      },
      confidence: {
        type: 'score'
      }
    });

    console.log(`[Hermes] Kev decided: ${decision.answers.action_type.choice}`);

    // Step 2: Execute based on decision
    if (decision.answers.action_type.choice === 'generate') {
      const content = await this.generateText(task);
      return { status: 'generated', content };
    }

    if (decision.answers.action_type.choice === 'analyze') {
      const analysis = await this.analyzeImage(task);
      return { status: 'analyzed', analysis };
    }

    return { status: 'complete', decision };
  }
}

const hermes = new HermesAgent();

// API Endpoints
app.post('/orchestrate', async (req, res) => {
  const { task } = req.body;
  try {
    const result = await hermes.orchestrate(task);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/decide', async (req, res) => {
  const { input, questions } = req.body;
  try {
    const result = await hermes.decide(input, questions);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/analyze', async (req, res) => {
  const { image_path } = req.body;
  try {
    const result = await hermes.analyzeImage(image_path);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    services: {
      kev: `${KEV_URL}`,
      minicpm: `${MINICPM_URL}`,
      ollama: `${OLLAMA_URL}`
    }
  });
});

app.listen(3000, () => {
  console.log('[Hermes] Agent running on :3000 (no internet required)');
});
```

---

## Step 4: VS Code Setup

**Create:** `.devcontainer/devcontainer.json`

```json
{
  "name": "Studex Local Offline Stack",
  "dockerComposeFile": "../docker-compose-offline.yml",
  "service": "hermes",
  "workspaceFolder": "/app",
  
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-vscode-remote.remote-containers",
        "ms-python.python",
        "ms-vscode.makefile-tools",
        "REST Client.rest-client",
        "eamodio.gitlens",
        "ms-vscode-docker.docker"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.linting.enabled": true,
        "editor.formatOnSave": true
      }
    }
  },

  "forwardPorts": [8009, 8888, 3000, 11434, 8080],
  "portsAttributes": {
    "8009": {"label": "Kev", "onAutoForward": "silent"},
    "8888": {"label": "MiniCPM", "onAutoForward": "silent"},
    "3000": {"label": "Hermes", "onAutoForward": "notify"},
    "11434": {"label": "Ollama", "onAutoForward": "silent"},
    "8080": {"label": "SQLite Admin", "onAutoForward": "silent"}
  },

  "postCreateCommand": "npm install && npm run dev"
}
```

---

## Step 5: Launch (VS Code)

**In VS Code:**

1. Install "Remote - Containers" extension
2. Open command palette: `Remote-Containers: Reopen in Container`
3. Wait for Docker to start all services (~5 min first time)
4. All endpoints ready:
   - Kev: `http://localhost:8009`
   - MiniCPM: `http://localhost:8888`
   - Hermes: `http://localhost:3000`
   - Ollama: `http://localhost:11434`

**Terminal in VS Code:**

```bash
# Check services
curl http://localhost:3000/health

# Test Kev decision
curl -X POST http://localhost:3000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Should I publish content?",
    "questions": {
      "publish": {"type": "noul"}
    }
  }'

# Test MiniCPM
curl -F "file=@image.jpg" http://localhost:3000/analyze

# Test Ollama
curl -X POST http://localhost:11434/api/generate \
  -d '{
    "model": "deepseek-r1",
    "prompt": "Write a greeting"
  }'
```

---

## File Structure

```
studex-local-stack/
├── .devcontainer/
│   └── devcontainer.json          # VS Code container config
├── docker-compose-offline.yml     # All local services
├── hermes-agent/
│   ├── src/
│   │   └── index.ts               # Hermes orchestrator
│   └── package.json
├── models/                        # Model cache (~30GB)
│   ├── kev/
│   ├── minicpm/
│   └── ollama/
├── data/
│   └── sqlite.db                  # Local database
├── minicpm_server.py              # Vision model server
└── README.md
```

---

## How They Connect

```
VS Code
  ↓
Hermes Agent (:3000)
  ├─→ Kev (:8009) — "Should I do X?"
  │   └─ Local decision model
  │
  ├─→ MiniCPM (:8888) — "Analyze this image"
  │   └─ Local vision model
  │
  └─→ Ollama (:11434) — "Write content"
      └─ DeepSeek-R1, Qwen, Phi (local)

All local. No internet. No API keys. No cloud.
```

---

## Offline Capabilities

✅ **What works (fully local):**
- Kev decisions (instant)
- Image analysis (MiniCPM)
- Text generation (Ollama)
- Agent orchestration (Hermes)
- Sqlite persistence
- VS Code debugging

❌ **What doesn't (requires internet):**
- First-time model downloads (use airplane mode after)
- Blotato posting (but can cache locally)
- External APIs

---

## Boot Sequence

**Terminal 1: Start Stack**
```bash
cd studex-local-stack
docker-compose -f docker-compose-offline.yml up -d

# Wait for health checks
docker-compose logs -f
```

**Terminal 2: Open VS Code**
```bash
code .
# Click: "Reopen in Container"
```

**Terminal 3: Test**
```bash
npm run test:offline
# Should see:
# ✓ Kev responding
# ✓ MiniCPM responding
# ✓ Ollama responding
# ✓ Zero internet calls
```

---

## Cost

| Component | Cost |
|-----------|------|
| Docker Desktop (Mac) | Free |
| Kev model | Free (local) |
| MiniCPM model | Free (local) |
| Ollama + models | Free (local) |
| VS Code | Free |
| **Total** | **$0/mo** |

---

## Next: Integrate with Arcade

Once local stack is live:
```bash
# Arcade talks to Hermes
# Hermes orchestrates Kev + MiniCPM + Ollama
# Zero internet, fully autonomous
```

---

