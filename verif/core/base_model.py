import cocotb
from bitarray.util import int2ba, ba2int

CRC8_START = 0x0D
CRC_POLY = 0xC6

class BaseModel():
    def __init__(self) -> None:
        self.current_crc = CRC8_START

    def _CRC8_single_cycle(self, new_byte):
        crc = int2ba(self.current_crc, 8)
        data_bits = int2ba(new_byte, 8)
        poly = int2ba(CRC_POLY, 8)
        for j in range(7, -1, -1):
            if crc[7] != data_bits[j]:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
        return ba2int(crc)

    def CRC8(self, bytes_array: bytes) -> int:
        self.current_crc = CRC8_START
        crc = bytes_array[len(bytes_array)-1]
        data = bytes_array[:len(bytes_array)-1]

        # self._log.info(f"bytes received in model = {[hex(byte) for byte in bytes_array]}")
        # self._log.info(f"data for crc = {[hex(byte) for byte in data]}")
        # self._log.info(f"crc = {[hex(crc)]}")

        for current_byte in data:
            self.current_crc = self._CRC8_single_cycle(current_byte)
            # self._log.info(f"current crc = {hex(current_crc)}")
        if self.current_crc == crc:
            return 1
        return 0
