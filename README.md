# Arcade Gaming Ecosystem
## AI-Powered Autonomous Game Master

Arcade is where agents become NPCs. Kev makes decisions. Charlie talks. Naledi spins the story.

---

## Architecture

```
Player Input (text/voice)
    ↓
Charlie (ElevenLabs/Twilio voice agent)
Transcribes & processes player intent
    ↓
Kev (Decision Model Router)
Analyzes: sentiment, action type, game state
Routes to: combat, dialogue, exploration, quest
    ↓
Naledi (Game Master)
Generates narrative outcome + NPC dialogue
Updates game state
    ↓
Game State DB (Supabase)
Player progress, inventory, karma, quest log
    ↓
Response (text + voice)
Back to player
```

---

## Core Components

### 1. Kev Router (`kev_router.py`)
```python
# Routes player action to game system
# Input: "I want to attack the merchant"
# Output: { "action_type": "combat", "target": "merchant", "difficulty": 8 }

from typesafe_sdk import Choice, TypeSafeClient

client = TypeSafeClient(
    api_key="local",
    base_url="http://127.0.0.1:8009",
    model="kev-4b",
)

response = client.system_one(
    state=player_action,
    questions={
        "action_type": {
            "type": "choice",
            "instructions": "What is the player trying to do?",
            "criteria": {
                "combat": "Attack, fight, duel",
                "dialogue": "Talk, negotiate, persuade",
                "exploration": "Move, search, discover",
                "quest": "Accept mission, complete objective",
                "trade": "Buy, sell, exchange",
            }
        },
        "sentiment": {
            "type": "score",
            "instructions": "What is player mood?",
            "criteria": ["Calm", "Excited", "Angry", "Confused"]
        },
        "escalate": {
            "type": "noul",
            "instructions": "Does this need Naledi to intervene?"
        }
    }
)

return response.answers
```

### 2. Charlie Voice Agent (`charlie_agent.py`)
```python
# Voice-in, voice-out NPC interaction

from twilio.rest import Client
import openai

class CharliNPC:
    def __init__(self):
        self.twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        self.elevenlabs = ElevenLabs(api_key=ELEVENLABS_KEY)
    
    def process_call(self, player_audio):
        # 1. Transcribe player audio
        transcript = self.twilio.transcribe(player_audio)
        
        # 2. Send to Kev router
        action = kev_router(transcript)
        
        # 3. Get narrative from Naledi
        npc_response = naledi_game_master(action)
        
        # 4. Synthesize to voice
        voice_audio = self.elevenlabs.tts(npc_response.dialogue)
        
        # 5. Play back
        return voice_audio
```

### 3. Naledi Game Master (`naledi_gm.py`)
```python
# Generates narrative + NPC dialogue based on Kev decision

class NalediGameMaster:
    def __init__(self):
        self.llm = "deepseek-r1"  # Local via Ollama
        self.game_lore = load_game_lore()
    
    def generate_outcome(self, kev_decision, game_state):
        prompt = f"""
        Game State: {game_state}
        Player Action: {kev_decision['action_type']}
        Target: {kev_decision['target']}
        Difficulty: {kev_decision['difficulty']}
        
        Generate:
        1. Outcome (success/fail/partial)
        2. NPC dialogue (2-3 sentences, character voice)
        3. State changes (inventory, karma, quest progress)
        """
        
        response = deepseek.generate(prompt)
        return parse_response(response)
```

### 4. Game State (`game_state.py`)
```python
# Supabase schema

class GameState(Base):
    __tablename__ = "players"
    
    id = Column(String, primary_key=True)
    player_name = Column(String)
    location = Column(String)
    health = Column(Integer, default=100)
    karma = Column(Integer, default=0)
    inventory = Column(JSON)
    quest_log = Column(JSON)
    dialogue_history = Column(JSON)
    last_action_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
```

---

## Quick Start

### 1. Install dependencies
```bash
cd Arcade
uv sync
```

### 2. Start Kev locally
```bash
uv run python -m kev.serve --run jaredpalmer/kev-4b --port 8009
```

### 3. Start Ollama (for Naledi)
```bash
ollama run deepseek-r1
# Or: qwen2.5:14b
```

### 4. Set up Supabase
```bash
# .env
SUPABASE_URL=your-project-url
SUPABASE_KEY=your-key
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
ELEVENLABS_API_KEY=your-key
```

### 5. Launch game
```bash
python arcade_game.py
```

Game will:
- Listen for voice input (Twilio/ElevenLabs)
- Route to Kev for action classification
- Generate narrative via Naledi (DeepSeek)
- Update game state in Supabase
- Respond with voice

---

## Game Design (Alpha)

**Setting:** Studex Trading Post — a commodities bazaar in future Johannesburg

**NPCs:**
- **Charlie** (Merchant voice) — Can trade, share market gossip
- **Naledi** (Guild Master voice) — Assigns quests, tracks karma
- **EDDIE** (Price Oracle) — Gives market predictions

**Player Loop:**
1. Arrive at trading post (voice call: +27... arcade number)
2. Charlie greets you
3. Choose action (trade, gather intel, quest, gamble)
4. Kev routes decision
5. Naledi generates outcome
6. Repeat or hang up

**Progression:**
- Karma system (ethics matter)
- Inventory (commodities you hold)
- Quest log (multi-step missions)
- Leaderboard (top traders this month)

---

## Features (MVP)

- [x] Kev router backbone
- [x] Charlie voice scaffold
- [x] Naledi narrative engine
- [x] Supabase game state
- [ ] Combat system
- [ ] Trading mechanics
- [ ] Quest generator
- [ ] Leaderboard + rankings
- [ ] Multi-player concurrent calls
- [ ] Rich dialogue trees

---

## API Endpoints

```
POST /game/action
{
  "player_id": "tumi-001",
  "action": "I want to buy wheat futures",
  "voice_input": true
}

Response:
{
  "outcome": "success",
  "npc_dialogue": "Good choice! Wheat is up 8% this week...",
  "state_delta": {
    "inventory": { "wheat_futures": 100 },
    "karma": 1
  },
  "voice_output": "audio.mp3"
}
```

---

## Deployment

**Development:** Local (Kev on 8009, Ollama on 11434)

**Production:** 
- Kev → Modal (HTTPS endpoint)
- Deepseek → Modal or HuggingFace Space
- Supabase → Cloud
- Twilio/ElevenLabs → SaaS (already managed)

---

## Next Steps

1. Build Kev router (action classification)
2. Wire Charlie voice agent
3. Implement Naledi outcome generation
4. Launch MVP (closed beta)
5. Iterate based on player feedback

---

