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
import logging
from math import floor

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
            phase_residual = float(sample) - last_phase - cfg['sampling_period']
            filtered = meanfilter(phase_residual) * cfg['fosc']

            control = round(pid(filtered))
            dac.set(control)

            report = {
                "ts": ts,
                "phase": sample,
                "phase_residual": phase_residual,
                "filter_output": filtered,
                "control_output": control
            }
            log.info(report)
            srv.publish("rt_report", json.dumps(report))

            last_phase = sample

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('-l', '--loglevel', choices=['debug', 'info', 'warning', 'error', 'critical'])
    p.add_argument('-c', '--config', default='loopcontrol.json')
    args = p.parse_args()

    # load config
    with open(args.config) as fh:
        cfg = json.load(fh)

    if args.loglevel is None:
        loglevel = cfg['loglevel'].upper()
    else:
        loglevel = args.loglevel.upper()

    logging.basicConfig(format='%(asctime)s %(levelname)s %(msg)s', datefmt='%Y-%m-%d %H:%M:%S', level=getattr(logging, loglevel))
    log = logging.getLogger()

    # connect to mqtt server
    srv = mqtt.Client()
    srv.connect_async('localhost')
    srv.loop_start()

    # setup DAC, do this before the ticc
    dac = DAC(cfg['dacport'])

    # setup TICC
    comparator = ticc.TICC(process_line, cfg['ticcport'], cfg['ticcbaud'], timeout=0.1, rtscts=True)
    meanfilter = WindowFilter(cfg['lpf_length'], statistics.mean)

    last_phase = None

    # set max=2^20-2 to leave one free in case the round() before the dac.set() rounds to +1
    pid = PID(cfg['gain'], cfg['reset'], cfg['rate'], setpoint=0, sample_time=cfg['sampling_period'], output_limits=(0, 1048574))

    try:
        log.info("Starting control loop")
        while True:
            sleep(cfg['sampling_period'] / 10)
            comparator()
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        log.info("Exiting")
        '''
        with open(args.config, 'w') as fh:
            fh.write(json.dumps(cfg, indent=4))
        '''
