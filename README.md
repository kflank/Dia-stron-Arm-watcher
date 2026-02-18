# Dia-Stron Arm Watcher (MVP)

A beginner-friendly Python project that watches a robotic arm with a camera and alerts you if the arm appears to stop moving for too long.

This is designed for long Dia-Stron runs in a humidity chamber where software stalls can leave the arm stuck for hours.

---

## What this project does

- Uses **OpenCV** to watch motion in a selected **ROI (Region of Interest)**.
- Reduces false positives using:
  - grayscale + blur,
  - frame differencing,
  - thresholding,
  - erosion/dilation.
- Computes a normalized **motion score** (`moving_pixels / roi_pixels`).
- Declares **FROZEN** if motion score stays below threshold for `freeze_seconds` (default 30s).
- Uses a state machine:
  - `MOVING -> FROZEN` when no motion long enough,
  - `FROZEN -> MOVING` only after stable recovery (`recover_seconds`).
- Sends alerts once, with a cooldown to avoid spam.
- Supports 2 notifier methods:
  - **SMTP Email**
  - **Pushover Push**
- Logs to `logs/monitor.log` and can save freeze evidence frames to `evidence/`.

---

## Project structure

```text
Dia-stron-Arm-watcher/
├── src/
│   ├── app.py                    # main entrypoint: python -m src.app
│   ├── config.py                 # YAML config loader
│   ├── detector.py               # motion detection logic
│   ├── state_machine.py          # freeze/recover state machine
│   ├── roi_selector.py           # mouse ROI selection
│   ├── logger_setup.py           # logging config
│   └── notifications/
│       ├── email_notifier.py     # SMTP notifier
│       └── pushover_notifier.py  # Pushover notifier
├── configs/settings.yaml         # user-tunable settings
├── tests/                        # lightweight unit tests
├── scripts/run.sh                # helper script
├── example.env                   # sample secrets template
├── requirements.txt
└── README.md
```

---

## 1) Install prerequisites (beginner step-by-step)

### A. Install Python 3.11+
- Windows: Download from https://www.python.org/downloads/ and check **"Add Python to PATH"**.
- macOS: Use python.org installer or `brew install python@3.11`.
- Linux: Use your package manager (`sudo apt install python3.11 python3.11-venv` etc.).

Check:

```bash
python --version
```

or:

```bash
python3 --version
```

### B. Install Git
- Windows: https://git-scm.com/download/win
- macOS: `brew install git` or Xcode command line tools.
- Linux: `sudo apt install git`

Check:

```bash
git --version
```

### C. Clone your repository

```bash
git clone <your-repo-url>
cd Dia-stron-Arm-watcher
```

---

## 2) Create virtual environment + install dependencies

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

If `python` command is missing, replace with `python3`.

---

## 3) Camera connection and quick verification

1. Connect your USB/IP camera.
2. Make sure no other app is locking the camera.
3. Open `configs/settings.yaml` and set:

```yaml
camera:
  index: 0
```

If camera does not open, try `1`, `2`, etc.

---

## 4) Configure secrets (.env)

1. Copy template:

```bash
cp example.env .env
```

(Windows PowerShell: `Copy-Item example.env .env`)

2. Edit `.env` and fill credentials.

### Email (SMTP)
For Gmail:
- Enable 2FA on your Google account.
- Create an **App Password**.
- Use:
  - `SMTP_HOST=smtp.gmail.com`
  - `SMTP_PORT=587`
  - app password in `SMTP_PASSWORD`

### Pushover
- Create account at pushover.net.
- Create an app to get `PUSHOVER_APP_TOKEN`.
- Find your personal `PUSHOVER_USER_KEY`.

> `.env` is ignored by git via `.gitignore`, so secrets are not committed.

---

## 5) First run and ROI setup

Run:

```bash
python -m src.app --config configs/settings.yaml
```

If `detection.roi` is `null`, the app asks you to draw ROI:
- Drag mouse over the robotic arm area.
- Press **S** to save selection for this session.
- Press **Q** to cancel.

Then main preview opens and shows:
- ROI rectangle
- motion mask overlay (optional)
- motion score
- status (`MOVING` or `FROZEN`)

Press **q** in preview to quit.

### Save ROI permanently
After selecting ROI, copy printed ROI tuple and paste into config:

```yaml
detection:
  roi: [100, 120, 500, 300]
```

Now next starts will use this ROI automatically.

---

## 6) Tune detection and freeze behavior (calibration)

Open `configs/settings.yaml` and tune these:

- `motion_threshold` (default `0.015`):
  - Lower => more sensitive (more likely motion detected)
  - Higher => less sensitive
- `freeze_seconds` (default `30`):
  - No-motion duration before alert.
- `recover_seconds` (default `2`):
  - Motion must return for this long before status becomes MOVING again.
- `min_pixel_threshold` (default `25`):
  - Pixel-difference cutoff in frame diff.
- `erode_iterations`, `dilate_iterations`:
  - Noise suppression and blob cleanup.

### Recommended beginner calibration workflow
1. Start with defaults.
2. Let arm move normally for 1–2 minutes and observe motion score range.
3. Stop movement briefly and observe low-score range.
4. Set `motion_threshold` between those ranges.
5. Set `freeze_seconds` based on your process safety tolerance.
6. Repeat until false alarms are rare.

---

## 7) Notifications behavior

When freeze is detected:
- app logs event,
- optional evidence frame is saved,
- notifications sent via enabled methods in config,
- alert is throttled by `alerts.cooldown_seconds`.

Enable methods in config:

```yaml
alerts:
  enabled_methods:
    - email
    - pushover
```

---

## 8) Logs and evidence

- Log file: `logs/monitor.log`
- Freeze snapshots: `evidence/freeze_YYYYMMDD_HHMMSS.jpg`

If you receive alert, check log + snapshot to confirm actual stall.

---

## 9) Run options

Standard run:

```bash
python -m src.app
```

Explicit config:

```bash
python -m src.app --config configs/settings.yaml
```

Script helper (macOS/Linux):

```bash
bash scripts/run.sh
```

---

## 10) Lightweight tests

Run:

```bash
pytest -q
```

Tests cover config defaults and freeze state transitions.

---

## Troubleshooting

### 1) `Could not open camera index X`
- Try different camera indexes (`0`, `1`, `2`).
- Close Zoom/Teams/other camera apps.
- Check OS camera permissions.
- Unplug/replug camera.

### 2) OpenCV window does not appear
- Run from desktop/local terminal (some remote shells cannot open GUI).
- On Linux, ensure X11/Wayland GUI session is active.
- On Windows, avoid launching from restricted service session.

### 3) No alerts are sent
- Verify `.env` exists and keys are filled.
- Check `alerts.enabled_methods` includes your notifier names.
- Inspect `logs/monitor.log` for notifier errors.

### 4) Too many false freeze alerts
- Increase `motion_threshold` slightly.
- Increase `freeze_seconds`.
- Tighten ROI to arm only.
- Increase `dilate_iterations` or adjust blur/threshold.

### 5) Motion never returns to MOVING
- Decrease `recover_seconds`.
- Reduce `motion_threshold` a little.

### 6) Dependency install fails
- Upgrade pip first:
  ```bash
  pip install --upgrade pip setuptools wheel
  ```
- Confirm Python is 3.11+.
- Recreate virtual environment and reinstall.

---

## Safety notes

- This tool is a monitoring aid; keep hardware safety interlocks in place.
- Test alerting thoroughly before overnight runs.
- Place camera securely to avoid drift in ROI.
- In humid environments, ensure camera housing/cabling are suitable.

---

## Next improvements (optional)

- Add Telegram bot notifier.
- Persist ROI from GUI directly into YAML.
- Add web dashboard for remote status.
- Add heartbeat notifications every N minutes.
