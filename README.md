# ScriptNova

Turn audio and video recordings into text — on your own Windows laptop, no
subscription, no account, no uploading your files to some company's cloud.

You give it a recording, it gives you back a clean transcript (with who-said-what
speaker labels and a summary) that you can copy or download as TXT, DOCX, or SRT.

It uses [AssemblyAI](https://www.assemblyai.com/) to do the actual speech-to-text
work, so you'll need a free AssemblyAI account — more on that below. Everything
else (the app, your files, your transcripts) stays on your computer.

## Getting started (takes about 5 minutes)

### Step 1 — Install Python

This app needs Python to run. If you don't already have it:

1. Go to **[python.org/downloads](https://www.python.org/downloads/)** and
   download the latest version.
2. Run the installer. **Important:** on the first screen, check the box that
   says **"Add python.exe to PATH"** before clicking Install.

### Step 2 — Download ScriptNova

Pick whichever of these is easier for you — both end up with the same
folder on your computer.

**Option A — ZIP download (no Git needed)**
1. Click the green **Code** button at the top of this page → **Download ZIP**.
2. Once it's downloaded, right-click the ZIP file and choose **Extract All**.
3. Open the extracted folder.

**Option B — Git clone**
1. Open a terminal (Command Prompt or PowerShell).
2. Run:
   ```
   git clone https://github.com/phukhang2211/scriptnova.git
   ```
3. Open the new `scriptnova` folder it created.

### Step 3 — Run one script

Inside the folder, double-click **`install-autostart.bat`**.

A black window will open and install everything the app needs — this only
takes a minute or two. When it's done, your browser opens to the app
automatically.

From now on, ScriptNova starts quietly in the background every time you log
into Windows — no window, nothing to double-click. Just open
**http://127.0.0.1:8000/** in your browser whenever you want to use it.

> If Windows shows a blue "Windows protected your PC" popup, click **More
> info** → **Run anyway**. This happens because the app isn't a signed,
> paid piece of software — the code is right here in this repo for anyone
> to read.

> Don't want it running all the time? Double-click **`setup.bat`** instead,
> then use **`run.bat`** whenever you want to open it — see
> [Running it without auto-start](#running-it-without-auto-start) below.

### Step 4 — Add your AssemblyAI key

The first time you open the app, it'll ask you to add an AssemblyAI API key.

1. Go to **[assemblyai.com/dashboard](https://www.assemblyai.com/dashboard)**
   and sign up (free — no credit card required).
2. Copy your API key from the dashboard.
3. Paste it into the **Settings** page in ScriptNova and click **Save**.

That's it — you can now upload a file and get a transcript.

## Using it after the first time

Nothing to do — it's already running. Just open
**http://127.0.0.1:8000/** in your browser any time.

To stop it starting automatically, double-click **`uninstall-autostart.bat`**.

## Running it without auto-start

If you'd rather start ScriptNova by hand instead of it running all the
time in the background:

1. Double-click **`setup.bat`** once (installs everything, same as above,
   but doesn't register auto-start).
2. Double-click **`run.bat`** whenever you want to use it. A window opens
   and your browser opens to the app — closing that window stops the app.

You can switch between the two later: `install-autostart.bat` and
`uninstall-autostart.bat` just turn the background auto-start on or off,
and are safe to run more than once.

## Troubleshooting

**"Python was not found" when I double-click a .bat file**
Python isn't installed, or wasn't added to PATH. Reinstall Python from
[python.org](https://www.python.org/downloads/) and make sure to check
"Add python.exe to PATH" during setup.

**Video files fail to transcribe**
Install [ffmpeg](https://ffmpeg.org/download.html) and make sure it's on
your `PATH` — it's used to pull the audio out of video files before sending
it to AssemblyAI. Audio files (MP3, WAV, M4A) don't need it.

**The browser opened but shows an error / can't connect**
The server can take a couple of seconds to start. Wait a moment and refresh
the page.

**I want to start over / reset everything**
Run `uninstall-autostart.bat` (if you'd installed auto-start), then delete
the `.venv` folder and the `db.sqlite3` file, then run `install-autostart.bat`
or `setup.bat` again.

## What it does and doesn't do

- No accounts, no login screen — it's your computer, your app.
- No billing, no limits — you're using your own free AssemblyAI account.
- Your uploaded files are stored locally in the `media` folder and stay
  there until you delete the job from the dashboard.
- Supports MP3, WAV, M4A, AAC, MP4, MOV, WebM — up to 1 GB per file by default.
- Automatic language detection (or pick a language manually), speaker
  labels, an AI-generated summary, and TXT / DOCX / SRT export.
- English and Vietnamese interface (switch in the top-right corner).

---

## Advanced / other ways to run it

<details>
<summary>macOS / Linux, or running manually instead of the .bat files</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

You'll also need [ffmpeg](https://ffmpeg.org/download.html) on your `PATH`
to transcribe video files.
</details>

<details>
<summary>Running with Docker instead</summary>

```bash
cp .env.example .env
docker compose up -d
```

Then open `http://127.0.0.1:8000/`.
</details>

<details>
<summary>Configuration reference</summary>

Everything in `.env.example` has a working default — you shouldn't need to
touch it. The two settings worth knowing about:

| Var | Purpose |
|-----|---------|
| `ASSEMBLYAI_API_KEY` | Fallback key if you don't set one on the Settings page |
| `MAX_UPLOAD_FILE_SIZE_MB` | Max upload size (default 1024 MB) |
</details>

<details>
<summary>Running tests</summary>

```bash
python manage.py test jobs
```
</details>
