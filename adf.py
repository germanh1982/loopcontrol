import spi
from time import sleep

class spidev(spi.SPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def write(self, value):
        bytevalue = value.to_bytes(4, 'big')
        print('Will write [{}]'.format(' '.join([f'{x:02X}' for x in bytevalue])))
        super().write(bytevalue)

def main():
    dev = spidev("/dev/spidev0.0")
    dev.mode = dev.MODE_0
    dev.bits_per_word = 8
    dev.speed = 250000

    # Set R13
    dev.write(0xd)
    # Set R12
    dev.write(0x15fc)
    # Set R11
    dev.write(0x61200b)
    # Set R10
    dev.write(0xc0067a)
    # Set R9
    dev.write(0x7047cc9)
    # Set R8
    dev.write(0x15596568)
    # Set R7
    dev.write(0x60000e7)
    # Set R6
    dev.write(0x35008076)
    # Set R5
    dev.write(0x800025)
    # Set R4
    dev.write(0x30008b84)
    # Set R3
    dev.write(0x3)
    # Set R2
    dev.write(0x12)
    # Set R1
    dev.write(0x1)
    # Wait 16 ADC cycles
    sleep(1/98039 * 16)
    # Set R0
    dev.write(0x302a80)

if __name__ == "__main__":
    main()
