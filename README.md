# 🎬 Manim Studio — Animation IDE

A beautiful web-based IDE for creating and rendering Manim animations with Docker sandboxing, render history, and real-time syntax validation.

## ✨ Features

- **Monaco Editor** with Python syntax highlighting and auto-completion
- **🐳 Docker Sandboxing** — Renders user code in isolated containers for security
- **📋 Render History** — Track all your renders with playback, download, and code replay
- **✅ Syntax Validation** — Real-time Python and Manim syntax checking before rendering
- **One-click rendering** of Manim animations
- **Video preview** with built-in player
- **Download MP4** files for use anywhere
- **Example library** with ready-to-use templates
- **Quality settings** (150p to 4K)
- **Dark theme** with glassmorphism design

## 🚀 Quick Start

### Option 1: Local Development

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install -y ffmpeg texlive-latex-base texlive-latex-extra texlive-fonts-recommended libcairo2-dev libpango1.0-dev

# Install Python packages
pip install -r requirements.txt

# Run the IDE
python app.py
```

Open http://localhost:5000

### Option 2: Docker (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or just use the build script
chmod +x build.sh
./build.sh compose
```

### Option 3: Build Script

```bash
chmod +x build.sh

# See all options
./build.sh

# Quick start (install + run)
./build.sh 7
```

## 🐳 Docker Sandboxing

Manim Studio automatically detects Docker and uses it for sandboxed rendering when available:

- **Automatic detection** — No configuration needed
- **Isolated execution** — Each render runs in a temporary container
- **Resource limits** — Containers are memory-limited (1GB) and CPU-limited (2 cores)
- **Automatic cleanup** — Containers are destroyed after rendering
- **Graceful fallback** — Falls back to local rendering if Docker is unavailable

Status indicator in the bottom-left shows the current render mode (Docker/Local).

## 📋 Render History

Track all your renders with full metadata:

- **Playback** — Watch any previous render directly
- **Download** — Re-download any MP4 file
- **Code Replay** — Load the exact code from any past render
- **Delete** — Remove individual entries or clear all history
- **Persistent** — History survives server restarts (stored in JSON)

Access via the **History** tab in the navigation bar.

## ✅ Syntax Validation

Real-time syntax checking prevents render failures:

- **Python syntax** — Catches syntax errors before rendering
- **Manim structure** — Warns if no Scene subclass is found
- **Safety checks** — Flags potentially dangerous imports
- **Visual indicators** — Top bar shows syntax status (OK/Warning/Error)
- **Debounced** — Validates after 500ms of inactivity to avoid flickering

## 🎨 Usage

1. **Write Code** — Use the Monaco editor to write your Manim Python code
2. **Syntax Check** — Watch the syntax indicator for real-time feedback
3. **Choose Quality** — Select from Low (150p) to 4K (2160p)
4. **Render** — Click the purple "Render" button or press `Ctrl+Enter`
5. **Preview** — Watch your animation in the built-in video player
6. **Download** — Click the download button to save the MP4 file
7. **History** — Access past renders from the History tab

## 📝 Example Code

Click the "Examples" tab to browse and load ready-made Manim examples:

- **Circle** — Basic shape creation
- **Square to Circle** — Transform animation
- **Sine Wave** — Mathematical plotting
- **Dot Grid** — Color interpolation
- **Math Formula** — LaTeX rendering
- **Graph** — Function plotting
- **Bar Chart** — Data visualization

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Render animation |

## 🏗️ Architecture

```
manim_ide/
├── app.py                 # Flask backend with Docker sandboxing
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container build for full deployment
├── docker-compose.yml     # One-command deployment
├── vercel.json            # Vercel deployment config
├── build.sh               # Build & deploy script
├── api/
│   └── index.py           # Vercel serverless entry point
├── renders/               # Generated video files
├── render_history.json    # Persistent render history
├── static/
│   ├── css/style.css      # Dark glassmorphism theme
│   └── js/editor.js       # Monaco editor + validation + history
└── templates/
    └── index.html         # Main HTML template
```

## 🚢 Deployment

### Docker Deployment

```bash
docker-compose up -d
```

### Vercel Deployment (Frontend Only)

> ⚠️ **Important:** Vercel serverless functions cannot run Manim (requires FFmpeg, Cairo, Pango, LaTeX). Deploy the **frontend UI only** to Vercel and point it at a separate backend running on Docker/Railway/Fly.io.

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy (UI only — connect to external backend)
vercel --prod
```

### Manual Deployment

```bash
# Build zip package
./build.sh zip

# Upload and extract on your server
# Install deps and run
pip install -r requirements.txt
python app.py
```

## 🎯 Tips

- Docker provides the best security for rendering untrusted code
- Keep animations simple for faster rendering
- Use `self.wait()` at the end to see the result
- Lower quality renders faster during development
- Check syntax indicator before rendering to catch errors early

## 📄 License

MIT License — Free to use and modify
