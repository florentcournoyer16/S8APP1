
from bitarray.util import int2ba, ba2int


def prepare_data(command, addr, data):
    data_sent = (command << 43) + (addr << 32) + data
    return data_sent

"""
CRC utility
Usage example
    data = prepare_data(0, 9, 0x345678)  # Reading reg at address 0
    some_bytes = data.to_bytes(6, sys.byteorder)
    resultingCRC = get_expected_crc(some_bytes)
    my_bytearray = bytearray(some_bytes)
    my_bytearray.append(resultingCRC)
    await uart_source.write(my_bytearray)
"""

CRC8_START = 0x0D
CRC_POLY = 0xC6

def get_bit(value, idx):
    val = 0x01
    return ((value & (val << idx)) != 0)


def calculateCRC8(data, current_crc):
    crc = int2ba(current_crc, 8)
    data_bits = int2ba(data, 8)
    poly = int2ba(CRC_POLY, 8)
    for j in range(7, -1, -1):
        if crc[7] != data_bits[j]:
            crc = (crc >> 1) ^ poly
        else:
            crc >>= 1
    return ba2int(crc)


def get_expected_crc(value):
    current_crc = CRC8_START
    print(value)
    for b in value:
        current_crc = calculateCRC8(b, current_crc)

    return current_crc