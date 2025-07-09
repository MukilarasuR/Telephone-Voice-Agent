import time
import logging
import csv
import datetime
from typing import Any
from dataclasses import dataclass
from livekit.agents import function_tool, Agent, RunContext
from livekit.agents import get_job_context
from src.prompts.system_prompt import *

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

# --- Timing & Logging Utilities ---
def log_duration(label: str, start: float, end: float):
    duration = end - start
    logging.info(f"[Timing] {label}: {duration:.2f}s")
    save_metrics_to_csv(label, duration)
    return duration

def save_metrics_to_csv(label: str, value: float):
    with open("metrics_log.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.now().isoformat(), label, f"{value:.2f}"])

# --- Main Assistant Agent ---
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=EMPLOYEE_LOOKUP_PROMPT
        )

    async def on_message(self, ctx: RunContext):
        logging.info("[Agent] Starting interaction timing log")

        total_start = time.time()

        # Simulated ASR step (input already converted to text)
        asr_start = time.time()
        input_text = ctx.input.text
        asr_end = time.time()
        log_duration("ASR", asr_start, asr_end)

        # LLM step
        llm_start = time.time()
        response_text = await self.run_llm(ctx, input_text)
        llm_end = time.time()
        log_duration("LLM", llm_start, llm_end)

        # TTS step (speak)
        tts_start = time.time()
        await ctx.session.speak(response_text)
        tts_end = time.time()
        log_duration("TTS", tts_start, tts_end)

        total_end = time.time()
        log_duration("TOTAL", total_start, total_end)

    async def run_llm(self, ctx: RunContext, input_text: str) -> str:
        return await ctx.session.llm.respond(input_text)

    @function_tool
    async def order_items(self, items: InventoryItems) -> str:
        return f"Order for {items.quantity} {items.item_name} has been placed successfully."

    @function_tool
    async def end_call(self, ctx: RunContext):
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()
        await hangup_call()

    @function_tool
    async def check_availability(self, date: str) -> bool:
        return True



# from livekit.agents import Agent
# from src.prompts.system_prompt import *
# from livekit.agents import function_tool, Agent, RunContext
# from typing import Any, Dict
# from dataclasses import dataclass, field
# from livekit import api, rtc
# from livekit.agents import get_job_context

# @dataclass
# class InventoryItems:
#     item_name: str
#     quantity: int


# async def hangup_call():
#     ctx = get_job_context()
#     if ctx is None:
#         # Not running in a job context
#         return
    
#     await ctx.api.room.delete_room(
#         api.DeleteRoomRequest(
#             room=ctx.room.name,
#         )
#     )
# class Assistant(Agent):
#     def __init__(self) -> None:
#         super().__init__(
#             instructions=EMPLOYEE_LOOKUP_PROMPT
#         )

#     @function_tool
#     async def order_items(self, items: InventoryItems) -> str:
#         """
#         Order items from the inventory.
        
#         Args:
#             items (InventoryItems): The items to order with their quantities.
        
#         Returns:
#             str: Confirmation message of the order.
#         """
#         return f"Order for {items.quantity} {items.item_name} has been placed successfully."


#     @function_tool
#     async def end_call(self, ctx: RunContext):
#         """when the user wants to end the call or the user is not interested in proceeding or the conversation is over"""
#         # let the agent finish speaking
#         current_speech = ctx.session.current_speech
#         if current_speech:
#             await current_speech.wait_for_playout()

#         await hangup_call()

#     @function_tool
#     async def check_availability(self, date: str) -> bool:
#         """
#         Check if the requested date is available for leave.
        
#         Args:
#             date (str): The date to check availability for.
        
#         Returns:
#             bool: True if available, False otherwise.
#         """
#         # Simulate checking availability
#         # In a real scenario, this would query a database or an API
#         return True
