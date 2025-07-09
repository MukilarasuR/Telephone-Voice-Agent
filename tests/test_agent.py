"""Tests for the voice agent."""

import pytest
import asyncio
from src.tools.voice_agent import VoiceAgent

class TestVoiceAgent:
    """Test cases for VoiceAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create a voice agent instance."""
        return VoiceAgent()
        
    @pytest.mark.asyncio
    async def test_agent_start_stop(self, agent):
        """Test agent start and stop functionality."""
        await agent.start()
        assert agent.is_running is True
        
        await agent.stop()
        assert agent.is_running is False
