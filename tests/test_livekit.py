"""Tests for LiveKit functionality."""

import pytest
from src.livekit.room_manager import RoomManager
from src.livekit.participant_manager import ParticipantManager

class TestRoomManager:
    """Test cases for RoomManager."""
    
    @pytest.fixture
    def room_manager(self):
        """Create a room manager instance."""
        return RoomManager("test_key", "test_secret", "ws://localhost:7880")
        
    def test_room_manager_init(self, room_manager):
        """Test room manager initialization."""
        assert room_manager.api_key == "test_key"
        assert room_manager.api_secret == "test_secret"

class TestParticipantManager:
    """Test cases for ParticipantManager."""
    
    @pytest.fixture
    def participant_manager(self):
        """Create a participant manager instance."""
        return ParticipantManager()
        
    def test_add_participant(self, participant_manager):
        """Test adding a participant."""
        participant_manager.add_participant("test_id", {"name": "Test User"})
        assert "test_id" in participant_manager.participants
