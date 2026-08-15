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

Click the green **Code** button at the top of this page → **Download ZIP**.
Once it's downloaded, right-click the ZIP file and choose **Extract All**, then
open the extracted folder.

*(If you're comfortable with Git, `git clone` works too.)*

### Step 3 — Run the setup

Inside the folder, double-click **`setup.bat`**.

A black window will open and install everything the app needs. This only
takes a minute or two, and you only have to do this once. When it says
**"Setup complete"**, press any key to close the window.

> If Windows shows a blue "Windows protected your PC" popup, click **More
> info** → **Run anyway**. This happens because the app isn't a signed,
> paid piece of software — the code is right here in this repo for anyone
> to read.

### Step 4 — Start the app

Double-click **`run.bat`**. A window will open (keep it open — closing it
stops the app), and your browser will automatically open to the app.

### Step 5 — Add your AssemblyAI key

The first time you open the app, it'll ask you to add an AssemblyAI API key.

1. Go to **[assemblyai.com/dashboard](https://www.assemblyai.com/dashboard)**
   and sign up (free — no credit card required).
2. Copy your API key from the dashboard.
3. Paste it into the **Settings** page in ScriptNova and click **Save**.

That's it — you can now upload a file and get a transcript.

## Using it after the first time

You don't need to repeat the setup. Just double-click **`run.bat`** whenever
you want to use the app, and close its window when you're done.

## Troubleshooting

**"Python was not found" when I double-click setup.bat**
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
Delete the `.venv` folder and the `db.sqlite3` file, then run `setup.bat`
again.

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
