import asyncio
import logging
import time

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero

# Constants
TIMEOUT_SECONDS = 30
PROMPT_WARNING_TIME = 10
GOODBYE_DELAY = 3

load_dotenv()
logger = logging.getLogger("voice-assistant")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # State variables
    last_interaction_time = time.time()
    still_there_prompt_sent = False
    is_agent_speaking = False
    is_user_speaking = False

    def reset_timeout():
        nonlocal still_there_prompt_sent, last_interaction_time
        still_there_prompt_sent = False
        last_interaction_time = time.time()

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: ${summary}")

    async def hangup():
        logger.info("Idle too long, hanging up")
        try:
            await ctx.room.disconnect()
        except Exception as e:
            logger.warning(f"Error while ending call: {e}")

    async def should_end_call():
        nonlocal still_there_prompt_sent
        idle_time = int(time.time() - last_interaction_time)
        if idle_time >= PROMPT_WARNING_TIME:
            logger.debug(f"Idle time: {idle_time} (Prompt sent: {still_there_prompt_sent}, Agent speaking: {is_agent_speaking}, User speaking: {is_user_speaking})")
        if is_agent_speaking or is_user_speaking:
            return False
        return idle_time > TIMEOUT_SECONDS

    async def send_agent_prompt():
        nonlocal still_there_prompt_sent
        if is_agent_speaking or is_user_speaking:
            return
        if time.time() - last_interaction_time >= PROMPT_WARNING_TIME and not still_there_prompt_sent:
            logger.info("Sending idle too long prompt")
            still_there_prompt_sent = True
            await agent.say("Are you still there?", allow_interruptions=True)

    async def monitor_interaction():
        while True:
            if (is_agent_speaking or is_user_speaking) and not still_there_prompt_sent:
                reset_timeout()
            if await should_end_call():
                logger.info("Ending call due to inactivity.")
                await agent.say("Goodbye!", allow_interruptions=False)
                await asyncio.sleep(GOODBYE_DELAY)
                await hangup()
                break
            await send_agent_prompt()
            await asyncio.sleep(1)  # Check every second

    # Initialize and start the agent
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
        ),
    )

    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    dg_model = "nova-2-general"
    if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        dg_model = "nova-2-phonecall"

    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(model=dg_model),
        llm=openai.LLM(),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
    )

    # Event handlers
    @agent.on("agent_started_speaking")
    def _on_agent_started_speaking():
        nonlocal is_agent_speaking
        is_agent_speaking = True
        logger.info("Agent started speaking")
        if not still_there_prompt_sent:
            reset_timeout()

    @agent.on("agent_stopped_speaking")
    def _on_agent_stopped_speaking():
        nonlocal is_agent_speaking
        is_agent_speaking = False
        logger.info("Agent stopped speaking")
        if not still_there_prompt_sent:
            reset_timeout()

    @agent.on("user_started_speaking")
    def _on_user_started_speaking():
        nonlocal is_user_speaking
        is_user_speaking = True
        logger.info("User started speaking")
        reset_timeout()

    @agent.on("user_stopped_speaking")
    def _on_user_stopped_speaking():
        nonlocal is_user_speaking
        is_user_speaking = False
        logger.info("User stopped speaking")
        reset_timeout()

    agent.start(ctx.room, participant)
    usage_collector = metrics.UsageCollector()
    ctx.add_shutdown_callback(log_usage)
    asyncio.create_task(monitor_interaction())
    chat = rtc.ChatManager(ctx.room)

    await agent.say("Hello, how can I help you today?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )