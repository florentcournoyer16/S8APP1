import cocotb
from bitarray.util import int2ba, ba2int
from cocotb.triggers import Event
from cocotb.utils import get_sim_time
from cocotb.log import SimLog

CRC8_START = 0x0D
CRC_POLY = 0xC6

class BaseModel():
    def __init__(self) -> None:
        self.current_crc = CRC8_START
        
        self._log = SimLog("cocotb.%s" % type(self).__qualname__)

    def _crc8_single_cycle(self, new_byte):
        crc = int2ba(self.current_crc, 8)
        data_bits = int2ba(new_byte, 8)
        poly = int2ba(CRC_POLY, 8)
        for j in range(7, -1, -1):
            if crc[7] != data_bits[j]:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
        return ba2int(crc)

    def crc8(self, bytes_array: bytes) -> int:
        self.current_crc = CRC8_START
        crc = bytes_array[len(bytes_array)-1]
        data = bytes_array[:len(bytes_array)-1]

        # self._log.info(f"bytes received in model = {[hex(byte) for byte in bytes_array]}")
        # self._log.info(f"data for crc = {[hex(byte) for byte in data]}")
        # self._log.info(f"crc = {[hex(crc)]}")

        for current_byte in data:
            self.current_crc = self._crc8_single_cycle(current_byte)
            # self._log.info(f"current crc = {hex(current_crc)}")
        if self.current_crc == crc:
            return 1
        return 0

    async def tdc(self, i_trig_rising: Event, i_trig_falling: Event) -> tuple[int, int]:
        pulse_width = 0
        timestamp = 0
        while pulse_width < 20*10**3:
            initial_timestamp = get_sim_time(units='ps')
            await i_trig_rising.wait()
            rising_timestamp = get_sim_time(units='ps')
            await i_trig_falling.wait()
            falling_timestamp = get_sim_time(units='ps')
            
            self._log.info("initial_timestamp = %s", initial_timestamp)
            self._log.info("rising_timestamp = %s", rising_timestamp)
            self._log.info("falling_timestamp = %s", falling_timestamp)
            
            pulse_width = (falling_timestamp - rising_timestamp)
            timestamp = initial_timestamp % 171*10**6 # 171ms max
    
            self._log.info("pulse_width = %s", pulse_width)
            self._log.info("timestamp = %s", timestamp)
            
            if pulse_width > 50*10**6:
                pulse_width = 50*10**6
        
        return (pulse_width, timestamp)
