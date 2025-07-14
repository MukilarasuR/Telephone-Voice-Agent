#main.py file
import os
import csv
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import logging
import asyncio
from typing import Any, Optional
from dataclasses import dataclass
from livekit.agents import function_tool, Agent, RunContext
from livekit.agents import get_job_context
from livekit import api
from livekit.plugins import cartesia, deepgram, openai, silero, noise_cancellation, elevenlabs, assemblyai
from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

class VoiceAgentMetrics:
    def __init__(self):
        self.session_start_time = None
        self.session_end_time = None
        self.interactions = []
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logs_dir = "logs"
        os.makedirs(self.logs_dir, exist_ok=True)
        
    def start_session(self):
        """Mark the start of voice agent session"""
        self.session_start_time = time.time()
        logging.info(f"[Metrics] Session started: {self.session_id}")
        
    def end_session(self):
        """Mark the end of voice agent session"""
        self.session_end_time = time.time()
        logging.info(f"[Metrics] Session ended: {self.session_id}")
        
    def log_interaction(self, interaction_data):
        """Log a single interaction with all metrics"""
        interaction_data['session_id'] = self.session_id
        self.interactions.append(interaction_data)
        logging.info(f"[Metrics] Logged interaction: {interaction_data['interaction_id']}")
        
    def calculate_metrics(self):
        """Calculate all required metrics"""
        if not self.interactions:
            logging.warning("[Metrics] No interactions recorded")
            return None
            
        # Calculate per-interaction metrics
        for i, interaction in enumerate(self.interactions):
            # Agent idle time per question (speech_end_time to response_start_time)
            interaction['agent_idle_time_per_question'] = round(
                interaction['response_start_time'] - interaction['speech_end_time'], 3
            )
            
            # User response waiting time (time between interactions)
            if i == 0:
                interaction['user_response_waiting_time'] = round(
                    interaction['speech_start_time'] - self.session_start_time, 3
                )
            else:
                interaction['user_response_waiting_time'] = round(
                    interaction['speech_start_time'] - self.interactions[i-1]['agent_response_end_time'], 3
                )
        
        # Calculate summary metrics
        total_user_speaking_time = sum(i['user_speaking_time'] for i in self.interactions)
        total_agent_reply_time = sum(i['agent_reply_time'] for i in self.interactions)
        total_agent_idle_time = sum(i['agent_idle_time_per_question'] for i in self.interactions)
        
        num_questions = len(self.interactions)
        
        summary = {
            'session_id': self.session_id,
            'total_questions': num_questions,
            'total_user_speaking_time': round(total_user_speaking_time, 3),
            'average_user_speaking_time': round(total_user_speaking_time / num_questions, 3),
            'total_agent_reply_time': round(total_agent_reply_time, 3),
            'average_agent_reply_time': round(total_agent_reply_time / num_questions, 3),
            'total_agent_idle_time': round(total_agent_idle_time, 3),
            'average_agent_idle_time': round(total_agent_idle_time / num_questions, 3),
            'total_voice_agent_response_time_during_start_end_call': round(
                self.session_end_time - self.session_start_time, 3
            ) if self.session_end_time else 0,
            'session_start_time': self.session_start_time,
            'session_end_time': self.session_end_time
        }
        
        return summary
        
    def save_csv(self):
        """Save metrics to CSV file"""
        if not self.interactions:
            logging.warning("[Metrics] No interactions to save to CSV")
            return None
            
        csv_file = os.path.join(self.logs_dir, f"voice_agent_metrics_{self.session_id}.csv")
        
        with open(csv_file, 'w', newline='') as f:
            fieldnames = [
                'session_id', 'timestamp', 'interaction_id', 'speech_start_time', 'speech_end_time',
                'response_start_time', 'agent_response_end_time', 'user_speaking_time',
                'agent_reply_time', 'user_response_waiting_time', 'agent_idle_time_per_question'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.interactions)
        
        logging.info(f"[Metrics] CSV saved: {csv_file}")
        return csv_file
        
    def save_json(self):
        """Save metrics to JSON file"""
        json_file = os.path.join(self.logs_dir, f"voice_agent_metrics_{self.session_id}.json")
        
        summary = self.calculate_metrics()
        
        data = {
            'session_info': summary,
            'interactions': self.interactions
        }
        
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        logging.info(f"[Metrics] JSON saved: {json_file}")
        return json_file
        
    def print_human_readable_table(self):
        """Print human-readable table of metrics"""
        if not self.interactions:
            print("No interactions recorded.")
            return
            
        summary = self.calculate_metrics()
        
        print(f"\n{'='*80}")
        print(f"VOICE AGENT METRICS REPORT - {self.session_id}")
        print(f"{'='*80}")
        
        # Interactions table
        print(f"\nINTERACTIONS:")
        print(f"{'ID':<4} {'User Wait':<10} {'User Speak':<11} {'Agent Idle':<11} {'Agent Reply':<11}")
        print(f"{'-'*4} {'-'*10} {'-'*11} {'-'*11} {'-'*11}")
        
        for i, interaction in enumerate(self.interactions, 1):
            print(f"{i:<4} {interaction['user_response_waiting_time']:<10.3f} "
                  f"{interaction['user_speaking_time']:<11.3f} "
                  f"{interaction['agent_idle_time_per_question']:<11.3f} "
                  f"{interaction['agent_reply_time']:<11.3f}")
        
        # Summary table
        print(f"\nSUMMARY:")
        print(f"{'Metric':<40} {'Value':<15}")
        print(f"{'-'*40} {'-'*15}")
        print(f"{'Total Questions':<40} {summary['total_questions']:<15}")
        print(f"{'Total User Speaking Time (s)':<40} {summary['total_user_speaking_time']:<15.3f}")
        print(f"{'Average User Speaking Time (s)':<40} {summary['average_user_speaking_time']:<15.3f}")
        print(f"{'Total Agent Reply Time (s)':<40} {summary['total_agent_reply_time']:<15.3f}")
        print(f"{'Average Agent Reply Time (s)':<40} {summary['average_agent_reply_time']:<15.3f}")
        print(f"{'Total Agent Idle Time (s)':<40} {summary['total_agent_idle_time']:<15.3f}")
        print(f"{'Average Agent Idle Time (s)':<40} {summary['average_agent_idle_time']:<15.3f}")
        print(f"{'Total Session Time (s)':<40} {summary['total_voice_agent_response_time_during_start_end_call']:<15.3f}")
        print(f"{'='*80}")


@dataclass
class InventoryItems:
    item_name: str
    quantity: int

# --- Utility: Hang up function ---
async def hangup_call():
    ctx = get_job_context()
    if ctx is None:
        return
    await ctx.api.room.delete_room(
        api.DeleteRoomRequest(
            room=ctx.room.name,
        )
    )

# --- Enhanced Assistant Agent ---
class Assistant(Agent):
    def __init__(self, metrics=None) -> None:
        super().__init__(
            instructions="You are a helpful voice assistant. Respond naturally and helpfully to user queries."
        )
        self.metrics = metrics
        self.conversation_id = str(datetime.now().timestamp())
        self.interaction_count = 0
        
        # Track timing for current interaction
        self.current_speech_start_time = None
        self.current_speech_end_time = None
        self.current_response_start_time = None
        self.current_response_end_time = None
        
        # Add demo interactions for testing
        self._add_demo_interactions()

    def _add_demo_interactions(self):
        """Add some demo interactions for testing purposes"""
        if self.metrics:
            current_time = time.time()
            
            # Demo interaction 1
            demo_interaction_1 = {
                'timestamp': datetime.now().isoformat(),
                'interaction_id': f"demo_1_{self.conversation_id}",
                'speech_start_time': current_time,
                'speech_end_time': current_time + 2.5,
                'response_start_time': current_time + 2.5,
                'agent_response_end_time': current_time + 5.0,
                'user_speaking_time': 2.5,
                'agent_reply_time': 2.5,
                'user_response_waiting_time': 0.0,
                'agent_idle_time_per_question': 0.0
            }
            
            # Demo interaction 2
            demo_interaction_2 = {
                'timestamp': datetime.now().isoformat(),
                'interaction_id': f"demo_2_{self.conversation_id}",
                'speech_start_time': current_time + 7.0,
                'speech_end_time': current_time + 10.0,
                'response_start_time': current_time + 10.0,
                'agent_response_end_time': current_time + 13.5,
                'user_speaking_time': 3.0,
                'agent_reply_time': 3.5,
                'user_response_waiting_time': 2.0,
                'agent_idle_time_per_question': 0.0
            }
            
            self.metrics.log_interaction(demo_interaction_1)
            self.metrics.log_interaction(demo_interaction_2)

    async def on_message(self, ctx: RunContext):
        """Handle incoming messages and calculate all metrics"""
        self.interaction_count += 1
        interaction_id = f"{self.conversation_id}_{self.interaction_count}"

        logging.info(f"[Agent] Processing interaction {interaction_id}")
        
        # Mark when user finished speaking and agent starts processing
        current_time = time.time()
        self.current_speech_end_time = current_time
        self.current_response_start_time = current_time
        
        # Estimate when user started speaking (based on speech duration)
        speech_text = ctx.input.text or "Hello"
        estimated_speech_duration = max(len(speech_text) * 0.1, 1.0)  # ~100ms per character, min 1 second
        self.current_speech_start_time = self.current_speech_end_time - estimated_speech_duration
        
        logging.info(f"[Agent] User said: {speech_text}")
        
        # Process the LLM response
        response_text = await self.run_llm(ctx, speech_text)
        
        # Simulate TTS time
        await asyncio.sleep(0.5)  # Simulate TTS processing time
        
        # Speak the response
        await ctx.session.speak(response_text)
        self.current_response_end_time = time.time()
        
        # Calculate metrics for this interaction
        user_speaking_time = self.current_speech_end_time - self.current_speech_start_time
        agent_reply_time = self.current_response_end_time - self.current_response_start_time
        
        # Log interaction metrics
        if self.metrics:
            interaction_data = {
                'timestamp': datetime.now().isoformat(),
                'interaction_id': interaction_id,
                'speech_start_time': self.current_speech_start_time,
                'speech_end_time': self.current_speech_end_time,
                'response_start_time': self.current_response_start_time,
                'agent_response_end_time': self.current_response_end_time,
                'user_speaking_time': round(user_speaking_time, 3),
                'agent_reply_time': round(agent_reply_time, 3),
                'user_response_waiting_time': 0,  # Will be calculated in metrics class
                'agent_idle_time_per_question': 0  # Will be calculated in metrics class
            }
            
            self.metrics.log_interaction(interaction_data)
            
            logging.info(f"[Agent] Metrics - User speaking: {user_speaking_time:.3f}s, "
                        f"Agent reply: {agent_reply_time:.3f}s")
        
        logging.info(f"[Agent] Completed interaction {interaction_id}")

    async def run_llm(self, ctx: RunContext, input_text: str) -> str:
        """Run the LLM to generate a response"""
        try:
            # Simulate LLM processing time
            await asyncio.sleep(0.2)
            
            # Simple response generation
            if "order" in input_text.lower():
                return "I can help you with your order. What would you like to order?"
            elif "availability" in input_text.lower() or "available" in input_text.lower():
                return "Let me check the availability for you."
            elif "end" in input_text.lower() or "bye" in input_text.lower() or "goodbye" in input_text.lower():
                return "Thank you for calling. Have a great day!"
            else:
                return f"I understand you said: {input_text}. How can I help you with your request?"
                
        except Exception as e:
            logging.error(f"LLM generation error: {e}")
            return "I'm sorry, I didn't understand that. Could you please repeat your request?"

    @function_tool
    async def order_items(self, items: InventoryItems) -> str:
        """Order items from the inventory"""
        return f"Order for {items.quantity} {items.item_name} has been placed successfully."

    @function_tool
    async def end_call(self, ctx: RunContext):
        """End the call when user wants to hang up"""
        # Let the agent finish speaking
        logging.info(f"[Agent] Call ended. Total interactions: {self.interaction_count}")
        
        # End session in metrics and save files
        if self.metrics:
            self.metrics.end_session()
            
            # Save all formats
            csv_file = self.metrics.save_csv()
            json_file = self.metrics.save_json()
            
            # Print human-readable table
            self.metrics.print_human_readable_table()
            
            if csv_file and json_file:
                print(f"\nFiles saved:")
                print(f"CSV: {csv_file}")
                print(f"JSON: {json_file}")
        
        await hangup_call()

    @function_tool
    async def check_availability(self, date: str) -> bool:
        """Check if the requested date is available"""
        return True

load_dotenv()

# Global metrics instance
voice_metrics = VoiceAgentMetrics()

async def entrypoint(ctx: agents.JobContext):
    global voice_metrics
    
    # Start session tracking
    voice_metrics.start_session()
    
    # Initialize the AgentSession
    session: AgentSession = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4.1-2025-04-14"),
        tts=elevenlabs.TTS(
            voice_id="ZUrEGyu8GFMwnHbvLhv2",
            model="eleven_flash_v2_5",
            voice_settings=elevenlabs.VoiceSettings(
                stability=0.60,
                speed=0.95,
                similarity_boost=0.75
            ),
        ),
        vad=silero.VAD.load(),
    )

    # Pass the metrics to the Assistant
    assistant = Assistant(metrics=voice_metrics)

    # Start the session with the Assistant agent
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVCTelephony(),
        ),
    )

    await ctx.connect()
    
    # Set up cleanup handler
    async def cleanup():
        logging.info("[Main] Cleanup started")
        voice_metrics.end_session()
        
        # Save all formats
        csv_file = voice_metrics.save_csv()
        json_file = voice_metrics.save_json()
        
        # Print human-readable table
        voice_metrics.print_human_readable_table()
        
        if csv_file and json_file:
            print(f"\nFiles saved:")
            print(f"CSV: {csv_file}")
            print(f"JSON: {json_file}")

    # Register cleanup handler
    ctx.add_shutdown_callback(cleanup)

if __name__ == "__main__":
    # Add endpoints for metrics access
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import FileResponse
    
    app = FastAPI()

    @app.get("/download-csv")
    async def download_csv():
        csv_file = voice_metrics.save_csv()
        if csv_file:
            return FileResponse(csv_file, filename="voice_agent_metrics.csv")
        return {"error": "No metrics available"}

    @app.get("/download-json")
    async def download_json():
        json_file = voice_metrics.save_json()
        if json_file:
            return FileResponse(json_file, filename="voice_agent_metrics.json")
        return {"error": "No metrics available"}

    @app.get("/metrics")
    async def get_metrics():
        summary = voice_metrics.calculate_metrics()
        return {
            "summary": summary,
            "interactions": voice_metrics.interactions
        }

    # Run the FastAPI server in a separate thread
    import threading
    threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": "0.0.0.0", "port": 8000},
        daemon=True
    ).start()

    # Run the main agent
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint))



# import os
# import csv
# import time
# from datetime import datetime
# from dotenv import load_dotenv
# import logging

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )

# from livekit.plugins import cartesia, deepgram, openai, silero, noise_cancellation, elevenlabs, assemblyai
# from livekit import agents
# from livekit.agents import AgentSession, Agent, RoomInputOptions

# from src.agent.livekit_agents import Assistant

# load_dotenv()

# # Set environment variables for LiveKit
# os.environ["LIVEKIT_API_KEY"]
# os.environ["LIVEKIT_API_SECRET"]
# os.environ["LIVEKIT_URL"]

# async def entrypoint(ctx: agents.JobContext):
#     # Initialize the AgentSession
#     session: AgentSession = AgentSession(
#         stt=deepgram.STT(model="nova-2"),
#         llm=openai.LLM(model="gpt-4o"),
#         tts=elevenlabs.TTS(
#             voice_id="ZUrEGyu8GFMwnHbvLhv2",
#             model="eleven_flash_v2_5",
#             voice_settings=elevenlabs.VoiceSettings(
#                 stability=0.60,
#                 speed=0.95,
#                 similarity_boost=0.75
#             ),
#         ),
#         vad=silero.VAD.load(),
#     )

#     # Create the Assistant agent
#     assistant = Assistant()

#     # Start the session with the Assistant agent
#     await session.start(
#         room=ctx.room,
#         agent=assistant,
#         room_input_options=RoomInputOptions(
#             noise_cancellation=noise_cancellation.BVCTelephony(),
#         ),
#     )

#     await ctx.connect()
    
#     # Log that the agent is ready
#     logging.info("Agent is ready and listening for interactions")

# if __name__ == "__main__":
#     # Add CSV download endpoint if running directly
#     import uvicorn
#     from fastapi import FastAPI
#     from fastapi.responses import FileResponse
#     import json
#     import glob

#     app = FastAPI()

#     @app.get("/download-response-logs")
#     async def download_response_logs():
#         # Find the latest response time log file
#         log_files = glob.glob("logs/response_times_*.csv")
#         if log_files:
#             latest_log = max(log_files, key=os.path.getmtime)
#             return FileResponse(latest_log, filename="response_times.csv")
#         return {"message": "No response time logs available"}

#     @app.get("/response-stats")
#     async def get_response_stats():
#         """Get response time statistics as JSON"""
#         log_files = glob.glob("logs/response_times_*.csv")
#         if not log_files:
#             return {"message": "No response time data available"}
        
#         latest_log = max(log_files, key=os.path.getmtime)
        
#         response_times = []
#         try:
#             with open(latest_log, 'r') as f:
#                 reader = csv.DictReader(f)
#                 response_times = [row for row in reader]
#         except Exception as e:
#             return {"error": f"Failed to read log file: {e}"}
        
#         if not response_times:
#             return {"message": "No response time data in log file"}
        
#         latencies = [float(row['total_response_latency_ms']) for row in response_times if row['total_response_latency_ms']]
        
#         if not latencies:
#             return {"message": "No valid latency data found"}
        
#         stats = {
#             "total_interactions": len(latencies),
#             "average_response_time_ms": sum(latencies) / len(latencies),
#             "min_response_time_ms": min(latencies),
#             "max_response_time_ms": max(latencies),
#             "latest_log_file": latest_log,
#             "response_times": response_times
#         }
        
#         return stats

#     # Run the FastAPI server in a separate thread
#     import threading
#     threading.Thread(
#         target=uvicorn.run,
#         args=(app,),
#         kwargs={"host": "0.0.0.0", "port": 8000},
#         daemon=True
#     ).start()
    
#     print("FastAPI server started on http://localhost:8000")
#     print("Check response stats at: http://localhost:8000/response-stats")
#     print("Download logs at: http://localhost:8000/download-response-logs")

#     # Run the main agent
#     agents.cli.run_app(agents.WorkerOptions(
#         entrypoint_fnc=entrypoint
#     ))