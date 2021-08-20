from ad5791 import AD5791
from argparse import ArgumentParser
import logging

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('value', type=int)
    args = p.parse_args()

    logging.basicConfig()

    dac = AD5791('/dev/spidev0.0')
    dac.code = args.value
