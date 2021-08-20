import spi
import logging

class AD5791:
    DAC_REG = 0x1 << 20
    CONTROL_REG = 0x2 << 20
    CLEARCODE_REG = 0x3 << 20
    SW_CONTROL_REG = 0x4 << 20

    # Control register flags
    RBUF = 1
    OPGND = 2
    DACTRI = 3
    BIN_2SC = 4
    SDODIS = 5
    LINCOMP = 6

    READ = 23

    def __init__(self, device, speed=50000):
        self.log = logging.getLogger(__name__)
        self.dev = spi.SPI(device, speed=speed, polarity=True)
        self._writereg(self.CONTROL_REG, 1 << self.BIN_2SC)

    @property
    def code(self):
        got = self._readreg(self.DAC_REG)
        return int.from_bytes(got, 'big') & 0xfffff

    @code.setter
    def code(self, code):
        self._writereg(self.DAC_REG, code)

    def _transfer(self, value):
        t = value.to_bytes(3, 'big', signed=True)
        self.log.debug(f'Setting DAC with code {t}')
        return self.dev.transfer(t)

    def _writereg(self, reg, data):
        self._transfer(reg | data)

    def _readreg(self, reg):
        self._transfer(1 << self.READ | reg)
        return self._transfer(0x0)
