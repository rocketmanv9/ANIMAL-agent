#!/usr/bin/env python3
import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    from pywinauto import Application, Desktop
except Exception:
    Application = None
    Desktop = None

APP_NAME = "Bambu Studio"
DEFAULT_EXE = r"C:\Program Files\Bambu Studio\bambu-studio.exe"
PROJECT_DIR = Path(__file__).resolve().parent
LOG_DIR = PROJECT_DIR / "logs"
LOG_FILE = LOG_DIR / "print.log"
CONFIG_FILE = PROJECT_DIR / "config.json"


class PrintCtlError(Exception):
    pass


def load_config():
    if not CONFIG_FILE.exists():
        raise PrintCtlError(f"Missing config: {CONFIG_FILE}")
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def setup_logger(debug=False):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("printctl")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.handlers.clear()

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.DEBUG if debug else logging.INFO)
    sh.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(sh)
    return logger


def ensure_pywinauto():
    if Application is None:
        raise PrintCtlError("pywinauto not installed. Install requirements first.")


def launch_or_attach(exe_path, logger, timeout=45):
    ensure_pywinauto()
    logger.info("[1/7] Launch/attach Bambu Studio")
    try:
        app = Application(backend="uia").connect(path=exe_path)
        logger.info("Attached to running Bambu Studio")
    except Exception:
        logger.info("Launching Bambu Studio...")
        app = Application(backend="uia").start(f'"{exe_path}"')

    end = time.time() + timeout
    while time.time() < end:
        wins = Desktop(backend="uia").windows(title_re=".*Bambu.*Studio.*")
        if wins:
            win = wins[0]
            win.set_focus()
            logger.info("Bambu Studio window ready")
            return app, win
        time.sleep(1)
    raise PrintCtlError("Timed out waiting for Bambu Studio window")


def list_controls(window, logger):
    logger.info("--- DEBUG: visible controls snapshot ---")
    try:
        for c in window.descendants()[:200]:
            txt = c.window_text()
            if txt:
                logger.info(f"{c.friendly_class_name():<20} | {txt}")
    except Exception as e:
        logger.info(f"Could not dump controls: {e}")


def click_first(window, candidates, logger, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        for name in candidates:
            try:
                ctrl = window.child_window(title_re=f"^{name}$", control_type="Button")
                if ctrl.exists(timeout=0.2):
                    ctrl.click_input()
                    logger.info(f"Clicked button: {name}")
                    return True
            except Exception:
                pass
        time.sleep(0.5)
    return False


def import_model(exe_path, model_path, logger):
    logger.info("[2/7] Import STL into Bambu Studio")
    if not Path(model_path).exists():
        raise PrintCtlError(f"Model file not found: {model_path}")

    # Prefer opening file through shell with Studio association, but enforce Studio path if possible.
    subprocess.run([exe_path, str(model_path)], check=False)
    logger.info(f"Import command issued: {model_path}")
    time.sleep(3)


def apply_default_preset(window, config, logger):
    logger.info("[3/7] Apply default preset")
    # UI label text differs by version; we log intent and attempt common selectors.
    preset = config.get("default_profile", "0.2mm Standard @PLA")
    filament = config.get("filament_type", "PLA")
    logger.info(f"Target preset: {preset}")
    logger.info(f"Target filament: {filament}")

    # Best-effort click into profile dropdown areas by text.
    for text in [preset, "0.2mm", "Standard", filament, "Generic PLA"]:
        try:
            window.child_window(title_re=f".*{text}.*").click_input()
            logger.info(f"Preset/UI match clicked: {text}")
            time.sleep(0.4)
            break
        except Exception:
            continue


def slice_model(window, logger, timeout=180):
    logger.info("[4/7] Slice model")
    if not click_first(window, ["Slice plate", "Slice", "Slice all"], logger, timeout=15):
        raise PrintCtlError("Could not find Slice button")

    end = time.time() + timeout
    while time.time() < end:
        # wait until print button appears/enables as proxy for slice completion
        for name in ["Print plate", "Print", "Send"]:
            try:
                b = window.child_window(title_re=f"^{name}$", control_type="Button")
                if b.exists(timeout=0.2) and b.is_enabled():
                    logger.info("Slicing appears complete (print/send action available)")
                    return
            except Exception:
                pass
        time.sleep(1)
    raise PrintCtlError("Timed out waiting for slicing completion")


def choose_printer(window, printer_name, logger):
    logger.info("[6/7] Select target printer if needed")
    # If a printer picker appears, click desired printer text.
    try:
        picker = window.child_window(title_re=".*Printer.*|.*Device.*")
        if picker.exists(timeout=0.5):
            try:
                window.child_window(title_re=f".*{printer_name}.*").click_input()
                logger.info(f"Selected printer: {printer_name}")
            except Exception:
                logger.info("Printer picker detected, but exact selector not found. Proceeding.")
    except Exception:
        pass


def start_print(window, config, logger, timeout=45):
    logger.info("[5/7] Click Print")
    if not click_first(window, ["Print plate", "Print", "Send"], logger, timeout=15):
        raise PrintCtlError("Could not find Print button")

    choose_printer(window, config.get("printer_name", "P1S"), logger)

    # Confirm final dialog if present
    click_first(window, ["Send", "Confirm", "Start", "Print"], logger, timeout=5)

    logger.info("[7/7] Print action submitted (verify in Bambu Studio/printer status)")


def test_mode(exe_path, debug=False):
    logger = setup_logger(debug=debug)
    logger.info("Running test mode...")
    app, win = launch_or_attach(exe_path, logger)
    if debug:
        list_controls(win, logger)
    logger.info("Test OK: Bambu Studio reachable")


def run_slice(exe_path, model_path, debug=False):
    config = load_config()
    logger = setup_logger(debug=debug)
    app, win = launch_or_attach(exe_path, logger)
    import_model(exe_path, model_path, logger)
    apply_default_preset(win, config, logger)
    slice_model(win, logger)
    logger.info("Slice complete")


def run_print(exe_path, model_path, debug=False):
    config = load_config()
    logger = setup_logger(debug=debug)
    app, win = launch_or_attach(exe_path, logger)
    import_model(exe_path, model_path, logger)
    apply_default_preset(win, config, logger)
    slice_model(win, logger)
    start_print(win, config, logger)


def main():
    parser = argparse.ArgumentParser(description="Bambu Studio automation controller (Cloud Mode compatible)")
    parser.add_argument("command", choices=["print", "slice", "test"])
    parser.add_argument("file", nargs="?")
    parser.add_argument("--exe", default=os.environ.get("BAMBU_STUDIO_EXE", DEFAULT_EXE))
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    try:
        if args.command == "test":
            test_mode(args.exe, debug=args.debug)
        elif args.command == "slice":
            if not args.file:
                raise PrintCtlError("slice requires <file>")
            run_slice(args.exe, args.file, debug=args.debug)
        elif args.command == "print":
            if not args.file:
                raise PrintCtlError("print requires <file>")
            run_print(args.exe, args.file, debug=args.debug)
    except PrintCtlError as e:
        logger = setup_logger(debug=True)
        logger.error(f"ERROR: {e}")
        sys.exit(2)
    except Exception as e:
        logger = setup_logger(debug=True)
        logger.exception(f"UNHANDLED: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
