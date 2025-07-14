import os
import csv
import time
from datetime import datetime
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from livekit.plugins import cartesia, deepgram, openai, silero, noise_cancellation, elevenlabs, assemblyai
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions

from src.agent.livekit_agents import Assistant

load_dotenv()

# Set environment variables for LiveKit
os.environ["LIVEKIT_API_KEY"]
os.environ["LIVEKIT_API_SECRET"]
os.environ["LIVEKIT_URL"]

async def entrypoint(ctx: agents.JobContext):
    # Initialize the AgentSession
    session: AgentSession = AgentSession(
        stt=deepgram.STT(model="nova-2"),
        llm=openai.LLM(model="gpt-4o"),
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

    # Create the Assistant agent
    assistant = Assistant()

    # Start the session with the Assistant agent
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVCTelephony(),
        ),
    )

    await ctx.connect()
    
    # Log that the agent is ready
    logging.info("Agent is ready and listening for interactions")

if __name__ == "__main__":
    # Add CSV download endpoint if running directly
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import FileResponse
    import json
    import glob

    app = FastAPI()

    @app.get("/download-response-logs")
    async def download_response_logs():
        # Find the latest response time log file
        log_files = glob.glob("logs/response_times_*.csv")
        if log_files:
            latest_log = max(log_files, key=os.path.getmtime)
            return FileResponse(latest_log, filename="response_times.csv")
        return {"message": "No response time logs available"}

    @app.get("/response-stats")
    async def get_response_stats():
        """Get response time statistics as JSON"""
        log_files = glob.glob("logs/response_times_*.csv")
        if not log_files:
            return {"message": "No response time data available"}
        
        latest_log = max(log_files, key=os.path.getmtime)
        
        response_times = []
        try:
            with open(latest_log, 'r') as f:
                reader = csv.DictReader(f)
                response_times = [row for row in reader]
        except Exception as e:
            return {"error": f"Failed to read log file: {e}"}
        
        if not response_times:
            return {"message": "No response time data in log file"}
        
        latencies = [float(row['total_response_latency_ms']) for row in response_times if row['total_response_latency_ms']]
        
        if not latencies:
            return {"message": "No valid latency data found"}
        
        stats = {
            "total_interactions": len(latencies),
            "average_response_time_ms": sum(latencies) / len(latencies),
            "min_response_time_ms": min(latencies),
            "max_response_time_ms": max(latencies),
            "latest_log_file": latest_log,
            "response_times": response_times
        }
        
        return stats

    # Run the FastAPI server in a separate thread
    import threading
    threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": "0.0.0.0", "port": 8000},
        daemon=True
    ).start()
    
    print("FastAPI server started on http://localhost:8000")
    print("Check response stats at: http://localhost:8000/response-stats")
    print("Download logs at: http://localhost:8000/download-response-logs")

    # Run the main agent
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint
    ))