# Speech-to-Text API

A FastAPI-based speech-to-text service using OpenAI Whisper that converts audio files to text with precise timestamps.

## Features

- 🎵 Support for multiple audio formats (MP3, WAV, M4A, FLAC, OGG, WMA, AAC)
- ⏱️ Precise timestamps with minutes and seconds
- 🚀 Fast transcription using OpenAI Whisper
- 🐳 Docker support for easy deployment
- 📊 Health check endpoints
- 🔧 Production-ready with Nginx reverse proxy

## API Endpoints

### POST `/transcribe`
Transcribe an audio file and return text with timestamps.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Audio file

**Response:**
```json
{
  "text": "Full transcription text",
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "Hello world",
      "minutes": 0,
      "seconds": 0
    }
  ],
  "duration": 10.5,
  "language": "en"
}
```

### GET `/health`
Health check endpoint.

### GET `/`
API information and version.

## Local Development

### Prerequisites
- Python 3.11+
- FFmpeg

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd readymode
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

4. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## Docker Deployment

### Basic Deployment

1. Build and run with Docker:
```bash
docker build -t stt-api .
docker run -p 8000:8000 stt-api
```

2. Or use Docker Compose:
```bash
docker-compose up -d
```

### Production Deployment with Nginx

1. Run with production profile:
```bash
docker-compose --profile production up -d
```

This will start both the API and Nginx reverse proxy.

## VPS Deployment

### Prerequisites
- Docker and Docker Compose installed on your VPS
- Domain name (optional, for SSL)

### Steps

1. Clone the repository on your VPS:
```bash
git clone <your-repo-url>
cd readymode
```

2. Create logs directory:
```bash
mkdir logs
```

3. For basic deployment:
```bash
docker-compose up -d
```

4. For production with Nginx:
```bash
docker-compose --profile production up -d
```

### SSL Configuration (Optional)

1. Obtain SSL certificates (Let's Encrypt recommended):
```bash
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

2. Create SSL directory and copy certificates:
```bash
mkdir ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*
```

3. Uncomment SSL configuration in `nginx.conf`

4. Restart services:
```bash
docker-compose --profile production down
docker-compose --profile production up -d
```

## Usage Examples

### cURL
```bash
curl -X POST "http://localhost:8000/transcribe" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@audio.mp3"
```

### Python
```python
import requests

url = "http://localhost:8000/transcribe"
files = {"file": open("audio.mp3", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### JavaScript
```javascript
const formData = new FormData();
formData.append('file', audioFile);

fetch('http://localhost:8000/transcribe', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## Configuration

### Whisper Model
You can change the Whisper model in `main.py`:
- `tiny`: Fastest, least accurate
- `base`: Good balance (default)
- `small`: Better accuracy
- `medium`: Even better accuracy
- `large`: Best accuracy, slowest

### File Size Limits
Adjust `client_max_body_size` in `nginx.conf` for larger files.

### Timeout Settings
Modify timeout values in `nginx.conf` for longer audio files.

## Monitoring

- Health check: `GET /health`
- Logs: `docker-compose logs -f stt-api`
- Container status: `docker-compose ps`

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Install FFmpeg on your system
2. **Out of memory**: Use a smaller Whisper model or increase system RAM
3. **Timeout errors**: Increase timeout values in nginx.conf
4. **Large file uploads**: Increase `client_max_body_size` in nginx.conf

### Performance Tips

- Use GPU-enabled Docker images for faster transcription
- Implement file size limits to prevent abuse
- Add rate limiting for production use
- Use a CDN for file uploads in high-traffic scenarios

## License

MIT License - see LICENSE file for details.