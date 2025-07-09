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
        """Create a dispatch and add a SIP participant to call the phone number"""
        self.lkapi = api.LiveKitAPI()
        self.outbound_trunk_id = "ST_BGckDMqrXEe2"
    
    async def make_call(self, phone_number):
        room_name = f"call-{phone_number.replace('+', '').replace('-', '')}-{int(asyncio.get_event_loop().time())}"
        agent_name = "asset_management_agent"
        
        # Create agent dispatch
        logger.info(f"Creating dispatch for agent {agent_name} in room {room_name}")
        dispatch = await self.lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=agent_name, room=room_name, metadata=phone_number
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
        except Exception as e:
            logger.error(f"Error creating SIP participant: {e}")
        
        # Close API connection
        await self.lkapi.aclose()



async def make_outbound_call():
    """Example function to make an outbound call"""
    telephony = TelephonyManager()
    
    # Replace with actual phone number in E.164 format
    phone_number = os.getenv("PHONE_NUMBER")
    phone_number = "+919363332539" 
    
    try:
        room_name = await telephony.make_call(phone_number)
        logger.info(f"Outbound call initiated to {phone_number} in room {room_name}")
        
        # The agent will automatically handle the call when someone joins the room
        return room_name
        
    except Exception as e:
        logger.error(f"Failed to make outbound call: {e}")



if __name__ == "__main__":
    
    # For outbound calls, you can use:
    asyncio.run(make_outbound_call())