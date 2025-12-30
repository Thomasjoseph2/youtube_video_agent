# 🎬 YouTube Video AI Agent

An intelligent AI agent that creates YouTube Shorts videos from text prompts using Gemini AI, Pexels stock footage, and automated video editing.

## ✨ Features

- 🧠 **AI-Powered Script Generation**: Uses Google Gemini to create engaging scripts
- 🎥 **Automatic Media Fetching**: Downloads relevant stock videos from Pexels
- 🎙️ **Text-to-Speech**: Generates natural voiceovers using Google TTS
- ✂️ **Smart Video Editing**: Automatically assembles videos with subtitles
- ☁️ **Cloudinary Integration**: Uploads final videos to the cloud
- 🧹 **Lightweight Server**: Auto-cleanup keeps your server storage minimal

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- FFmpeg installed
- API Keys for:
  - Google Gemini
  - Pexels
  - Cloudinary

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Thomasjoseph2/youtube_video_agent.git
cd "invideo clone"
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

Create a `.env` file with:

```env
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Pexels API
PEXELS_API_KEY=your_pexels_api_key

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## 📖 Usage

### Run the Flask App

```bash
python app.py
```

The app will start on `http://localhost:5000`

### Create a Video

```bash
POST /create-video
{
  "prompt": "Create a 10-second video about golden retriever puppies playing"
}
```

## 🧹 Automatic Cleanup (Lightweight Server)

The orchestrator automatically cleans up files to keep your server lightweight:

1. **After Processing**:
   - ✅ Uploads final video to Cloudinary
   - 🗑️ Deletes temp directory (`data/temp/`)
   - 🗑️ Deletes result directory (`data/results/`)
   - 🗑️ Cleans up fetched media (`media/`)

2. **What's Kept**:
   - ✅ Video metadata in `data/library.json`
   - ✅ Cloudinary URL for video access
   - ✅ Python source code

3. **Git Ignores**:
   - `.env` (sensitive data)
   - `.venv/` (virtual environment)
   - `__pycache__/` (Python cache)
   - `media/` (fetched videos)
   - `data/temp/` (temporary files)
   - `data/results/` (final videos - stored on Cloudinary)

## 📁 Project Structure

```
.
├── agent.py                 # AI Director (Gemini script generation)
├── media_fetcher.py         # Pexels video downloader
├── audio_generator.py       # Google TTS integration
├── video_editor.py          # MoviePy video assembly
├── cloudinary_manager.py    # Cloud upload handler
├── orchestrator.py          # Main workflow orchestrator
├── library_manager.py       # Video record storage
├── app.py                   # Flask API server
├── main.py                  # CLI interface
├── data/
│   └── library.json        # Video metadata (only this persists)
└── requirements.txt
```

## 🎯 Workflow

1. **User submits prompt** → Flask API receives request
2. **AI Director** → Gemini generates script with timeline
3. **Media Fetcher** → Downloads relevant Pexels videos
4. **Audio Generator** → Creates voiceover with TTS
5. **Video Editor** → Assembles final video with subtitles
6. **Cloudinary Upload** → Saves video to cloud
7. **Auto Cleanup** → Removes all local temp/result files
8. **Response** → Returns Cloudinary URL to user

## 🔧 API Endpoints

### POST `/create-video`
Creates a new video from a text prompt.

**Request:**
```json
{
  "prompt": "Your video idea here"
}
```

**Response:**
```json
{
  "success": true,
  "video": {
    "id": "20251230_123456_your_video_idea",
    "cloudinary_url": "https://res.cloudinary.com/...",
    "timestamp": "20251230_123456"
  }
}
```

### GET `/videos`
Lists all created videos from the library.

## 🛠️ Development

### Run in Development Mode

```bash
python main.py
```

This runs the CLI version for testing.

## 📝 Notes

- All videos are stored **only on Cloudinary** after processing
- Local files are automatically deleted to save disk space
- The `data/library.json` file tracks video metadata
- Server stays lightweight with minimal storage usage

## 🐛 Troubleshooting

### Video files taking up space?
The orchestrator should auto-cleanup. If not, manually delete:
```bash
rm -rf data/temp/*
rm -rf data/results/*
rm -rf media/*
```

### Git repository too large?
Videos should be in `.gitignore`. Clean Git history if needed:
```bash
git rm -r --cached data/temp data/results media
git commit -m "Remove video files from tracking"
```

## 📄 License

MIT License - feel free to use and modify!

## 👨‍💻 Author

Thomas Joseph

---

**Note**: This project automatically manages storage by uploading videos to Cloudinary and deleting local copies. Your server will stay lightweight! ⚡
