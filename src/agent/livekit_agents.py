#Livekit_agents.py file

import time
import logging
import datetime
from typing import Any, Optional
from dataclasses import dataclass
from livekit.agents import function_tool, Agent, RunContext
from livekit.agents import get_job_context
from livekit import api
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

# --- Main Assistant Agent ---
class Assistant(Agent):
    def __init__(self, metrics=None) -> None:
        super().__init__(
            instructions=EMPLOYEE_LOOKUP_PROMPT
        )
        self.metrics = metrics
        self.conversation_id = str(datetime.datetime.now().timestamp())
        self.interaction_count = 0
        
        # Track timing for current interaction
        self.current_speech_start_time = None
        self.current_speech_end_time = None
        self.current_response_start_time = None
        self.current_response_end_time = None

    async def on_message(self, ctx: RunContext):
        """Handle incoming messages and calculate all metrics"""
        self.interaction_count += 1
        interaction_id = f"{self.conversation_id}_{self.interaction_count}"

        logging.info(f"[Agent] Processing interaction {interaction_id}")
        
        # Mark when user finished speaking and agent starts processing
        self.current_speech_end_time = time.time()
        self.current_response_start_time = time.time()
        
        # Estimate when user started speaking (based on speech duration)
        # This is an approximation - in real implementation, you'd track VAD events
        speech_text = ctx.input.text
        estimated_speech_duration = len(speech_text) * 0.05  # ~50ms per character
        self.current_speech_start_time = self.current_speech_end_time - estimated_speech_duration
        
        logging.info(f"[Agent] User said: {speech_text}")
        
        # Process the LLM response
        response_start = time.time()
        response_text = await self.run_llm(ctx, speech_text)
        
        # Speak the response
        tts_start = time.time()
        await ctx.session.speak(response_text)
        self.current_response_end_time = time.time()
        
        # Calculate metrics for this interaction
        user_speaking_time = self.current_speech_end_time - self.current_speech_start_time
        agent_reply_time = self.current_response_end_time - self.current_response_start_time
        
        # Log interaction metrics
        if self.metrics:
            interaction_data = {
                'timestamp': datetime.datetime.now().isoformat(),
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
            # Simple response generation - replace with your actual LLM logic
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
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()
        
        # Log final information
        logging.info(f"[Agent] Call ended. Total interactions: {self.interaction_count}")
        
        # End session in metrics
        if self.metrics:
            self.metrics.end_session()
        
        await hangup_call()

    @function_tool
    async def check_availability(self, date: str) -> bool:
        """Check if the requested date is available"""
        # Simulate checking availability
        return True

    # Event handlers for more precise timing (if available in your LiveKit setup)
    async def on_speech_started(self, ctx: RunContext):
        """Called when user starts speaking"""
        self.current_speech_start_time = time.time()
        logging.info("[Agent] User started speaking")
        
    async def on_speech_ended(self, ctx: RunContext):
        """Called when user stops speaking"""
        self.current_speech_end_time = time.time()
        logging.info(f"[Agent] User stopped speaking")

# Enhanced Assistant with VAD event tracking (if supported)
class EnhancedAssistant(Assistant):
    """Assistant with more precise VAD-based timing"""
    
    def __init__(self, metrics=None):
        super().__init__(metrics)
        self.vad_start_time = None
        self.vad_end_time = None
        
    async def on_vad_start(self, ctx: RunContext):
        """Handle VAD start event"""
        self.vad_start_time = time.time()
        self.current_speech_start_time = self.vad_start_time
        logging.info(f"[VAD] Speech started at {self.vad_start_time}")
        
    async def on_vad_end(self, ctx: RunContext):
        """Handle VAD end event"""
        self.vad_end_time = time.time()
        self.current_speech_end_time = self.vad_end_time
        logging.info(f"[VAD] Speech ended at {self.vad_end_time}")
        
    async def on_message(self, ctx: RunContext):
        """Enhanced message handling with VAD timing"""
        # Use VAD timing if available, otherwise fall back to estimation
        if self.vad_start_time and self.vad_end_time:
            self.current_speech_start_time = self.vad_start_time
            self.current_speech_end_time = self.vad_end_time
        
        # Call parent implementation
        await super().on_message(ctx)



# import time
# import logging
# import csv
# import datetime
# import os
# from typing import Any, Optional
# from dataclasses import dataclass
# from livekit.agents import function_tool, Agent, RunContext
# from livekit.agents import get_job_context
# from livekit import api
# from src.prompts.system_prompt import *

# @dataclass
# class InventoryItems:
#     item_name: str
#     quantity: int

# # --- Utility: Hang up function ---
# async def hangup_call():
#     ctx = get_job_context()
#     if ctx is None:
#         return
#     await ctx.api.room.delete_room(
#         api.DeleteRoomRequest(
#             room=ctx.room.name,
#         )
#     )

# # --- Response Time Logger ---
# class ResponseTimeLogger:
#     def __init__(self):
#         self.logs_dir = "logs"
#         os.makedirs(self.logs_dir, exist_ok=True)
#         timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
#         self.csv_file = os.path.join(self.logs_dir, f"response_times_{timestamp}.csv")
#         self.initialize_csv()
#         self.interaction_count = 0
        
#     def initialize_csv(self):
#         """Initialize CSV file with headers"""
#         try:
#             with open(self.csv_file, 'w', newline='') as f:
#                 writer = csv.writer(f)
#                 writer.writerow([
#                     "timestamp",
#                     "interaction_id", 
#                     "speech_end_time",
#                     "response_start_time",
#                     "total_response_latency_ms",
#                     "total_response_latency_seconds"
#                 ])
#             logging.info(f"[ResponseLogger] CSV file initialized: {self.csv_file}")
#         except Exception as e:
#             logging.error(f"[ResponseLogger] Failed to initialize CSV: {e}")
    
#     def log_response_time(self, speech_end_time: float, response_start_time: float, interaction_id: str):
#         """Log response time directly to CSV"""
#         try:
#             response_latency = response_start_time - speech_end_time
            
#             # Write to CSV immediately
#             with open(self.csv_file, 'a', newline='') as f:
#                 writer = csv.writer(f)
#                 writer.writerow([
#                     datetime.datetime.now().isoformat(),
#                     interaction_id,
#                     speech_end_time,
#                     response_start_time,
#                     round(response_latency * 1000, 2),  # milliseconds
#                     round(response_latency, 3)  # seconds
#                 ])
            
#             logging.info(f"[ResponseLogger] Logged response time: {response_latency * 1000:.2f}ms for interaction {interaction_id}")
#             return response_latency
#         except Exception as e:
#             logging.error(f"[ResponseLogger] Failed to log response time: {e}")
#             return 0

# # --- Main Assistant Agent ---
# class Assistant(Agent):
#     def __init__(self) -> None:
#         super().__init__(
#             instructions=EMPLOYEE_LOOKUP_PROMPT
#         )
#         # Create response time logger
#         self.response_logger = ResponseTimeLogger()
#         self.conversation_start = time.time()
#         self.conversation_id = str(datetime.datetime.now().timestamp())
#         self.interaction_count = 0
        
#         # Track timing for response calculation
#         self.user_speech_end_time = None
        
#         logging.info(f"[Assistant] Initialized with conversation ID: {self.conversation_id}")
#         logging.info(f"[Assistant] CSV log file: {self.response_logger.csv_file}")

#     async def on_message(self, ctx: RunContext):
#         """Handle incoming messages and calculate response time"""
#         self.interaction_count += 1
#         interaction_id = f"{self.conversation_id}_{self.interaction_count}"
        
#         # Record when we start processing (this is when user finished speaking)
#         user_speech_end_time = time.time()
        
#         logging.info(f"[Assistant] Processing interaction {interaction_id}")
#         logging.info(f"[Assistant] User said: {ctx.input.text}")
        
#         # Start timing our response
#         response_start_time = time.time()
        
#         # Calculate and log response time
#         response_latency = self.response_logger.log_response_time(
#             user_speech_end_time,
#             response_start_time,
#             interaction_id
#         )
        
#         # Generate LLM response
#         try:
#             response_text = await self.generate_response(ctx.input.text)
#             logging.info(f"[Assistant] Generated response: {response_text}")
#         except Exception as e:
#             logging.error(f"[Assistant] Error generating response: {e}")
#             response_text = "I apologize, but I encountered an error. Could you please repeat that?"
        
#         # Send response to user
#         await ctx.session.say(response_text)
        
#         logging.info(f"[Assistant] Completed interaction {interaction_id} with {response_latency * 1000:.2f}ms latency")

#     async def generate_response(self, user_input: str) -> str:
#         """Generate a response using the LLM"""
#         # Simple response logic - you can expand this
#         if "order" in user_input.lower():
#             return "I can help you with ordering items. What would you like to order and in what quantity?"
#         elif "availability" in user_input.lower() or "available" in user_input.lower():
#             return "I can check availability for you. What date are you interested in?"
#         elif "end" in user_input.lower() or "bye" in user_input.lower() or "goodbye" in user_input.lower():
#             return "Thank you for your time. I'll end the call now. Goodbye!"
#         else:
#             return f"I understand you said: {user_input}. How can I assist you today?"

#     @function_tool
#     async def order_items(self, items: InventoryItems) -> str:
#         """Order items from the inventory"""
#         # Log this as a separate interaction
#         self.interaction_count += 1
#         interaction_id = f"{self.conversation_id}_{self.interaction_count}_order"
        
#         function_start_time = time.time()
#         function_end_time = function_start_time + 0.1  # Simulate processing time
        
#         self.response_logger.log_response_time(
#             function_start_time,
#             function_end_time,
#             interaction_id
#         )
        
#         return f"Order for {items.quantity} {items.item_name} has been placed successfully."

#     @function_tool
#     async def check_availability(self, date: str) -> bool:
#         """Check if the requested date is available"""
#         # Log this as a separate interaction
#         self.interaction_count += 1
#         interaction_id = f"{self.conversation_id}_{self.interaction_count}_availability"
        
#         function_start_time = time.time()
#         function_end_time = function_start_time + 0.05  # Simulate processing time
        
#         self.response_logger.log_response_time(
#             function_start_time,
#             function_end_time,
#             interaction_id
#         )
        
#         return True

#     @function_tool
#     async def end_call(self, ctx: RunContext):
#         """End the call when user wants to hang up"""
#         # Let the agent finish speaking
#         current_speech = ctx.session.current_speech
#         if current_speech:
#             await current_speech.wait_for_playout()
        
#         # Log final statistics
#         logging.info(f"[Assistant] Call ended. Total interactions: {self.interaction_count}")
#         logging.info(f"[Assistant] CSV log file saved at: {self.response_logger.csv_file}")
        
#         # Add a final log entry for call end
#         self.interaction_count += 1
#         interaction_id = f"{self.conversation_id}_{self.interaction_count}_end_call"
        
#         end_time = time.time()
#         self.response_logger.log_response_time(
#             end_time - 0.1,
#             end_time,
#             interaction_id
#         )
        
#         await hangup_call()

#     async def on_start(self, ctx: RunContext):
#         """Called when the agent starts"""
#         logging.info(f"[Assistant] Agent started in room: {ctx.room.name}")
        
#         # Log the start of conversation
#         start_time = time.time()
#         self.response_logger.log_response_time(
#             start_time - 0.1,
#             start_time,
#             f"{self.conversation_id}_start"
#         )
        
#         # Send initial greeting
#         await ctx.session.say("Hello! I'm your assistant. How can I help you today?")

#     async def on_end(self, ctx: RunContext):
#         """Called when the agent ends"""
#         logging.info(f"[Assistant] Agent ended. Final CSV file: {self.response_logger.csv_file}")
        
#         # Log the end of conversation
#         end_time = time.time()
#         self.response_logger.log_response_time(
#             end_time - 0.1,
#             end_time,
#             f"{self.conversation_id}_end"
#         )

# # Test function to simulate interactions
# def test_response_logger():
#     """Test the response logger independently"""
#     logging.info("Testing Response Logger...")
    
#     logger = ResponseTimeLogger()
    
#     # Simulate some interactions
#     base_time = time.time()
    
#     for i in range(1, 6):
#         speech_end = base_time + (i * 2)
#         response_start = speech_end + (0.2 + (i * 0.05))
        
#         logger.log_response_time(speech_end, response_start, f"test_{i}")
#         logging.info(f"Test interaction {i} logged")
    
#     logging.info(f"Test completed. CSV file: {logger.csv_file}")
#     return logger.csv_file

# if __name__ == "__main__":
#     # Test the logger
#     test_response_logger()