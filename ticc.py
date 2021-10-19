from serial import Serial
import re
from time import sleep

class TICC(Serial):
    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buf = b''
        self.callback = callback
        #self.dtr = False
        self.dtr = True
        sleep(0.1)
        l = self.read(self.in_waiting)
        self.line_re = re.compile('(\d+\.\d+) (chA|chB)')

    def __call__(self):
        r = self.read(2048)
        if len(r) > 0:
            self.buf += r
            while True:
                # fetch buffer contents and split input lines
                end = self.buf.find(b'\n')
                if end == -1:
                    break
                line = self.buf[:end + 1].decode().rstrip()
                self.buf = self.buf[end + 1:]

                # filter interesting lines
                m = self.line_re.match(line)
                if m:
                    phase, channel = m.groups()
                    self.callback(channel, float(phase))
