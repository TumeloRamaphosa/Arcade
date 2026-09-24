# Kev Autonomous Agent - Deployment Guide

**Kev is now:** A talking decision-making agent that listens, decides, acts, and speaks.

---

## What Kev Does (Voice Loop)

```
User calls Kev: +27 XXXX XXXXX (Twilio number)
    ↓
Kev listens (Whisper transcription)
    ↓
Kev decides (Kev model, Kev-4B)
    ↓
Kev acts (executes autonomously or escalates)
    ↓
Kev speaks (ElevenLabs voice synthesis)
    ↓
Conversation complete
```

---

## Setup (30 minutes)

### 1. Requirements

```bash
# Python 3.11+
python --version

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt:**
```
typesafe-sdk==1.0.0
twilio==8.10.0
elevenlabs==0.2.0
supabase==2.1.0
anthropic==0.7.0
flask==2.3.0
python-dotenv==1.0.0
```

### 2. Environment Variables

**.env**
```env
# Kev Model (Local)
KEV_API_KEY=local
KEV_BASE_URL=http://127.0.0.1:8009
KEV_MODEL=kev-4b

# Twilio (Voice I/O)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+27101234567

# ElevenLabs (Voice Output)
ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxxxxx

# Supabase (Memory & State)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJ0eXAiOi...

# Claude (Fallback Reasoning)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx

# Flask
FLASK_ENV=production
FLASK_PORT=5000
```

### 3. Start Kev Model Server

**Terminal 1: Kev Decision Model**
```bash
cd ~/.claude/skills/notebooklm  # or wherever Kev is
python -m kev.serve --run jaredpalmer/kev-4b --port 8009
```

Check it's running:
```bash
curl http://127.0.0.1:8009/v1/systemone
# Should return: model required
```

### 4. Start Kev Agent (Flask)

**Terminal 2: Kev Voice Agent**
```bash
python KEV_AUTONOMOUS_AGENT.py
# Flask running on 0.0.0.0:5000
```

### 5. Wire Twilio Webhook

Go to **Twilio Console** → **Phone Numbers** → Your number

Set **When a call comes in:**
```
URL: https://your-domain.com/kev/call
Method: POST
```

(Or use ngrok for local testing:)
```bash
ngrok http 5000
# Copy HTTPS URL to Twilio webhook
```

### 6. Create Supabase Tables

```sql
-- Decisions table
CREATE TABLE kev_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  input TEXT,
  action TEXT,
  confidence FLOAT,
  can_act_alone BOOLEAN,
  risk FLOAT,
  timestamp TIMESTAMP DEFAULT now()
);

-- Actions table
CREATE TABLE kev_actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_id UUID REFERENCES kev_decisions(id),
  type TEXT,
  command TEXT,
  status TEXT,
  result JSONB,
  timestamp TIMESTAMP DEFAULT now()
);

-- Memory table
CREATE TABLE kev_memory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_state JSONB,
  timestamp TIMESTAMP DEFAULT now()
);

-- Escalations table
CREATE TABLE escalations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  issue TEXT,
  from_agent TEXT,
  confidence FLOAT,
  status TEXT,
  timestamp TIMESTAMP DEFAULT now()
);

-- Learning table
CREATE TABLE kev_learning (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  feedback TEXT,
  decision_id UUID,
  timestamp TIMESTAMP DEFAULT now()
);
```

---

## Test It

### Test 1: Make a Voice Call

```bash
# Use Twilio CLI or your phone
twilio api:core:calls:create \
  --from "+27101234567" \
  --to "+27987654321" \
  --url "https://your-ngrok-url/kev/call"
```

Expected:
- Kev answers
- You speak
- Kev listens + decides + acts
- Kev speaks response
- Call ends

### Test 2: Send SMS

```bash
curl -X POST http://localhost:5000/kev/sms \
  -d "From=+27987654321" \
  -d "Body=Should I publish this blog post?"
```

Expected response:
```
Decision: decide
Action: publish
Response: "Yes, high confidence. Publishing now to 6 platforms."
```

### Test 3: Direct API Call

```python
from KEV_AUTONOMOUS_AGENT import KevAgent

kev = KevAgent()

# Make a decision
decision = kev.decide("I have $50K to spend on ads. What should I do?")
print(decision)

# Act on it
result = kev.act(decision)
print(result)

# Respond
response = kev.respond(decision, result)
print(response)
```

---

## Use Cases (Right Now)

### 1. **Customer Support Agent**
```
Customer calls: "My order is late"
Kev decides: "escalate" (confidence 85%)
Kev acts: Sends to human support
Kev speaks: "I'm escalating you to our support team."
```

### 2. **Content Decision Agent**
```
Input: "Should I publish this market signal?"
Kev decides: "publish" (confidence 92%)
Kev acts: Posts to Blotato (6 platforms)
Kev speaks: "Published to Twitter, LinkedIn, Instagram"
```

### 3. **Game Master (Arcade)**
```
Player: "I attack the merchant"
Kev decides: "execute" (action_type=combat, difficulty=7)
Kev acts: Updates game state
Kev speaks: "You hit for 15 damage. Merchant is angry!"
```

### 4. **Autonomous Executor**
```
Input: "Execute my daily marketing workflow"
Kev decides: "execute" (confidence 95%)
Kev acts: Runs n8n workflow
Kev speaks: "Workflow started. Check dashboard for updates."
```

---

## Deployment Options

### Option A: Local (Dev/Testing)
- Kev on :8009
- Flask on :5000
- Ngrok for Twilio
- Perfect for testing

### Option B: Railway (Production)
```bash
# Deploy Flask app
railway up
```

### Option C: Modal (Serverless)
```bash
modal deploy KEV_AUTONOMOUS_AGENT.py
```

### Option D: Docker

**Dockerfile**
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY KEV_AUTONOMOUS_AGENT.py .
EXPOSE 5000
CMD ["python", "KEV_AUTONOMOUS_AGENT.py"]
```

```bash
docker build -t kev-agent .
docker run -p 5000:5000 --env-file .env kev-agent
```

---

## Monitoring

### Check Decisions (Real-Time)
```bash
curl http://localhost:5000/kev/status
# Returns: last 10 decisions, confidence, actions
```

### View Memory
```sql
SELECT * FROM kev_decisions ORDER BY timestamp DESC LIMIT 10;
```

### Track Actions
```sql
SELECT action, status, COUNT(*) 
FROM kev_actions 
GROUP BY action, status;
```

### Escalations Alert
```sql
SELECT * FROM escalations WHERE status='pending_review';
-- Alert Tumelo if > 0
```

---

## Cost (Monthly)

| Component | Cost |
|-----------|------|
| Twilio (voice) | $50 |
| ElevenLabs (TTS) | $30 |
| Supabase (storage) | $25 |
| Claude API (fallback) | $20 |
| Railway deploy | $7 |
| **Total** | **$132** |

---

## Roadmap

**Week 1:**
- [ ] Deploy locally + test voice loop
- [ ] Integrate with Blotato for content decisions
- [ ] Wire game state updates for Arcade

**Week 2:**
- [ ] Add learning feedback loop
- [ ] Create Kev skill registry (10 trained behaviors)
- [ ] Launch as internal API

**Month 2:**
- [ ] Open Kev as SaaS API ($99/mo for startups)
- [ ] Train on customer data
- [ ] 100+ autonomous decisions/day

**Month 3:**
- [ ] Kev becomes revenue product
- [ ] $20K ARR from Ghost Tier customers

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Kev not responding | Check http://127.0.0.1:8009 is up |
| Twilio webhook failing | Use ngrok, check logs |
| Voice output silent | Check ELEVENLABS_API_KEY is valid |
| Memory not saving | Check Supabase connection + tables exist |
| Low confidence decisions | Train Kev with more examples |

---

## Next: Integrate with Your Stack

### Wire Kev into EDDIE (Ad Engine)
Kev decides: "Which tier should this customer be in?"
EDDIE executes: "Run ads for Merchant tier"

### Wire Kev into Naledi (CMO)
Kev decides: "Is this content good enough?"
Naledi publishes: "Yes, publish to all platforms"

### Wire Kev into Arcade (Game)
Kev decides: "What's the outcome of this player action?"
Naledi narrates: "You rolled a 7. You move forward..."

---

## Go-Live: TODAY

```bash
# Terminal 1
python -m kev.serve --run jaredpalmer/kev-4b --port 8009

# Terminal 2
python KEV_AUTONOMOUS_AGENT.py

# Terminal 3 (if local testing)
ngrok http 5000

# Then: Set Twilio webhook to ngrok URL
# Call: Your Twilio number
# Kev answers!
```

---

