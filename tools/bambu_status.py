#!/usr/bin/env python3
import argparse
import json
import ssl
import time
from pathlib import Path

# Uses Windows-installed paho-mqtt from system Python via powershell/cmd if needed.
# In WSL environments without paho, run with Windows Python:
#   python C:\path\to\bambu_status.py ...


def load_from_bambu_studio_conf(conf_path):
    txt = Path(conf_path).read_text(errors='ignore')
    data = json.loads(txt)
    ac = data.get('access_code', {})
    if not ac:
        raise RuntimeError('No access_code found in BambuStudio.conf')
    serial, code = next(iter(ac.items()))
    return serial, code


def read_status(ip, serial, access_code, timeout=8):
    import paho.mqtt.client as mqtt

    out = {"connected": False, "messages": [], "summary": None}

    def on_connect(client, userdata, flags, rc, properties=None):
        out["connected"] = (rc == 0)
        client.subscribe(f"device/{serial}/report", qos=0)
        req = {"pushing": {"sequence_id": "0", "command": "pushall"}}
        client.publish(f"device/{serial}/request", json.dumps(req), qos=0)

    def on_message(client, userdata, msg):
        payload = msg.payload.decode('utf-8', 'ignore')
        out["messages"].append(payload)

    client = mqtt.Client(client_id='animal_bambu_status', protocol=mqtt.MQTTv311)
    client.username_pw_set('bblp', access_code)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(ip, 8883, 10)
    client.loop_start()
    start = time.time()
    while time.time() - start < timeout and not out["messages"]:
        time.sleep(0.2)
    client.loop_stop()
    client.disconnect()

    if out["messages"]:
        try:
            j = json.loads(out["messages"][-1])
            p = j.get('print', {})
            keys = [
                'gcode_state', 'mc_percent', 'mc_remaining_time', 'nozzle_temper', 'bed_temper',
                'layer_num', 'total_layer_num', 'project_id', 'task_id', 'wifi_signal'
            ]
            out["summary"] = {k: p.get(k) for k in keys if k in p}
        except Exception:
            pass

    return out


def main():
    ap = argparse.ArgumentParser(description='Read-only Bambu printer status poll over LAN MQTT')
    ap.add_argument('--ip', required=True)
    ap.add_argument('--serial')
    ap.add_argument('--access-code')
    ap.add_argument('--conf', default='/mnt/c/Users/grant/AppData/Roaming/BambuStudio/BambuStudio.conf')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    serial = args.serial
    access_code = args.access_code

    if not serial or not access_code:
        s, c = load_from_bambu_studio_conf(args.conf)
        serial = serial or s
        access_code = access_code or c

    res = read_status(args.ip, serial, access_code)
    out = {
        'ip': args.ip,
        'serial': serial,
        'connected': res['connected'],
        'status_received': bool(res['messages']),
        'summary': res['summary'],
        'note': 'Read-only status poll; no print control commands sent.'
    }

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"Bambu status @ {out['ip']} ({out['serial']}):")
        print(f"- connected: {out['connected']}")
        print(f"- status received: {out['status_received']}")
        print(f"- summary: {out['summary']}")


if __name__ == '__main__':
    main()
