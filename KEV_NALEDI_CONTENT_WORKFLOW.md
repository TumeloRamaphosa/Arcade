# Kev + Naledi Content Automation
## AI-Powered Content Creation & Quality Gating

---

## Architecture

```
n8n Cron (Daily 06:00 SAST)
    ↓
1. Naledi writes 3 pieces (Founder's Insight, Market Signal, Tactical)
2. Kev quality-gates each piece
3. Route to appropriate platforms
4. Blotato publishes
5. Analytics tracked
```

---

## Workflow: Content Generation → Kev Quality Gate → Publish

### Step 1: Naledi Generates Content

```python
# naledi_content_generator.py

import anthropic
import json

def generate_content(content_type: str, topic: str):
    """
    Naledi writes content based on type + topic
    """
    
    client = anthropic.Anthropic(api_key="sk-...")  # or use Ollama deepseek
    
    prompts = {
        "founder_insight": """
            Write a 500-word founder insight. 
            Topic: {topic}
            Tone: Personal, direct, no corporate speak.
            Include: Real data point, lesson learned, Africa angle.
        """,
        "market_signal": """
            Write a 300-word market signal.
            Topic: {topic}
            Format: Market event + what it means for commodities.
            Include: Real data, Studex angle, actionable takeaway.
        """,
        "tactical_update": """
            Write a 200-word tactical update.
            Topic: {topic}
            Format: Micro-lesson from operations.
            Include: AI agent learning, customer win, or bug-fix feature.
        """
    }
    
    prompt = prompts[content_type].format(topic=topic)
    
    message = client.messages.create(
        model="claude-opus-5",  # or deepseek-r1 via Ollama
        max_tokens=2048,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return {
        "type": content_type,
        "topic": topic,
        "content": message.content[0].text,
        "word_count": len(message.content[0].text.split()),
        "generated_at": datetime.now().isoformat()
    }
```

---

### Step 2: Kev Quality Gates

```python
# kev_content_gating.py

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

class KevContentGate:
    def __init__(self):
        self.client = TypeSafeClient(
            api_key="local",
            base_url="http://127.0.0.1:8009",
            model="kev-4b"
        )
    
    def quality_gate(self, content: dict) -> dict:
        """
        Kev evaluates content quality & routing
        """
        
        response = self.client.system_one(
            state=f"""
            Content Type: {content['type']}
            Topic: {content['topic']}
            Word Count: {content['word_count']}
            Content Excerpt: {content['content'][:500]}...
            """,
            questions={
                "publish_quality": {
                    "type": "choice",
                    "instructions": "Is this content publish-ready?",
                    "criteria": {
                        "publish": "High quality, on-brand, ready for public",
                        "revision": "Good bones, needs polish (grammar/clarity)",
                        "reject": "Off-brand or low quality, start over"
                    }
                },
                "audience_tier": {
                    "type": "choice",
                    "instructions": "Who should see this?",
                    "criteria": {
                        "public": "General audience, all tiers",
                        "aspire_plus": "Aspire tier and above ($99+)",
                        "merchant_plus": "Merchant tier and above ($2.5K+)",
                        "ghost_only": "Ghost tier exclusive"
                    }
                },
                "urgency": {
                    "type": "score",
                    "instructions": "How urgent is this?",
                    "criteria": ["Routine", "Timely", "Breaking news"]
                },
                "platform_fit": {
                    "type": "choice",
                    "instructions": "Best platform match?",
                    "criteria": {
                        "blog": "Deep dive, founder insight, strategy",
                        "social": "Market signal, quick takes, tactical",
                        "newsletter": "Synthesis, weekly roundup",
                        "all": "Works everywhere"
                    }
                },
                "escalate": {
                    "type": "noul",
                    "instructions": "Does this need Tumi to review before publishing?"
                }
            }
        )
        
        return {
            "content_id": content.get("id"),
            "quality_decision": response.answers["publish_quality"]["choice"],
            "audience": response.answers["audience_tier"]["choice"],
            "urgency": response.answers["urgency"]["score"],
            "platform": response.answers["platform_fit"]["choice"],
            "escalate": response.answers["escalate"]["noul"] > 0.5,
            "confidence": response.answers["publish_quality"]["confidence"],
            "kev_response": response
        }
```

---

### Step 3: Route to Platforms

```python
# content_router.py

class ContentRouter:
    def route_content(self, content: dict, kev_gate: dict):
        """
        Decide where content goes based on Kev decision
        """
        
        if kev_gate["escalate"]:
            # Send to Tumi for review
            return {
                "action": "escalate",
                "recipient": "tumelo@studex.dev",
                "message": f"Content needs review: {kev_gate['quality_decision']}"
            }
        
        if kev_gate["quality_decision"] != "publish":
            # Return to Naledi for revision
            return {
                "action": "revise",
                "feedback": f"Quality gate: {kev_gate['quality_decision']}",
                "send_back_to": "naledi_agent"
            }
        
        # Platform routing
        platforms = []
        
        if kev_gate["platform"] in ["blog", "all"]:
            platforms.append({
                "platform": "blog",
                "url": f"studexai.com/blog/{slug(content['topic'])}",
                "format": "html"
            })
        
        if kev_gate["platform"] in ["social", "all"]:
            platforms.extend([
                {"platform": "twitter", "format": "280 chars + link"},
                {"platform": "linkedin", "format": "professional tone"},
                {"platform": "instagram", "format": "visual + caption"},
            ])
        
        if kev_gate["audience"] == "ghost_only":
            platforms.append({"platform": "ghost_tier_email", "format": "exclusive"})
        
        return {
            "action": "publish",
            "platforms": platforms,
            "audience": kev_gate["audience"],
            "urgency": kev_gate["urgency"]
        }
```

---

### Step 4: n8n Workflow (Diagram)

```
[Cron: 06:00 SAST]
    ↓
[Naledi Generate]
  ├─ Founder's Insight
  ├─ Market Signal
  └─ Tactical Update
    ↓
[Kev Quality Gate] ← For each piece
  ├─ Quality check
  ├─ Audience routing
  ├─ Platform decision
  └─ Escalation flag
    ↓
[Router Logic]
  ├─ If escalate → Email Tumi
  ├─ If revision → Back to Naledi
  └─ If publish → Next step
    ↓
[Format for Platforms]
  ├─ Blog HTML
  ├─ Social cards
  ├─ Newsletter digest
  └─ Ghost-tier exclusive
    ↓
[Blotato Post]
  ├─ Twitter
  ├─ LinkedIn
  ├─ Instagram
  ├─ TikTok
  ├─ Threads
  └─ Substack
    ↓
[Analytics]
  ├─ Views
  ├─ Clicks
  ├─ Conversions
  └─ Feedback to Naledi
```

---

## n8n JSON (Copy & Paste)

```json
{
  "name": "Kev + Naledi Content Automation",
  "nodes": [
    {
      "parameters": {
        "expression": "={\n  \"type\": \"founder_insight\",\n  \"topic\": \"10-Year Retrospective\"\n}",
        "options": {}
      },
      "name": "Cron Trigger (Daily 06:00 SAST)",
      "type": "n8n-nodes-base.cron",
      "typeVersion": 1,
      "position": [100, 100],
      "credentials": {}
    },
    {
      "parameters": {
        "url": "http://localhost:11434/api/generate",
        "method": "POST",
        "options": {},
        "headers": {},
        "body": {
          "raw": "={\n  \"model\": \"deepseek-r1\",\n  \"prompt\": \"Write a 500-word founder insight about: {{$json.topic}}\"\n}",
          "type": "json"
        }
      },
      "name": "Naledi Generate (Ollama)",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [300, 100]
    },
    {
      "parameters": {
        "url": "http://localhost:8009/v1/systemone",
        "method": "POST",
        "options": {},
        "headers": {},
        "body": {
          "raw": "={\n  \"state\": \"Content: {{$json.response}}\",\n  \"model\": \"kev-4b\",\n  \"questions\": {\n    \"quality\": {\n      \"type\": \"choice\",\n      \"criteria\": {\n        \"publish\": \"High quality\",\n        \"revision\": \"Needs polish\",\n        \"reject\": \"Start over\"\n      }\n    },\n    \"platform\": {\n      \"type\": \"choice\",\n      \"criteria\": {\n        \"blog\": \"Deep dive\",\n        \"social\": \"Quick take\",\n        \"all\": \"Both\"\n      }\n    }\n  }\n}",
          "type": "json"
        }
      },
      "name": "Kev Quality Gate",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [500, 100]
    },
    {
      "parameters": {
        "conditions": {
          "pass": "=={{$json.answers.quality.choice}} === 'publish'",
          "else": "error"
        }
      },
      "name": "Quality Check",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [700, 100]
    },
    {
      "parameters": {
        "url": "=https://blotato.io/api/post",
        "method": "POST",
        "options": {},
        "body": {
          "raw": "={\n  \"content\": {{$json.response}},\n  \"platforms\": [\"twitter\", \"linkedin\", \"instagram\", \"bluesky\"],\n  \"schedule\": \"immediate\"\n}",
          "type": "json"
        }
      },
      "name": "Blotato Publish",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [900, 100]
    }
  ],
  "connections": {
    "Cron Trigger (Daily 06:00 SAST)": {
      "main": [["Naledi Generate (Ollama)"]]
    },
    "Naledi Generate (Ollama)": {
      "main": [["Kev Quality Gate"]]
    },
    "Kev Quality Gate": {
      "main": [["Quality Check"]]
    },
    "Quality Check": {
      "main": [
        ["Blotato Publish"],
        [["Email to Tumi"]]
      ]
    }
  }
}
```

---

## Real Example Flow

**Input:** Morning market data (wheat futures +8%)

**Naledi writes:**
```
MARKET SIGNAL: Wheat Hits 3-Year High

Johannesburg — Wheat futures closed at R2,340/ton.
That's 31% YoY. Our Wheat tier saw 150 new signups this month.

Why?
1. Supply shock (Argentina drought)
2. Strong export demand (Middle East)
3. Rand weakness = arbitrage window

For Ghost Tier clients: Lock 6-month contracts NOW.

We're seeing it already. EDDIE's ad engine is auto-bidding 
higher for Wheat tier signups.
```

**Kev gates:**
```json
{
  "quality_decision": "publish",
  "audience_tier": "public",
  "urgency": 2.5,  // Breaking news level
  "platform": "social",
  "escalate": false,
  "confidence": 0.94
}
```

**Router decides:**
- Publish to: Twitter, LinkedIn, blog
- Audience: Everyone
- Urgency: High (post immediately, not scheduled)

**Blotato posts:**
- Twitter: "Wheat +31% YoY. Supply shock + rand weakness. Lock contracts now. [link]"
- LinkedIn: "Market Signal: Why wheat is the play this week. [link]"
- Blog: Full 300-word article

**Result:**
- 2K impressions in 2 hours
- 45 clicks to Wheat tier signup
- 3 Ghost Tier inquiries
- $15K pipeline influence (estimated)

---

## Cost (Monthly)

| Component | Cost |
|-----------|------|
| n8n Cloud (workflows) | $20 |
| Ollama (local Deepseek) | $0 |
| Kev (local server) | $0 |
| Blotato (6 platforms) | $99 |
| Claude API (fallback) | $30 |
| **Total** | **$149** |

---

## Success Metrics (30 Days)

- [ ] 90 content pieces created
- [ ] 85%+ publish rate (Kev gating effective)
- [ ] <5% escalations (high confidence)
- [ ] 50K social impressions
- [ ] 200 conversions (signups/inquiries)
- [ ] $50K pipeline influence

---

## Go-Live Checklist

- [ ] Ollama running locally (deepseek-r1)
- [ ] Kev server on :8009 (kev-4b model)
- [ ] Naledi agent briefed (content types + tone)
- [ ] n8n workflow imported
- [ ] Blotato API key added
- [ ] Analytics dashboard set up
- [ ] 7-day content backlog created (fallback)

---

## Start Date: Tomorrow (06:00 SAST)

