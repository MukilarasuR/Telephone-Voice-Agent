#call.py file 

import asyncio
from livekit import api
import os
import logging
from dotenv import load_dotenv

load_dotenv()

from src.utils.logger import get_logger, setup_root_logger

# Setup logging first
setup_root_logger("DEBUG")
logger = get_logger(__name__)

class TelephonyManager:
    """Manage telephony operations with LiveKit"""
    
    def __init__(self):
        self.livekit_api = None
        self.setup_api()
        
    def setup_api(self):
        """Setup LiveKit API client"""
        self.lkapi = api.LiveKitAPI()
        self.outbound_trunk_id = "ST_BGckDMqrXEe2"
        
    async def make_call(self, phone_number):
        """Create a dispatch and add a SIP participant to call the phone number"""
        room_name = f"call-{phone_number.replace('+', '').replace('-', '')}-{int(asyncio.get_event_loop().time())}"
        agent_name = "asset_management_agent"
        
        # Create agent dispatch
        logger.info(f"Creating dispatch for agent {agent_name} in room {room_name}")
        dispatch = await self.lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=agent_name, 
                room=room_name, 
                metadata=phone_number
            )
        )
        logger.info(f"Created dispatch: {dispatch}")
        
        # Create SIP participant to make the call
        if not self.outbound_trunk_id or not self.outbound_trunk_id.startswith("ST_"):
            logger.error("SIP_OUTBOUND_TRUNK_ID is not set or invalid")
            return
            
        logger.info(f"Dialing {phone_number} to room {room_name}")
        
        try:
            # Create SIP participant to initiate the call
            sip_participant = await self.lkapi.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=room_name,
                    sip_trunk_id=self.outbound_trunk_id,
                    sip_call_to=phone_number,
                    participant_identity="phone_user",
                )
            )
            logger.info(f"Created SIP participant: {sip_participant}")
            
            # Return room name for monitoring
            return room_name
            
        except Exception as e:
            logger.error(f"Error creating SIP participant: {e}")
            return None
        
        # Close API connection
        await self.lkapi.aclose()

async def make_outbound_call():
    """Example function to make an outbound call"""
    telephony = TelephonyManager()
    
    # Replace with actual phone number in E.164 format
    phone_number = os.getenv("PHONE_NUMBER", "+919363332539")
    
    try:
        room_name = await telephony.make_call(phone_number)
        if room_name:
            logger.info(f"Outbound call initiated to {phone_number} in room {room_name}")
            
            # The agent will automatically handle the call when someone joins the room
            # Voice agent metrics tracking will be handled by the Assistant agent
            logger.info("Voice agent metrics tracking is active")
            logger.info("Metrics will be saved in the following formats:")
            logger.info("- CSV: logs/voice_agent_metrics_sessionXXX.csv")
            logger.info("- JSON: logs/voice_agent_metrics_sessionXXX.json")
            logger.info("- Human-readable table: printed to console at call end")
            
            # API endpoints for accessing metrics
            logger.info("Access metrics via:")
            logger.info("- http://localhost:8000/metrics (JSON)")
            logger.info("- http://localhost:8000/download-csv (CSV download)")
            logger.info("- http://localhost:8000/download-json (JSON download)")
            
            return room_name
        else:
            logger.error("Failed to create room for outbound call")
            return None
            
    except Exception as e:
        logger.error(f"Failed to make outbound call: {e}")
        return None

if __name__ == "__main__":
    # For outbound calls, you can use:
    result = asyncio.run(make_outbound_call())
    
    if result:
        print(f"Call initiated successfully. Room: {result}")
        print("\n" + "="*60)
        print("VOICE AGENT METRICS TRACKING ENABLED")
        print("="*60)
        print("The following metrics will be tracked:")
        print("1. User response waiting time")
        print("2. User speaking time")
        print("3. Agent reply time")
        print("4. Agent idle time per question")
        print("5. Average agent idle time")
        print("6. Total voice agent response time")
        print("7. Comprehensive latency summary")
        print("\nOutput formats:")
        print("- CSV file with detailed interaction data")
        print("- JSON file with structured metrics")
        print("- Human-readable table printed at call end")
        print("="*60)
    else:
        print("Failed to initiate call")



# import asyncio
# from livekit import api
# import os
# import logging
# from dotenv import load_dotenv

# load_dotenv()

# from src.utils.logger import get_logger, setup_root_logger

# # Setup logging first
# setup_root_logger("DEBUG")
# logger = get_logger(__name__)

# class TelephonyManager:
#     """Manage telephony operations with LiveKit"""
    
#     def __init__(self):
#         self.livekit_api = None
#         self.setup_api()
        
#     def setup_api(self):
#         """Setup LiveKit API client"""
#         self.lkapi = api.LiveKitAPI()
#         self.outbound_trunk_id = "ST_BGckDMqrXEe2"
        
#     async def make_call(self, phone_number):
#         """Create a dispatch and add a SIP participant to call the phone number"""
#         room_name = f"call-{phone_number.replace('+', '').replace('-', '')}-{int(asyncio.get_event_loop().time())}"
#         agent_name = "asset_management_agent"
        
#         # Create agent dispatch
#         logger.info(f"Creating dispatch for agent {agent_name} in room {room_name}")
#         dispatch = await self.lkapi.agent_dispatch.create_dispatch(
#             api.CreateAgentDispatchRequest(
#                 agent_name=agent_name, 
#                 room=room_name, 
#                 metadata=phone_number
#             )
#         )
#         logger.info(f"Created dispatch: {dispatch}")
        
#         # Create SIP participant to make the call
#         if not self.outbound_trunk_id or not self.outbound_trunk_id.startswith("ST_"):
#             logger.error("SIP_OUTBOUND_TRUNK_ID is not set or invalid")
#             return None
            
#         logger.info(f"Dialing {phone_number} to room {room_name}")
        
#         try:
#             # Create SIP participant to initiate the call
#             sip_participant = await self.lkapi.sip.create_sip_participant(
#                 api.CreateSIPParticipantRequest(
#                     room_name=room_name,
#                     sip_trunk_id=self.outbound_trunk_id,
#                     sip_call_to=phone_number,
#                     participant_identity="phone_user",
#                 )
#             )
#             logger.info(f"Created SIP participant: {sip_participant}")
            
#             # Log that response time tracking is active
#             logger.info("Response time tracking is now active")
#             logger.info("CSV logs will be saved in logs/response_times_*.csv")
            
#             return room_name
            
#         except Exception as e:
#             logger.error(f"Error creating SIP participant: {e}")
#             return None
#         finally:
#             # Close API connection
#             await self.lkapi.aclose()

# async def make_outbound_call():
#     """Example function to make an outbound call"""
#     telephony = TelephonyManager()
    
#     # Replace with actual phone number in E.164 format
#     phone_number = os.getenv("PHONE_NUMBER", "+919363332539")
    
#     try:
#         room_name = await telephony.make_call(phone_number)
#         if room_name:
#             logger.info(f"Outbound call initiated to {phone_number} in room {room_name}")
#             logger.info("Response time tracking is active - check logs/response_times_*.csv for latency data")
#             logger.info("API endpoints available at:")
#             logger.info("  - http://localhost:8000/response-stats (JSON stats)")
#             logger.info("  - http://localhost:8000/download-response-logs (download CSV)")
#             return room_name
#         else:
#             logger.error("Failed to create room for outbound call")
#             return None
            
#     except Exception as e:
#         logger.error(f"Failed to make outbound call: {e}")
#         return None

# if __name__ == "__main__":
#     # For outbound calls, you can use:
#     result = asyncio.run(make_outbound_call())
    
#     if result:
#         print(f"✅ Call initiated successfully. Room: {result}")
#         print(f"📊 Response time logs will be saved to logs/response_times_*.csv")
#         print(f"🌐 View response stats at: http://localhost:8000/response-stats")
#         print(f"📥 Download logs at: http://localhost:8000/download-response-logs")
#         print(f"💬 The agent will now track response times for each interaction")
#     else:
#         print("❌ Failed to initiate call")
        
#     # Keep the program running to maintain the call
#     print("Press Ctrl+C to stop the program")
#     try:
#         while True:
#             asyncio.sleep(1)
#     except KeyboardInterrupt:
#         print("Program stopped")