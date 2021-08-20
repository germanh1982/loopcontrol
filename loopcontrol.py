#!/usr/bin/python3
from time import sleep, monotonic
from ad5791 import AD5791
import statistics
from collections import deque
from simple_pid import PID
from argparse import ArgumentParser
import ticc
import paho.mqtt.client as mqtt
import json

class WindowFilter:
    def __init__(self, size, function):
        self.buffer = deque(maxlen=size)
        self.function = function

    def __call__(self, newsample):
        self.buffer.append(newsample)
        return self.function(self.buffer)

class DAC(AD5791):
    def set(self, x):
        self.code = x

def process_line(channel, sample):
    global last_phase

    ts = monotonic()

    if channel == 'chA':
        if last_phase is None:
            last_phase = sample
        else:
            # calculate new error signal
            # phase_residual goes to 0 when system is locked
            phase_residual = float(sample) - last_phase - 1 / cfg.ticcsps
            r = meanfilter(phase_residual)

            control = round(min(1048575, max(0, pid(r) * 1e10)))
            dac.set(control)

            report = {
                "ts": ts,
                "phase": sample,
                "phase_residual": phase_residual,
                "filter_output": r,
                "control_output": control
            }
            srv.publish("rt_report", json.dumps(report))

            last_phase = sample

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('configfile')
    args = p.parse_args()

    # load config
    with open(args.configfile) as fh:
        cfg = json.load(fh)

    # connect to mqtt server
    srv = mqtt.Client()
    srv.connect_async('localhost')
    srv.loop_start()

    # setup TICC
    comparator = ticc.TICC(process_line, cfg.ticcport, cfg.ticcbaud, timeout=0.1, rtscts=True)
    meanfilter = WindowFilter(600, statistics.mean)

    # setup DAC
    dac = DAC(cfg.dacport)
    dac.set(cfg.dacstart)

    last_phase = None

    pid = PID(cfg.kp, cfg.ki, cfg.kd, setpoint=0)

    try:
        while True:
            sleep(1 / cfg.ticcsps / 10)
            comparator()
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        log.info("Saving current configuration")
        with open(args.configfile, 'w') as fh:
            fh.write(json.dumps(cfg))
