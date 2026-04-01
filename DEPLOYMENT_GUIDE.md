# BioCodeTeacher - Getting Started

BioCodeTeacher is an AI-powered bioinformatics code educator for single-cell, spatial transcriptomics, and digital pathology analysis. You point it at any project folder, click on a line of code, and it tells you what that line does and why it matters biologically.

This guide walks you through every step from a fresh machine to a running app.

There are **two ways** to run BioCodeTeacher:

| Method | Best for | Requirements |
|--------|----------|-------------|
| **Option A: Standalone exe** | End users, no setup | Just unzip and run |
| **Option B: From source** | Developers, contributors | Python + Node.js |

---

## Option A: Standalone Executable (Easiest)

If someone has given you a `BioCodeTeacher.zip` file (or you downloaded a release), this is all you need:

### Step 1: Unzip

1. Right-click the `.zip` file and click **"Extract All"**
2. Choose a location (e.g., your Desktop or `C:\BioCodeTeacher`)
3. Open the extracted folder — you should see `BioCodeTeacher.exe`

### Step 2: Get an OpenRouter API Key

BioCodeTeacher uses AI models (Claude, GPT, Gemini) through a service called OpenRouter. You need a free account and a small amount of credit.

1. Go to **https://openrouter.ai/**
2. Click **"Sign Up"** and create an account (Google sign-in works)
3. Go to **https://openrouter.ai/keys**
4. Click **"Create Key"**
5. **Copy the key** — it looks like `sk-or-v1-abc123...` (you'll paste it into BioCodeTeacher later)
6. Go to **https://openrouter.ai/credits** and add a small amount ($5 is plenty to start)

> **Cost:** Each code explanation costs roughly $0.01-0.05. Architecture analysis costs about $0.10-0.20. $5 gives you hundreds of explanations.

### Step 3: Run

1. **Double-click `BioCodeTeacher.exe`**
2. A console window appears with the server status
3. Your browser opens automatically to BioCodeTeacher
4. Paste your OpenRouter API key, choose a model, and click **"Get Started"**

That's it! Skip ahead to **[Step 7: Load a Project](#step-7-load-a-project)** below.

> **Note:** The first time you run it, Windows SmartScreen may show "Windows protected your PC". Click **"More info"** then **"Run anyway"**. This is normal for unsigned applications.

### Stopping

- Close the console window, or press **Ctrl+C** in it

---

## Option B: From Source (Developer Setup)

This method requires installing Python and Node.js. Use this if you want to modify BioCodeTeacher or contribute to development.

### Step 1: Install Python

BioCodeTeacher's backend runs on Python. You need **Python 3.10, 3.11, 3.12, or 3.13**. Python 3.14 is too new and won't work yet (some dependencies don't have pre-built packages for it).

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

BioCodeTeacher's frontend runs on Node.js.

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

BioCodeTeacher uses AI models (Claude, GPT, Gemini) through a service called OpenRouter. You need a free account and a small amount of credit.

1. Go to **https://openrouter.ai/**
2. Click **"Sign Up"** and create an account (Google sign-in works)
3. Go to **https://openrouter.ai/keys**
4. Click **"Create Key"**
5. **Copy the key** — it looks like `sk-or-v1-abc123...` (you'll paste it into BioCodeTeacher later)
6. Go to **https://openrouter.ai/credits** and add a small amount ($5 is plenty to start)

> **Cost:** Each code explanation costs roughly $0.01-0.05. Architecture analysis costs about $0.10-0.20. $5 gives you hundreds of explanations.

---

## Step 4: Download BioCodeTeacher

You have two options:

### Option A: Download as ZIP (easiest)

1. Go to **https://github.com/alexs42/BioCodeTeacher**
2. Click the green **"<> Code"** button
3. Click **"Download ZIP"**
4. Open the downloaded ZIP file
5. Click **"Extract All"** and choose a location (e.g., your Desktop or `C:\BioCodeTeacher`)
6. Open the extracted folder — you should see files like `start.bat`, `README.md`, `backend/`, `frontend/`, etc.

### Option B: Clone with Git (if you have Git installed)

Open Command Prompt and type:
```
cd C:\
git clone https://github.com/alexs42/BioCodeTeacher.git
cd BioCodeTeacher
```

---

## Step 5: Start BioCodeTeacher

1. Open the BioCodeTeacher folder in **File Explorer**
2. **Double-click `start.bat`**

That's it. Here's what happens:

```
==========================================
  Starting BioCodeTeacher
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

## Step 6: Set Up BioCodeTeacher (first time only)

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

Now you need to point BioCodeTeacher at some code.

1. Click **"Open Repository"** in the top-left
2. Type a path, or click the **browse button** (hard drive icon) to navigate visually
3. For example, try loading BioCodeTeacher itself:
   ```
   C:\BioCodeTeacher
   ```
4. Click **"Load"**

A file tree appears on the left. On the right, **architecture analysis starts automatically** — you'll see a 4-phase progress tracker as the AI examines your codebase.

> **Tip:** You can also paste a GitHub URL like `https://github.com/someone/project`.

> **Tip:** The analysis is saved to disk (`C:\BioCodeTeacher\` folder). Next time you load the same project, the overview appears instantly.

---

## Step 8: Explore the Three-Tier Context

BioCodeTeacher shows you progressively more detail as you drill into the code:

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

The chat panel is open and ready at the bottom-right — no expand click needed. It lets you ask follow-up questions about the code you're viewing.

**Examples of what you can ask:**
- "What design pattern is this using?"
- "Why is this function async?"
- "What would happen if I removed this line?"
- "Can you show me a simpler way to write this?"
- "What are the potential bugs here?"

There are **educational prompt suggestions** to get you started:
- **Teach me this repo** — architecture walkthrough with pros/cons
- **Critique this code** — review with concrete improvement suggestions
- **Tutorial mode** — step-by-step file walkthrough
- **Analyze architecture** — trigger the 4-phase agentic analysis
- **Explain with examples** — concrete usage examples for the current file
- **Find potential bugs** — reviews the code for issues
- **Create diagram** — generates a visual diagram of the current file

---

## Stopping BioCodeTeacher

**If using the standalone exe:** Close the console window, or press **Ctrl+C**.

**If running from source:**
- Press **Ctrl+C** in the frontend window
- Close the minimized "BioCodeTeacher Backend" window
- Or just close both Command Prompt windows

---

## Updating BioCodeTeacher

**If using the standalone exe:**
1. Download the new `BioCodeTeacher.zip`
2. Extract it to the same location (overwrite old files)
3. Double-click `BioCodeTeacher.exe`

**If you downloaded the source as ZIP:**
1. Download the new ZIP from GitHub
2. Extract it to the same location (overwrite old files)
3. Double-click `start.bat`

**If you used Git:**
```
cd C:\BioCodeTeacher
git pull
start.bat
```

## Building the Standalone Application (for developers)

### Windows

1. Make sure **Python 3.10–3.13** and **Node.js** are installed (Steps 1-2 above)
2. Open Command Prompt in the BioCodeTeacher folder
3. Run:
   ```
   build.bat
   ```
4. Wait for the build to complete (takes a few minutes)
5. The output is in `dist\BioCodeTeacher\` — zip this folder to distribute

### macOS

1. Make sure **Python 3.10–3.13** and **Node.js** are installed
2. Open Terminal in the BioCodeTeacher folder
3. Run:
   ```bash
   ./build.sh
   ```
4. Wait for the build to complete
5. Output: `dist/BioCodeTeacher.app` and `dist/BioCodeTeacher.dmg`
6. First launch: right-click > Open to bypass Gatekeeper (unsigned app)

To install: open the DMG and drag BioCodeTeacher to Applications.

### How the build works

Both platforms use `biocodeteacher.spec` (cross-platform PyInstaller spec):

1. **Prerequisites** — finds Python 3.10–3.13, checks npm
2. **Frontend build** — `npm install` + `npm run build`
3. **Python environment** — creates `build_venv`, installs dependencies
4. **Clean previous build** — removes old output (Windows has Dropbox retry loops)
5. **PyInstaller** — bundles backend + frontend into a standalone app
6. **DMG creation** (macOS only) — wraps `.app` into a `.dmg` with Applications shortcut

### Build troubleshooting

| Error | Fix |
|-------|-----|
| `Python X.X is too new` | Install Python 3.12 or 3.13 alongside your current version |
| `pip install failed` | Check internet connection; make sure you're on Python 3.10–3.13 |
| `Cannot delete dist\BioCodeTeacher` | Pause Dropbox sync or close Explorer windows in that folder |
| `Frontend build failed` | Run `cd frontend && npm install` manually first |
| macOS "app is damaged" | Right-click > Open to bypass Gatekeeper |

---

## FAQ

**Q: Is my code sent to the internet?**
A: Your code is sent to OpenRouter's API for AI processing, the same way ChatGPT works. It is not stored or used for training. If this is a concern, don't use it with proprietary code.

**Q: How much does it cost?**
A: Each line explanation costs about $0.01-0.05 depending on the model. Architecture analysis costs $0.10-0.20. $5 of credit lasts a long time.

**Q: Can I use it offline?**
A: No. BioCodeTeacher requires an internet connection to call AI models through OpenRouter.

**Q: Can I use it with any programming language?**
A: Yes. BioCodeTeacher supports 40+ languages including Python, JavaScript, TypeScript, Java, C/C++, Go, Rust, Ruby, PHP, Swift, Kotlin, and more.

**Q: The explanations are wrong/confusing.**
A: Try switching to a different AI model in Settings (gear icon). Claude Opus 4.6 generally gives the best results.

**Q: Can I use my own OpenAI/Anthropic key directly?**
A: No. BioCodeTeacher uses OpenRouter as a unified gateway. OpenRouter supports all major AI providers through a single API key.

---

## Screenshot

![BioCodeTeacher Interface](Screenshot%202026-02-10%20130144.png)

The interface has three main areas:
- **Left:** File tree and code editor — browse files and click lines
- **Top-right:** Context panel — shows repo overview, file summary, or line explanation depending on what you've selected (breadcrumb navigation at the top)
- **Bottom-right:** Chat panel (open by default) — ask follow-up questions about the code, with educational prompt suggestions
