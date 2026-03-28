# CodeTeacher - Getting Started (Windows)

CodeTeacher is an AI-powered tool that explains code to you line by line. You point it at any project folder, click on a line of code, and it tells you what that line does and why.

This guide walks you through every step from a fresh Windows machine to a running app.

There are **two ways** to run CodeTeacher:

| Method | Best for | Requirements |
|--------|----------|-------------|
| **Option A: Standalone exe** | End users, no setup | Just unzip and run |
| **Option B: From source** | Developers, contributors | Python + Node.js |

---

## Option A: Standalone Executable (Easiest)

If someone has given you a `CodeTeacher.zip` file (or you downloaded a release), this is all you need:

### Step 1: Unzip

1. Right-click the `.zip` file and click **"Extract All"**
2. Choose a location (e.g., your Desktop or `C:\CodeTeacher`)
3. Open the extracted folder — you should see `CodeTeacher.exe`

### Step 2: Get an OpenRouter API Key

CodeTeacher uses AI models (Claude, GPT, Gemini) through a service called OpenRouter. You need a free account and a small amount of credit.

1. Go to **https://openrouter.ai/**
2. Click **"Sign Up"** and create an account (Google sign-in works)
3. Go to **https://openrouter.ai/keys**
4. Click **"Create Key"**
5. **Copy the key** — it looks like `sk-or-v1-abc123...` (you'll paste it into CodeTeacher later)
6. Go to **https://openrouter.ai/credits** and add a small amount ($5 is plenty to start)

> **Cost:** Each code explanation costs roughly $0.01-0.05. Architecture analysis costs about $0.10-0.20. $5 gives you hundreds of explanations.

### Step 3: Run

1. **Double-click `CodeTeacher.exe`**
2. A console window appears with the server status
3. Your browser opens automatically to CodeTeacher
4. Paste your OpenRouter API key, choose a model, and click **"Get Started"**

That's it! Skip ahead to **[Step 7: Load a Project](#step-7-load-a-project)** below.

> **Note:** The first time you run it, Windows SmartScreen may show "Windows protected your PC". Click **"More info"** then **"Run anyway"**. This is normal for unsigned applications.

### Stopping

- Close the console window, or press **Ctrl+C** in it

---

## Option B: From Source (Developer Setup)

This method requires installing Python and Node.js. Use this if you want to modify CodeTeacher or contribute to development.

### Step 1: Install Python

CodeTeacher's backend runs on Python. You need **Python 3.10, 3.11, 3.12, or 3.13**. Python 3.14 is too new and won't work yet (some dependencies don't have pre-built packages for it).

1. Go to **https://www.python.org/downloads/**
2. Download **Python 3.12** or **3.13** (recommended — avoid 3.14 for now)
3. **Run the installer**
4. **IMPORTANT: Check the box that says "Add Python to PATH"** at the bottom of the first screen
5. Click **"Install Now"**
6. Wait for it to finish, then click **Close**

**Verify it worked:** Open Command Prompt (press `Win+R`, type `cmd`, press Enter) and type:
```
python --version
```
You should see something like `Python 3.12.x` or `Python 3.13.x`. If you see `'python' is not recognized`, you missed the "Add to PATH" checkbox — uninstall and reinstall Python with that box checked.

> **Already have Python 3.14?** You can install 3.12 alongside it. The `build.bat` script and `py` launcher will automatically find the right version.

---

## Step 2: Install Node.js

CodeTeacher's frontend runs on Node.js.

1. Go to **https://nodejs.org/**
2. Click the **LTS** download button (the green one on the left)
3. **Run the installer**
4. Click **Next** through all the screens (default settings are fine)
5. Click **Install**, then **Finish**

**Verify it worked:** Open a **new** Command Prompt window and type:
```
node --version
```
You should see something like `v20.x.x`.

---

## Step 3: Get an OpenRouter API Key

CodeTeacher uses AI models (Claude, GPT, Gemini) through a service called OpenRouter. You need a free account and a small amount of credit.

1. Go to **https://openrouter.ai/**
2. Click **"Sign Up"** and create an account (Google sign-in works)
3. Go to **https://openrouter.ai/keys**
4. Click **"Create Key"**
5. **Copy the key** — it looks like `sk-or-v1-abc123...` (you'll paste it into CodeTeacher later)
6. Go to **https://openrouter.ai/credits** and add a small amount ($5 is plenty to start)

> **Cost:** Each code explanation costs roughly $0.01-0.05. Architecture analysis costs about $0.10-0.20. $5 gives you hundreds of explanations.

---

## Step 4: Download CodeTeacher

You have two options:

### Option A: Download as ZIP (easiest)

1. Go to **https://github.com/alexs42/CodeTeacher**
2. Click the green **"<> Code"** button
3. Click **"Download ZIP"**
4. Open the downloaded ZIP file
5. Click **"Extract All"** and choose a location (e.g., your Desktop or `C:\CodeTeacher`)
6. Open the extracted folder — you should see files like `start.bat`, `README.md`, `backend/`, `frontend/`, etc.

### Option B: Clone with Git (if you have Git installed)

Open Command Prompt and type:
```
cd C:\
git clone https://github.com/alexs42/CodeTeacher.git
cd CodeTeacher
```

---

## Step 5: Start CodeTeacher

1. Open the CodeTeacher folder in **File Explorer**
2. **Double-click `start.bat`**

That's it. Here's what happens:

```
==========================================
  Starting CodeTeacher
==========================================

Backend will start in a separate window.
Frontend will run here. Press Ctrl+C to stop.
```

- A second window opens (minimized) running the backend server
- The main window installs dependencies and starts the frontend
- **First run takes 1-3 minutes** (downloading packages). Subsequent starts are fast.
- When you see `Local: http://localhost:5173/` the app is ready

3. Open your browser and go to: **http://localhost:5173**

### If `start.bat` doesn't work

If you get errors, try running the servers one at a time:

1. **Double-click `start-backend.bat`** — wait until you see `Uvicorn running on http://0.0.0.0:8000`
2. Open a second File Explorer window and **double-click `start-frontend.bat`** — wait until you see `Local: http://localhost:5173/`
3. Open **http://localhost:5173** in your browser

### Common errors at this step

| Error | Fix |
|-------|-----|
| `'python' is not recognized` | Reinstall Python 3.12/3.13 — check "Add to PATH" |
| `'npm' is not recognized` | Restart your computer after installing Node.js |
| `Port 8000 already in use` | Close other programs using that port, or restart your computer |
| `pip install` errors mentioning Rust/Cargo | You're on Python 3.14+ — install Python 3.12 or 3.13 instead |

---

## Step 6: Set Up CodeTeacher (first time only)

When the app opens in your browser, you'll see a **Welcome screen**.

1. **Paste your OpenRouter API key** into the first field
2. **Choose an AI model** from the dropdown (Claude Opus 4.6 is the default and recommended)
3. Click **"Get Started"**

Your key is saved in your browser — you won't need to enter it again.

### Which model should I pick?

| Model | Good for | Speed | Cost per explanation |
|-------|----------|-------|---------------------|
| **Claude Opus 4.6** | Best explanations overall | Medium | ~$0.03 |
| **GPT-5.4** | Strong reasoning | Medium | ~$0.02 |
| **Gemini 3.1 Pro** | Good all-rounder | Medium | ~$0.02 |
| **Gemini 3.0 Flash** | Fastest, cheapest | Fast | ~$0.005 |

Start with **Claude Opus 4.6** or **Gemini 3.0 Flash** if you want to save money.

---

## Step 7: Load a Project

Now you need to point CodeTeacher at some code.

1. Click **"Open Repository"** in the top-left
2. Type a path, or click the **browse button** (hard drive icon) to navigate visually
3. For example, try loading CodeTeacher itself:
   ```
   C:\CodeTeacher
   ```
4. Click **"Load"**

A file tree appears on the left. On the right, **architecture analysis starts automatically** — you'll see a 4-phase progress tracker as the AI examines your codebase.

> **Tip:** You can also paste a GitHub URL like `https://github.com/someone/project`.

> **Tip:** The analysis is saved to disk (`C:\CodeTeacher\` folder). Next time you load the same project, the overview appears instantly.

---

## Step 8: Explore the Three-Tier Context

CodeTeacher shows you progressively more detail as you drill into the code:

### Tier 1: Repository Overview (automatic)

After loading, the right panel shows:
- **Architecture overview** with component descriptions and relationships
- **Mermaid diagrams** showing how parts connect
- **Clickable file names** that navigate directly to files in the editor
- A progress tracker while analysis is running

### Tier 2: File Summary

1. **Click a file** in the file tree (e.g., `backend/main.py`)
2. The right panel shows an AI-generated **file summary**: purpose, role in the project, key components, connections to other files, and concepts to learn
3. **Clickable connection badges** let you navigate to imported/importing files

### Tier 3: Line Explanation

1. **Click any line** in the code editor
2. The right panel shows a detailed explanation enriched with both repo and file context
3. Includes purpose, token breakdown, how it fits, and diagrams

**Click and drag** across several lines to select a range — the AI explains the entire block as a unit.

Use the **breadcrumb bar** (`repo > file > line`) at the top of the right panel to navigate back to any level.

---

## Step 10: Use the Chat

The chat panel at the bottom-right lets you ask follow-up questions about the code you're viewing.

**Examples of what you can ask:**
- "What design pattern is this using?"
- "Why is this function async?"
- "What would happen if I removed this line?"
- "Can you show me a simpler way to write this?"
- "What are the potential bugs here?"

There are also **quick action buttons** for common tasks:
- **Create diagram** — generates a visual diagram of the current file
- **Find potential bugs** — reviews the code for issues
- **Summarize file** — gives a quick overview

---

## Stopping CodeTeacher

**If using the standalone exe:** Close the console window, or press **Ctrl+C**.

**If running from source:**
- Press **Ctrl+C** in the frontend window
- Close the minimized "CodeTeacher Backend" window
- Or just close both Command Prompt windows

---

## Updating CodeTeacher

**If using the standalone exe:**
1. Download the new `CodeTeacher.zip`
2. Extract it to the same location (overwrite old files)
3. Double-click `CodeTeacher.exe`

**If you downloaded the source as ZIP:**
1. Download the new ZIP from GitHub
2. Extract it to the same location (overwrite old files)
3. Double-click `start.bat`

**If you used Git:**
```
cd C:\CodeTeacher
git pull
start.bat
```

## Building the Standalone Executable (for developers)

If you want to build the `.exe` yourself from source:

1. Make sure **Python 3.10–3.13** and **Node.js** are installed (Steps 1-2 above)
2. Open Command Prompt in the CodeTeacher folder
3. Run:
   ```
   build.bat
   ```
4. Wait for the build to complete (takes a few minutes)
5. The output is in `dist\CodeTeacher\` — zip this folder to distribute

The build script runs 5 steps:
1. **Prerequisites** — finds a compatible Python (3.10–3.13) via the `py` launcher, checks npm
2. **Frontend build** — `npm install` + `npm run build`
3. **Python environment** — creates `build_venv`, installs dependencies (fails fast if `pip install` errors)
4. **Clean previous build** — removes old `dist\CodeTeacher\` with retries (handles Dropbox file locks)
5. **PyInstaller** — bundles everything into `dist\CodeTeacher\CodeTeacher.exe`

### Build troubleshooting

| Error | Fix |
|-------|-----|
| `Python X.X is too new` | Install Python 3.12 or 3.13 alongside your current version |
| `pip install failed` | Check internet connection; make sure you're on Python 3.10–3.13 |
| `Cannot delete dist\CodeTeacher` | Pause Dropbox sync or close Explorer windows in that folder |
| `Frontend build failed` | Run `cd frontend && npm install` manually first |

---

## FAQ

**Q: Is my code sent to the internet?**
A: Your code is sent to OpenRouter's API for AI processing, the same way ChatGPT works. It is not stored or used for training. If this is a concern, don't use it with proprietary code.

**Q: How much does it cost?**
A: Each line explanation costs about $0.01-0.05 depending on the model. Architecture analysis costs $0.10-0.20. $5 of credit lasts a long time.

**Q: Can I use it offline?**
A: No. CodeTeacher requires an internet connection to call AI models through OpenRouter.

**Q: Can I use it with any programming language?**
A: Yes. CodeTeacher supports 40+ languages including Python, JavaScript, TypeScript, Java, C/C++, Go, Rust, Ruby, PHP, Swift, Kotlin, and more.

**Q: The explanations are wrong/confusing.**
A: Try switching to a different AI model in Settings (gear icon). Claude Opus 4.6 generally gives the best results.

**Q: Can I use my own OpenAI/Anthropic key directly?**
A: No. CodeTeacher uses OpenRouter as a unified gateway. OpenRouter supports all major AI providers through a single API key.

---

## Screenshot

![CodeTeacher Interface](Screenshot%202026-02-10%20130144.png)

The interface has three main areas:
- **Left:** File tree and code editor — browse files and click lines
- **Top-right:** Context panel — shows repo overview, file summary, or line explanation depending on what you've selected (breadcrumb navigation at the top)
- **Bottom-right:** Chat panel — ask follow-up questions about the code
