# Lara AI Demo - AI Voice Agent

This repository is an MVP of the Lara AI voice agent system that provides real-time AI-powered voice interactions using LiveKit for WebRTC communication.

## Features

- Real-time voice processing
- AI-powered conversation handling
- LiveKit integration for WebRTC
- Speech-to-text and text-to-speech
- Modular architecture

## Project Structure

```
ai-voice-agent/
├── docker/                # Docker configuration
├── src/
│   ├── agent/             # Core voice agent logic
│   ├── livekit/           # LiveKit integration
│   └── utils/             # Utility modules
├── config/                # Configuration files
├── tests/                 # Test suite
└── main.py               # Application entry point                 # Test suite
└── call.py               # Outbound call

```

## Quick Start

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your API keys and configuration

3. Create environment:
  ```bash
  python3 -m venv env & source env/bin/activate
  ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the application:
   ```bash
   python main.py dev
   ```

6. To make the outbound call:
 _Change your phone number and sip trunk id in the `.env` file_
   ```bash
   python call.py
   ```



## Docker Deployment

```bash
cd docker
docker-compose up --build
```

## Configuration

- `config/app.yaml` - Main application configuration
- `config/livekit.yaml` - LiveKit specific settings
- `.env` - Environment variables (API keys, etc.)

## Development

Run tests:
```bash
pytest tests/
```

Code formatting:
```bash
black src/ tests/
```

## License

MIT License
