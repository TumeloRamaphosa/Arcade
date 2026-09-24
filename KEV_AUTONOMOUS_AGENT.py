"""
Kev Autonomous Talking Agent
Kev is now a decision-making agent with voice, memory, and autonomous action
"""

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
from twilio.rest import Client as TwilioClient
from elevenlabs import ElevenLabsClient
import json
from datetime import datetime
from supabase import create_client, Client as SupabaseClient
import anthropic

class KevAgent:
    """
    Kev: Autonomous decision-making agent with voice interface

    Capabilities:
    - Listens (voice via Twilio)
    - Decides (Kev decision model)
    - Acts (executes decisions autonomously)
    - Speaks (voice output via ElevenLabs)
    - Remembers (Supabase state persistence)
    - Learns (feedback loop)
    """

    def __init__(self):
        # Kev decision model (local)
        self.kev_client = TypeSafeClient(
            api_key="local",
            base_url="http://127.0.0.1:8009",
            model="kev-4b"
        )

        # Voice I/O
        self.twilio = TwilioClient(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.elevenlabs = ElevenLabsClient(
            api_key=os.getenv("ELEVENLABS_API_KEY")
        )

        # State persistence
        self.supabase: SupabaseClient = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )

        # Claude for narrative/context (fallback reasoning)
        self.anthropic = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        # Agent identity
        self.name = "Kev"
        self.role = "Decision Agent"
        self.personality = "Direct, analytical, confidence-driven"

    # ============================================================
    # VOICE INPUT
    # ============================================================

    def listen(self, call_sid: str) -> str:
        """
        Listen to incoming voice call, transcribe to text
        Triggered by Twilio webhook
        """

        # Get call recording from Twilio
        recording_url = self.twilio.calls(call_sid).fetch().recording_url

        # Transcribe via Whisper (or use Twilio built-in)
        transcription = self.twilio.transcriptions.create(
            recording_url=recording_url
        )

        return transcription.transcription_text

    # ============================================================
    # DECISION MAKING (CORE)
    # ============================================================

    def decide(self, input_text: str, context: dict = None) -> dict:
        """
        Make a decision using Kev model

        Input: User's request/state
        Output: Structured decision with confidence
        """

        # Build context from memory if available
        if context is None:
            context = self.load_agent_memory()

        # Ask Kev to decide
        response = self.kev_client.system_one(
            state=f"""
            User: {input_text}
            Context: {context}
            Agent Role: {self.role}
            Personality: {self.personality}
            """,
            questions={
                # What should Kev do?
                "action_type": {
                    "type": "choice",
                    "instructions": "What should Kev do?",
                    "criteria": {
                        "inform": "Provide information",
                        "decide": "Make a decision",
                        "execute": "Take autonomous action",
                        "escalate": "Hand off to human",
                        "learn": "Update memory based on feedback"
                    }
                },
                # How confident?
                "confidence": {
                    "type": "score",
                    "instructions": "Confidence in this decision",
                    "criteria": ["Low (0-3)", "Medium (3-6)", "High (6-10)"]
                },
                # Should Kev act alone?
                "autonomous": {
                    "type": "noul",
                    "instructions": "Can Kev execute autonomously?"
                },
                # Risk level
                "risk": {
                    "type": "score",
                    "instructions": "Risk of this decision",
                    "criteria": ["Safe", "Moderate", "High"]
                }
            }
        )

        decision = {
            "action": response.answers["action_type"]["choice"],
            "confidence": response.answers["confidence"]["score"],
            "confidence_level": response.answers["confidence"]["confidence"],
            "can_act_alone": response.answers["autonomous"]["noul"] > 0.6,
            "risk": response.answers["risk"]["score"],
            "input": input_text,
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.name,
            "full_response": response
        }

        # Store decision in memory
        self.save_decision(decision)

        return decision

    # ============================================================
    # AUTONOMOUS ACTION
    # ============================================================

    def act(self, decision: dict) -> dict:
        """
        Execute the decision autonomously

        Examples:
        - Publish content to Blotato
        - Update game state in Supabase
        - Send message to customer
        - Create task/reminder
        """

        action_type = decision["action"]
        input_text = decision["input"]
        confidence = decision["confidence_level"]

        # Only act if confidence > 70%
        if confidence < 0.7 and not decision["can_act_alone"]:
            return {
                "status": "awaiting_approval",
                "reason": f"Low confidence ({confidence:.0%}), needs human approval"
            }

        # ---- ACTION: INFORM ----
        if action_type == "inform":
            response = self._action_inform(input_text)

        # ---- ACTION: DECIDE ----
        elif action_type == "decide":
            response = self._action_decide(input_text, decision)

        # ---- ACTION: EXECUTE ----
        elif action_type == "execute":
            response = self._action_execute(input_text, decision)

        # ---- ACTION: ESCALATE ----
        elif action_type == "escalate":
            response = self._action_escalate(input_text, decision)

        # ---- ACTION: LEARN ----
        elif action_type == "learn":
            response = self._action_learn(input_text, decision)

        else:
            response = {"status": "unknown_action"}

        # Log the action
        self.log_action(decision, response)

        return response

    def _action_inform(self, query: str) -> dict:
        """Action: Provide information"""
        answer = self.anthropic.messages.create(
            model="claude-opus-5",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": f"Answer briefly and accurately: {query}"}
            ]
        ).content[0].text

        return {
            "status": "informed",
            "answer": answer
        }

    def _action_decide(self, request: str, decision: dict) -> dict:
        """Action: Make a structured decision"""
        # Re-ask Kev with more depth
        detailed_decision = self.kev_client.system_one(
            state=request,
            questions={
                "best_option": {
                    "type": "choice",
                    "instructions": "What's the best choice?",
                    "criteria": {
                        "option_a": "First option",
                        "option_b": "Second option",
                        "option_c": "Third option"
                    }
                },
                "why": {
                    "type": "noul",
                    "instructions": "Should we explain the reasoning?"
                }
            }
        )

        return {
            "status": "decided",
            "recommendation": detailed_decision.answers["best_option"]["choice"],
            "probabilities": detailed_decision.answers["best_option"]["probabilities"],
            "reasoning": "Option has highest probability based on current state"
        }

    def _action_execute(self, command: str, decision: dict) -> dict:
        """Action: Execute autonomously"""

        # Example: Publish content
        if "publish" in command.lower():
            return self._execute_publish(command)

        # Example: Update game state
        elif "game" in command.lower():
            return self._execute_game_action(command)

        # Example: Send message
        elif "message" in command.lower():
            return self._execute_send_message(command)

        else:
            return {"status": "execution_not_implemented"}

    def _execute_publish(self, command: str) -> dict:
        """Execute: Publish content to platforms"""
        # Hook into Blotato
        result = self.supabase.table("kev_actions").insert({
            "type": "publish",
            "command": command,
            "status": "queued",
            "timestamp": datetime.now().isoformat()
        }).execute()

        return {
            "status": "published",
            "action_id": result.data[0]["id"],
            "platforms": ["twitter", "linkedin", "instagram"]
        }

    def _execute_game_action(self, command: str) -> dict:
        """Execute: Update game state"""
        result = self.supabase.table("kev_actions").insert({
            "type": "game",
            "command": command,
            "status": "executed",
            "timestamp": datetime.now().isoformat()
        }).execute()

        return {
            "status": "game_state_updated",
            "action_id": result.data[0]["id"]
        }

    def _execute_send_message(self, command: str) -> dict:
        """Execute: Send message to user"""
        # Would integrate with Twilio SMS or WhatsApp
        return {
            "status": "message_sent",
            "recipient": "user"
        }

    def _action_escalate(self, issue: str, decision: dict) -> dict:
        """Action: Escalate to human"""
        # Send to Tumelo
        self.supabase.table("escalations").insert({
            "issue": issue,
            "from_agent": self.name,
            "confidence": decision["confidence_level"],
            "timestamp": datetime.now().isoformat(),
            "status": "pending_review"
        }).execute()

        return {
            "status": "escalated",
            "recipient": "tumelo@studex.dev",
            "reason": f"Low confidence ({decision['confidence_level']:.0%})"
        }

    def _action_learn(self, feedback: str, decision: dict) -> dict:
        """Action: Update memory based on feedback"""
        self.supabase.table("kev_learning").insert({
            "feedback": feedback,
            "decision_id": decision.get("id"),
            "timestamp": datetime.now().isoformat()
        }).execute()

        return {
            "status": "learned",
            "update": "Memory updated with new feedback"
        }

    # ============================================================
    # VOICE OUTPUT
    # ============================================================

    def speak(self, text: str, voice_id: str = "kev") -> str:
        """
        Synthesize text to speech, return audio URL
        """
        audio = self.elevenlabs.text_to_speech(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2"
        )

        # Upload to Supabase storage
        filename = f"kev_audio_{datetime.now().timestamp()}.mp3"
        self.supabase.storage.from_("kev-voice").upload(
            filename,
            audio.content
        )

        url = self.supabase.storage.from_("kev-voice").get_public_url(filename)

        return url

    def respond(self, decision: dict, action_result: dict) -> str:
        """
        Generate natural language response based on decision + action
        """

        prompt = f"""
        You are Kev, an autonomous decision agent.

        Decision: {decision['action']}
        Confidence: {decision['confidence_level']:.0%}
        Action Result: {action_result['status']}

        Generate a brief, confident response (1-2 sentences):
        """

        response = self.anthropic.messages.create(
            model="claude-opus-5",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        ).content[0].text

        return response

    # ============================================================
    # MEMORY & STATE
    # ============================================================

    def load_agent_memory(self) -> dict:
        """Load agent's memory from Supabase"""
        try:
            memory = self.supabase.table("kev_memory").select("*").execute()
            return memory.data[-1] if memory.data else {}
        except:
            return {}

    def save_decision(self, decision: dict):
        """Save decision to memory"""
        self.supabase.table("kev_decisions").insert(decision).execute()

    def log_action(self, decision: dict, result: dict):
        """Log action execution"""
        self.supabase.table("kev_actions").insert({
            "decision_id": decision.get("id"),
            "action": decision["action"],
            "result": result["status"],
            "timestamp": datetime.now().isoformat()
        }).execute()

    # ============================================================
    # FULL CONVERSATION LOOP
    # ============================================================

    def handle_voice_call(self, call_sid: str):
        """
        Full voice conversation with Kev

        Flow:
        1. Listen (transcribe voice)
        2. Decide (Kev model)
        3. Act (execute decision)
        4. Respond (speak result)
        5. Hang up
        """

        print(f"[Kev] Incoming call: {call_sid}")

        # 1. LISTEN
        user_input = self.listen(call_sid)
        print(f"[Kev] Heard: {user_input}")

        # 2. DECIDE
        decision = self.decide(user_input)
        print(f"[Kev] Decided: {decision['action']} ({decision['confidence_level']:.0%} confidence)")

        # 3. ACT
        action_result = self.act(decision)
        print(f"[Kev] Result: {action_result['status']}")

        # 4. RESPOND
        response_text = self.respond(decision, action_result)
        audio_url = self.speak(response_text)
        print(f"[Kev] Speaking: {response_text}")

        # Play audio back to caller
        self.twilio.calls(call_sid).update(twiml=f"""
        <Response>
            <Play>{audio_url}</Play>
            <Hangup/>
        </Response>
        """)

        return {
            "heard": user_input,
            "decision": decision['action'],
            "action": action_result['status'],
            "said": response_text
        }


# ============================================================
# DEPLOYMENT: Twilio Webhook
# ============================================================

from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)
kev = KevAgent()

@app.route("/kev/call", methods=["POST"])
def handle_incoming_call():
    """
    Twilio webhook for incoming calls
    """
    call_sid = request.form.get("CallSid")
    result = kev.handle_voice_call(call_sid)

    # Return TwiML to hang up
    response = VoiceResponse()
    response.say("Thanks for calling Kev. Goodbye.")
    response.hangup()

    return str(response)

@app.route("/kev/sms", methods=["POST"])
def handle_sms():
    """
    Alternative: SMS interface to Kev
    """
    from_number = request.form.get("From")
    message = request.form.get("Body")

    # Run through decision loop
    decision = kev.decide(message)
    action_result = kev.act(decision)
    response_text = kev.respond(decision, action_result)

    # Send SMS back
    kev.twilio.messages.create(
        body=response_text,
        from_="+27101234567",
        to=from_number
    )

    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
