#!/usr/bin/env python3
import argparse, json, ssl, time
import paho.mqtt.client as mqtt

IP='192.168.0.111'
SERIAL='01P00C5B0403147'
ACCESS='17545644'


def set_light(mode: str):
    msgs=[]
    def on_connect(c,u,f,rc,properties=None):
        c.subscribe(f'device/{SERIAL}/report', qos=0)
        cmd={"system":{"sequence_id":"9801","command":"ledctrl","led_node":"chamber_light","led_mode":mode}}
        c.publish(f'device/{SERIAL}/request', json.dumps(cmd), qos=0)
        c.publish(f'device/{SERIAL}/request', json.dumps({"pushing":{"sequence_id":"9802","command":"pushall"}}), qos=0)
    def on_message(c,u,m):
        msgs.append(m.payload.decode('utf-8','ignore'))

    c=mqtt.Client(client_id=f'animal_light_{mode}', protocol=mqtt.MQTTv311)
    c.username_pw_set('bblp',ACCESS)
    c.tls_set(cert_reqs=ssl.CERT_NONE)
    c.tls_insecure_set(True)
    c.on_connect=on_connect
    c.on_message=on_message
    c.connect(IP,8883,10)
    c.loop_start(); time.sleep(3); c.loop_stop(); c.disconnect()

    final='unknown'
    for p in reversed(msgs):
        if 'lights_report' in p:
            try:
                j=json.loads(p)
                lr=j.get('print',{}).get('lights_report',[])
                for item in lr:
                    if item.get('node')=='chamber_light':
                        final=item.get('mode','unknown')
                        break
                break
            except Exception:
                pass
    print(final)


if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['on','off'], required=True)
    args=ap.parse_args()
    set_light(args.mode)
