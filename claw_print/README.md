# Bambu Studio Cloud-Mode Automation (P1S)

## Mission
Automate slicing + print submission through **Bambu Studio desktop UI** while keeping printer in **Cloud Mode** (Bambu Handy remains functional).

---

## Phase 1 — Audit (completed)

- Windows: **Windows 11 Home 10.0.26200 (64-bit)**
- Python: **3.12.10**
- Bambu Studio executable: **`C:\Program Files\Bambu Studio\bambu-studio.exe`**
- Automation stack selected: **pywinauto (UIAutomation backend)**
  - Reason: stable element-based targeting without hardcoded screen coordinates
  - Fallback if selectors drift: inspect controls in `--debug` mode and update selector list

### Structured automation plan
1. Attach/launch Bambu Studio window via UIA.
2. Import STL by invoking Studio with file path.
3. Apply default preset (best-effort selector matching for profile/filament).
4. Trigger slicing via Slice button selector set.
5. Wait for slice completion by detecting enabled Print/Send control.
6. Trigger Print and printer selection flow.
7. Log every step + failures to `logs/print.log`.

---

## Project structure

`C:\claw_print\`
- `printctl.py`
- `config.json`
- `requirements.txt`
- `logs\`
- `README.md`

---

## Setup

Open **Windows PowerShell**:

```powershell
cd C:\claw_print
py -m pip install -r requirements.txt
```

---

## Commands

```powershell
python printctl.py test
python printctl.py slice path\to\file.stl
python printctl.py print path\to\file.stl
```

Optional debug mode:

```powershell
python printctl.py test --debug
python printctl.py print path\to\file.stl --debug
```

---

## Reliability safeguards included

- Window detection timeout
- Selector retries and button candidate lists
- Slice completion timeout
- Structured error codes / clear exceptions
- Action logging to `logs/print.log`

---

## Debug mode behavior

`--debug` prints a snapshot of visible UI controls (text/class names), useful when Bambu Studio updates UI labels.

If selectors break after an update:
1. Run `python printctl.py test --debug`
2. Identify updated label text
3. Update candidate lists in `click_first()` and preset matching list

---

## Example test run output

```text
Running test mode...
[1/7] Launch/attach Bambu Studio
Attached to running Bambu Studio
Bambu Studio window ready
Test OK: Bambu Studio reachable
```

---

## OpenClaw tool registration (example)

Add to your tools policy/runbook (e.g., `TOOLS.md`) something like:

- `C:\claw_print\printctl.py` — Bambu Studio UI automation (cloud-mode compatible) for `test/slice/print`.

You can then invoke from terminal/tooling:

```bash
python /mnt/c/claw_print/printctl.py test
python /mnt/c/claw_print/printctl.py print /mnt/c/path/to/model.stl
```

---

## Constraints respected

- No LAN-only requirement
- No hardcoded pixel coordinates
- No credential storage in script
- No network/printer-mode changes
