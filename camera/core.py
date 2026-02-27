import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

CONFIG_PATH = Path('/home/grant/.openclaw/workspace/camera/config.json')


def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def detect_environment():
    os_name = platform.system()
    is_wsl = False
    if os_name == 'Linux':
        try:
            txt = Path('/proc/version').read_text(errors='ignore').lower()
            is_wsl = ('microsoft' in txt) or ('wsl' in txt)
        except Exception:
            pass
    env = {
        'os': os_name,
        'release': platform.release(),
        'is_wsl': is_wsl,
        'ffmpeg': shutil.which('ffmpeg'),
        'v4l2_ctl': shutil.which('v4l2-ctl'),
        'dev_video': sorted([f'/dev/{n}' for n in os.listdir('/dev') if n.startswith('video')]) if os.path.isdir('/dev') else [],
    }
    if os_name == 'Linux' and is_wsl:
        env['backend'] = 'wsl_no_direct_camera'
    elif os_name == 'Linux':
        env['backend'] = 'v4l2_ffmpeg'
    elif os_name == 'Darwin':
        env['backend'] = 'avfoundation_ffmpeg'
    elif os_name == 'Windows':
        env['backend'] = 'dshow_ffmpeg'
    else:
        env['backend'] = 'unknown'
    return env


def _load_cfg():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {'consent_granted': False}


def _save_cfg(cfg):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def set_consent(granted: bool):
    cfg = _load_cfg()
    cfg['consent_granted'] = bool(granted)
    _save_cfg(cfg)
    return cfg


def ensure_consent():
    cfg = _load_cfg()
    return bool(cfg.get('consent_granted', False))


def list_devices():
    env = detect_environment()
    os_name = env['os']

    if os_name == 'Linux' and env['is_wsl']:
        return {'devices': [], 'note': 'Running under WSL2: no direct /dev/video* camera access. Run on host Windows/macOS/Linux or use host-capture workaround.'}

    if os_name == 'Linux':
        devices = []
        for d in env['dev_video']:
            name = d
            info = ''
            if env['v4l2_ctl']:
                rc, out, err = _run(['v4l2-ctl', '-d', d, '--all'])
                if rc == 0:
                    for line in out.splitlines():
                        if 'Card type' in line or 'Driver name' in line:
                            info += line.strip() + '; '
            devices.append({'id': d, 'name': name, 'info': info.strip('; ')})
        return {'devices': devices}

    if os_name == 'Darwin':
        if not env['ffmpeg']:
            return {'devices': [], 'error': 'ffmpeg not found'}
        rc, out, err = _run(['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''])
        text = out + '\n' + err
        lines = [l for l in text.splitlines() if 'AVFoundation video devices' in l or '[0]' in l or '[1]' in l or 'video devices' in l]
        return {'devices_raw': lines}

    if os_name == 'Windows':
        ffmpeg = env['ffmpeg'] or shutil.which('ffmpeg.exe')
        if not ffmpeg:
            return {'devices': [], 'error': 'ffmpeg not found in PATH'}
        rc, out, err = _run([ffmpeg, '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'])
        text = out + '\n' + err
        lines = [l for l in text.splitlines() if 'DirectShow video devices' in l or '"' in l]
        return {'devices_raw': lines}

    return {'devices': [], 'error': f'Unsupported OS: {os_name}'}


def _ffmpeg_capture_cmd(device: str, output_path: str):
    env = detect_environment()
    os_name = env['os']
    if os_name == 'Linux':
        return ['ffmpeg', '-y', '-f', 'v4l2', '-i', device or '/dev/video0', '-frames:v', '1', output_path]
    if os_name == 'Darwin':
        return ['ffmpeg', '-y', '-f', 'avfoundation', '-i', f'{device or "0"}:none', '-frames:v', '1', output_path]
    if os_name == 'Windows':
        return ['ffmpeg', '-y', '-f', 'dshow', '-i', f'video={device}', '-frames:v', '1', output_path]
    raise RuntimeError('Unsupported OS')


def capture_image(output_path, device=None, timeout=20):
    if not ensure_consent():
        raise PermissionError('Camera consent not granted. Run consent command first.')
    env = detect_environment()
    if env['os'] == 'Linux' and env['is_wsl']:
        raise RuntimeError('WSL2 cannot access laptop camera directly. Run camera command on host OS.')
    if not env['ffmpeg']:
        raise RuntimeError('ffmpeg not installed')
    cmd = _ffmpeg_capture_cmd(device, output_path)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return {'ok': True, 'output': output_path}


def record_clip(output_path, seconds=5, device=None, timeout=30):
    if not ensure_consent():
        raise PermissionError('Camera consent not granted. Run consent command first.')
    env = detect_environment()
    if env['os'] == 'Linux' and env['is_wsl']:
        raise RuntimeError('WSL2 cannot access laptop camera directly. Run camera command on host OS.')
    if not env['ffmpeg']:
        raise RuntimeError('ffmpeg not installed')
    os_name = env['os']
    if os_name == 'Linux':
        cmd = ['ffmpeg', '-y', '-f', 'v4l2', '-i', device or '/dev/video0', '-t', str(seconds), output_path]
    elif os_name == 'Darwin':
        cmd = ['ffmpeg', '-y', '-f', 'avfoundation', '-i', f'{device or "0"}:none', '-t', str(seconds), output_path]
    elif os_name == 'Windows':
        cmd = ['ffmpeg', '-y', '-f', 'dshow', '-i', f'video={device}', '-t', str(seconds), output_path]
    else:
        raise RuntimeError('Unsupported OS')
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return {'ok': True, 'output': output_path, 'seconds': seconds}


def who_is_using(device='/dev/video0'):
    env = detect_environment()
    os_name = env['os']
    if os_name == 'Linux' and env['is_wsl']:
        return {'note': 'WSL2: cannot directly inspect host camera handles.'}
    if os_name == 'Linux':
        out = {}
        for cmd, key in [(['fuser', '-v', device], 'fuser'), (['lsof', device], 'lsof')]:
            if shutil.which(cmd[0]):
                rc, so, se = _run(cmd)
                out[key] = {'rc': rc, 'stdout': so, 'stderr': se}
        return out
    if os_name == 'Darwin':
        if shutil.which('lsof'):
            rc, so, se = _run(['lsof'])
            raw = '\n'.join([ln for ln in so.splitlines() if 'camera' in ln.lower() or 'avfoundation' in ln.lower()][:200])
            return {'note': 'macOS camera process detection is best-effort', 'lsof_filtered': raw}
        return {'note': 'lsof not available'}
    if os_name == 'Windows':
        return {'note': 'Windows does not expose reliable per-process webcam handle via standard CLI. Use Process Explorer/Handle for deep inspection.'}
    return {'note': 'Unsupported OS'}
