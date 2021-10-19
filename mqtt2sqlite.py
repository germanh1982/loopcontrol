#!/usr/bin/env python3
import paho.mqtt.client as mqttc
import sqlite3
import argparse
import json
from time import sleep

def msgreceive(client, userdata, msg):
    try:
        js = json.loads(msg.payload)
    except json.decoder.JSONDecodeError as e:
        print(f"JSON parse error: {msg.payload}")
        return

    try:
        dat = js['ts'], js['phase'], js['phase_residual'], js['filter_output'], js['control_output']
    except TypeError:
        print(f"Received non-dict JSON: {js}")
        return
    except KeyError as e:
        print(f"Missing JSON key: {e.args[0]}")
        return

    db.execute("INSERT INTO samples (ts, phase, phase_residual, filter_output, control_output) VALUES (?, ?, ?, ?, ?)", dat)

def on_connect(client, userdata, flags, rc):
    client.subscribe('rt_report')

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('--loglevel', choices=['debug', 'info', 'warning', 'error', 'critical'])
    p.add_argument('file')
    args = p.parse_args()

    db = sqlite3.connect(args.file)
    db.execute("CREATE TABLE IF NOT EXISTS samples (ts REAL NOT NULL, phase REAL NOT NULL, phase_residual REAL NOT NULL, filter_output REAL NOT NULL, control_output INTEGER NOT NULL)")
    db.commit()

    srv = mqttc.Client()
    srv.message_callback_add('rt_report', msgreceive)
    srv.on_connect = on_connect
    srv.connect('localhost')

    try:
        srv.loop_forever()
    except KeyboardInterrupt:
        db.commit()

