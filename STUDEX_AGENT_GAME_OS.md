# Studex Agent Game OS
## Play Games. Agents Run the Business.

**Concept:** Mobile/desktop app where you play Arcade while agents autonomously:
- Write content (Naledi)
- Route decisions (Kev)
- Spend ad budget (EDDIE)
- Run 24/7 operations

**Stack:** React Native (mobile) + Electron (desktop) + Node.js orchestrator

---

## Architecture

```
┌─────────────────────────────────────────┐
│         STUDEX AGENT GAME OS            │
├─────────────────────────────────────────┤
│                                         │
│  ┌────────────────────────────────┐   │
│  │   FOREGROUND (Player)          │   │
│  │   • Arcade Game (Trading Post) │   │
│  │   • Real-time game state       │   │
│  │   • Voice chat with NPCs       │   │
│  └────────────────────────────────┘   │
│                                         │
│  ┌────────────────────────────────┐   │
│  │   BACKGROUND (Agents)          │   │
│  │   • Kev (decision routing)      │   │
│  │   • Naledi (content writing)    │   │
│  │   • EDDIE (ad optimization)     │   │
│  │   • Charlie (voice NPC)         │   │
│  │   • RALF (daily coordinator)    │   │
│  └────────────────────────────────┘   │
│                                         │
│  ┌────────────────────────────────┐   │
│  │   DASHBOARD (Live Updates)     │   │
│  │   • Agent activity feed        │   │
│  │   • Revenue tracker            │   │
│  │   • Decision log               │   │
│  │   • Notifications              │   │
│  └────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

## File Structure

```
studex-agent-game-os/
├── mobile/                          # React Native app
│   ├── ios/
│   ├── android/
│   ├── src/
│   │   ├── screens/
│   │   │   ├── ArcadeGameScreen.tsx
│   │   │   ├── AgentDashboardScreen.tsx
│   │   │   └── RevenueTrackerScreen.tsx
│   │   ├── components/
│   │   │   ├── GameCanvas.tsx
│   │   │   ├── AgentActivityFeed.tsx
│   │   │   └── VoiceInterface.tsx
│   │   └── App.tsx
│   └── package.json
│
├── desktop/                         # Electron app
│   ├── src/
│   │   ├── main.ts
│   │   └── preload.ts
│   └── package.json
│
├── backend/                         # Agent orchestration
│   ├── src/
│   │   ├── orchestrator.ts
│   │   ├── agents/
│   │   │   ├── kev-agent.ts
│   │   │   ├── naledi-agent.ts
│   │   │   ├── eddie-agent.ts
│   │   │   └── charlie-agent.ts
│   │   ├── game/
│   │   │   └── arcade-engine.ts
│   │   ├── api/
│   │   │   └── websocket.ts
│   │   └── db/
│   │       └── supabase.ts
│   └── package.json
│
├── docker-compose.yml               # Local dev stack
└── README.md
```

---

## Core Components

### 1. Game Layer (Foreground)

**ArcadeGameScreen.tsx:**
```typescript
export const ArcadeGameScreen = () => {
  const [gameState, setGameState] = useState({
    player: {
      health: 100,
      inventory: [],
      karma: 0,
      location: "Trading Post"
    },
    npcs: ["Charlie (Merchant)", "Naledi (GM)", "EDDIE (Price Oracle)"],
    activeAgent: null
  });

  const handlePlayerAction = async (action: string) => {
    // Send action to backend
    const response = await fetch("ws://localhost:3000/game/action", {
      method: "POST",
      body: JSON.stringify({ action, player_id: "tumi" })
    });

    // Kev decides outcome on backend
    // Naledi narrates
    // Game state updates in real-time
    setGameState(response.data.game_state);
  };

  return (
    <View style={styles.container}>
      <GameCanvas gameState={gameState} />
      <VoiceInterface onAction={handlePlayerAction} />
      <AgentActivityFeed activeAgent={gameState.activeAgent} />
    </View>
  );
};
```

### 2. Agent Orchestrator (Background)

**orchestrator.ts:**
```typescript
import { KevAgent } from "./agents/kev-agent";
import { NalediAgent } from "./agents/naledi-agent";
import { EDDIEAgent } from "./agents/eddie-agent";
import { CharlieAgent } from "./agents/charlie-agent";

export class StudexOrchestrator {
  private kev: KevAgent;
  private naledi: NalediAgent;
  private eddie: EDDIEAgent;
  private charlie: CharlieAgent;
  private gameState: GameState;
  private activityFeed: ActivityLog[] = [];

  async start() {
    console.log("[Orchestrator] Starting agent ecosystem...");

    // Morning routine (07:00 SAST)
    this.scheduleMorningRoutine();

    // Continuous loops
    this.startNalediContentLoop();  // Every hour
    this.startEDDIEAdLoop();        // Every 4 hours
    this.startKevDecisionLoop();    // Real-time
    this.startGameLoop();           // Real-time
  }

  private async startGameLoop() {
    // Listen for game actions
    this.gameEngine.on("player_action", async (action) => {
      console.log(`[Game] Player action: ${action}`);

      // Send to Kev for decision
      const decision = await this.kev.decide({
        action_type: "game",
        player_action: action,
        game_state: this.gameState
      });

      console.log(`[Kev] Decision: ${decision.action} (${decision.confidence}% confidence)`);

      // Get outcome from Naledi
      const outcome = await this.naledi.generateGameOutcome({
        action,
        kev_decision: decision
      });

      // Update game state
      this.gameState = outcome.game_state;

      // Broadcast to mobile app
      this.broadcastUpdate({
        type: "game_update",
        data: {
          outcome: outcome.narration,
          game_state: this.gameState,
          active_agent: "Kev + Naledi"
        }
      });

      this.activityFeed.push({
        timestamp: new Date(),
        agent: "Kev + Naledi",
        action: "Processed game action",
        outcome: outcome.narration
      });
    });
  }

  private async startNalediContentLoop() {
    setInterval(async () => {
      console.log("[Naledi] Writing daily content...");

      const content = await this.naledi.writeContent({
        market_data: await this.fetchMarketData(),
        topic: this.selectContentTopic()
      });

      // Kev quality gates
      const decision = await this.kev.decide({
        action_type: "publish",
        content: content
      });

      if (decision.confidence > 0.85) {
        // Auto-publish via Blotato
        await this.publishToBlotato(content);
        console.log("[Naledi] Published to 6 platforms");
      }

      this.broadcastUpdate({
        type: "agent_action",
        data: {
          agent: "Naledi",
          action: "Content written",
          status: decision.confidence > 0.85 ? "published" : "review"
        }
      });
    }, 1000 * 60 * 60); // Every hour
  }

  private async startEDDIEAdLoop() {
    setInterval(async () => {
      console.log("[EDDIE] Optimizing ad spend...");

      const campaign = await this.eddie.analyzeCampaigns();

      // Kev decides routing
      const decision = await this.kev.decide({
        action_type: "ad_spend",
        campaign: campaign
      });

      await this.eddie.executeSpend(decision);

      this.broadcastUpdate({
        type: "agent_action",
        data: {
          agent: "EDDIE",
          action: "Ad optimization",
          spend: campaign.total_spend,
          roas: campaign.roas
        }
      });
    }, 1000 * 60 * 60 * 4); // Every 4 hours
  }

  private broadcastUpdate(update: any) {
    // Send to all connected clients via WebSocket
    this.wsServer.broadcast(JSON.stringify(update));
  }
}
```

### 3. Dashboard (Real-time Activity Feed)

**AgentActivityFeed.tsx:**
```typescript
export const AgentActivityFeed = () => {
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [revenue, setRevenue] = useState(0);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket("ws://localhost:3000/updates");

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);

      if (update.type === "agent_action") {
        // Add to feed
        setActivities([update.data, ...activities]);

        // Update revenue
        if (update.data.spend) {
          setRevenue(r => r + update.data.spend);
        }
      }

      if (update.type === "game_update") {
        // Update game state in game screen
      }
    };

    return () => ws.close();
  }, []);

  return (
    <View style={styles.feedContainer}>
      <Text style={styles.title}>Live Agent Activity</Text>
      <Text style={styles.revenue}>Revenue: ${revenue.toLocaleString()}</Text>

      <FlatList
        data={activities}
        renderItem={({ item }) => (
          <View style={styles.activityItem}>
            <Text style={styles.agentName}>{item.agent}</Text>
            <Text style={styles.action}>{item.action}</Text>
            <Text style={styles.time}>{item.timestamp.toLocaleTimeString()}</Text>
          </View>
        )}
        keyExtractor={(item) => item.timestamp.toString()}
      />
    </View>
  );
};
```

---

## Deployment Architecture

```
┌────────────────────────────────────────┐
│        Your MacBook (Local Dev)        │
├────────────────────────────────────────┤
│  ┌──────────────────────────────────┐ │
│  │  Docker Compose                  │ │
│  ├──────────────────────────────────┤ │
│  │ • Kev model server (:8009)       │ │
│  │ • Ollama DeepSeek (:11434)       │ │
│  │ • Node.js orchestrator (:3000)   │ │
│  │ • Supabase local (:54321)        │ │
│  └──────────────────────────────────┘ │
│                                        │
│  React Native App (localhost)          │
│  • Arcade game                         │
│  • Agent dashboard                     │
└────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│        Production (Railway)            │
├────────────────────────────────────────┤
│ • Orchestrator (always running)        │
│ • Kev model server                     │
│ • Supabase Cloud                       │
│ • Blotato API integration              │
└────────────────────────────────────────┘
```

---

## Docker Compose (Local Dev)

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  # Kev decision model
  kev:
    image: python:3.11
    volumes:
      - ~/.cache/huggingface:/root/.cache
    command: python -m kev.serve --run jaredpalmer/kev-4b --port 8009
    ports:
      - "8009:8009"

  # Ollama (DeepSeek)
  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    ports:
      - "11434:11434"

  # Node.js Orchestrator
  orchestrator:
    build: ./backend
    environment:
      - NODE_ENV=development
      - KEV_BASE_URL=http://kev:8009
      - OLLAMA_BASE_URL=http://ollama:11434
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    ports:
      - "3000:3000"
    depends_on:
      - kev
      - ollama

  # Supabase (local)
  postgres:
    image: supabase/postgres:15
    environment:
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"

volumes:
  ollama_data:
```

**Run it:**
```bash
docker-compose up -d
npm run dev  # Start React Native app
```

---

## Day-in-the-Life Example

**09:00 SAST** — You wake up, open app

**Screen 1: Arcade Game**
- "Welcome, Tumelo! You're at the Trading Post"
- You: "I want to sell wheat"
- Kev decides outcome (confidence 92%)
- Naledi narrates: "The merchant offers R2,340/ton. Accept?"

**Meanwhile (Background)**
- 08:00: Naledi wrote 3 blog posts
- 08:15: Kev quality-gated them (2 published, 1 in review)
- 08:30: Blotato posted to 6 platforms (5K impressions)
- 09:00: EDDIE analyzed ad campaigns (ROAS up 12%)

**Screen 2: Agent Dashboard**
```
Live Agent Activity
Revenue: $24,532 (this month)

Naledi  | Content published  | 09:15
Kev     | 6 decisions routed  | 09:12
EDDIE   | Ad spend optimized  | 09:08
Charlie | Customer call       | 09:05
```

**You:** Keep playing game. Agents keep working.

---

## Ready to Deploy

Files to create:
1. Mobile app (React Native)
2. Backend orchestrator (Node.js)
3. Docker setup (local dev)
4. GitHub repo

**Where to save:**
- GitHub: Your repo
- Drive: Backup of code
- Local: Docker running

---

