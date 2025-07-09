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


class CSVLogger:
    def __init__(self):
        self.logs = []
        self.log_file = os.path.join("logs", f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        os.makedirs("logs", exist_ok=True)
        
    def log_component(self, component: str, duration: float):
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "duration_seconds": round(duration, 3)
        })
        
    def save(self):
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "component", "duration_seconds"])
            writer.writeheader()
            writer.writerows(self.logs)
        return self.log_file


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
    logger = CSVLogger()
    start_time = time.time()

    # Initialize the AgentSession
    session: AgentSession = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4.1-2025-04-14"),
        tts=elevenlabs.TTS(
            voice_id="ZUrEGyu8GFMwnHbvLhv2", # 248be419-c632-4f23-adf1-5324ed7dbf1d (cartesia voice)
            model="eleven_flash_v2_5",
            voice_settings=elevenlabs.VoiceSettings(
                stability=0.60,
                speed=0.95,
                similarity_boost=0.75
            ),

        ),
        vad=silero.VAD.load(),
    )

    # Start the session with the Assistant agent
    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVCTelephony(),
        ),
    )



    await ctx.connect()
    
    # Time ASR processing
    asr_start = time.time()
    # ASR processing would happen here
    asr_duration = time.time() - asr_start
    
    # Time LLM processing
    llm_start = time.time()
    await session.generate_reply()
    llm_duration = time.time() - llm_start
    
    # Time TTS processing
    tts_start = time.time()
    # TTS processing would happen here
    tts_duration = time.time() - tts_start
    
    # Log all components
    logger.log_component("ASR", asr_duration)
    logger.log_component("LLM", llm_duration)
    logger.log_component("TTS", tts_duration)
    logger.log_component("TOTAL", asr_duration + llm_duration + tts_duration)
    
    logger.save()
    print(f"Logs saved to: {logger.log_file}")

if __name__ == "__main__":
    # Add CSV download endpoint if running directly
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import FileResponse

    app = FastAPI()

    @app.get("/download-logs")
    async def download_logs():
        latest_log = max(
            (os.path.join("logs", f) for f in os.listdir("logs") if f.endswith(".csv")),
            key=os.path.getmtime,
            default=None
        )
        if latest_log:
            return FileResponse(latest_log, filename="logs.csv")
        return {"message": "No logs available"}

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
        entrypoint_fnc=entrypoint
        ))
