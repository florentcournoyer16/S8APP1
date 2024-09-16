from enum import Enum
from typing import Union, Optional, Tuple
from bitarray.util import int2ba, ba2int
from cocotb.triggers import Event, Timer, First
from cocotb.utils import get_sim_time
from cocotb.log import SimLog

CRC8_START = 0x0D
CRC_POLY = 0xC6

class RegAddr(Enum):
    DATA_MODE = 0x00            # RW
    BIAS_MODE = 0x01            # RW
    EN_COUNT_RATE = 0x02        # RW
    EN_EVENT_COUNT_RATE = 0x03  # RW
    TDC_THRESH = 0x04           # RW
    SRC_SEL = 0x05              # RW
    SYNC_FLAG_ERR = 0x06        # R
    CLEAR_SYNC_FLAG = 0x07      # W
    CHANNEL_EN_BITS = 0x08      # RW
    PRODUCT_VER_ID = 0x09       # R

class BaseModel():
    def __init__(self) -> None:
        self._current_crc = CRC8_START
        self._register_bank = {
            "0x0": 0x00000000,  # RW
            "0x1": 0x00000000,  # RW
            "0x2": 0x00000000,  # RW
            "0x3": 0x00000000,  # RW
            "0x4": 0x00000000,  # RW
            "0x5": 0x00000000,  # RW
            "0x6": 0x00000000,  # R
            "0x7": 0x00000000,  # W
            "0x8": 0x00000000,  # RW
            "0x9": 0xBADEFACE,  # R
        }
        self._read_data = 0
        
        self._log = SimLog("cocotb.%s" % type(self).__qualname__)

    def _crc8_single_cycle(self, new_byte):
        crc = int2ba(self._current_crc, 8)
        data_bits = int2ba(new_byte, 8)
        poly = int2ba(CRC_POLY, 8)
        for j in range(7, -1, -1):
            if crc[7] != data_bits[j]:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
        return ba2int(crc)

    def crc8(self, bytes_array: bytes) -> int:
        self._current_crc = CRC8_START
        crc = bytes_array[len(bytes_array)-1]
        data = bytes_array[:len(bytes_array)-1]

        # self._log.info(f"bytes received in model = {[hex(byte) for byte in bytes_array]}")
        # self._log.info(f"data for crc = {[hex(byte) for byte in data]}")
        # self._log.info(f"crc = {[hex(crc)]}")

        for current_byte in data:
            self._current_crc = self._crc8_single_cycle(current_byte)
            # self._log.info(f"current crc = {hex(current_crc)}")
        if self._current_crc == crc:
            return 1
        return 0

    async def tdc(self, i_trig_rising: Event, i_trig_falling: Event) -> tuple[int, int]:
        while True:
            await i_trig_rising.wait()
            rising_timestamp = get_sim_time(units='ps')
            return await self._tdc_falling_edge_monitoring(
                rising_timestamp=rising_timestamp,
                i_trig_rising=i_trig_rising,
                i_trig_falling=i_trig_falling
            )

    async def _tdc_falling_edge_monitoring(self, rising_timestamp: int, i_trig_rising: Event, i_trig_falling: Event) -> tuple[int, int]:
        await i_trig_falling.wait()
        falling_timestamp = get_sim_time(units='ps')

        pulse_width = falling_timestamp - rising_timestamp
        if pulse_width < 20*10**3:
            self._log.info("20ns or less glitch detected")
            return await self.tdc(
                i_trig_rising=i_trig_rising,
                i_trig_falling=i_trig_falling
            )

        timeout_or_rise: Optional[Union[Timer, Event]] = await First(Timer(19, units='ns'), i_trig_rising.wait())

        # If we waited for 20ns
        if isinstance(timeout_or_rise, Timer):

            timestamp = rising_timestamp % (40 * (2 ** 32))  # Wrap timestamps @ 171ms

            # Cap pulse width to 50us
            if pulse_width > 50 * 10 ** 6:
                pulse_width = 50 * 10 ** 6

            #self._log.info("initial_timestamp = %s", initial_timestamp)
            #self._log.info("rising_timestamp = %s", rising_timestamp)
            #self._log.info("falling_timestamp = %s", falling_timestamp)

            #self._log.info("pulse_width = %s", pulse_width)
            #self._log.info("timestamp = %s", timestamp)

            return (int(pulse_width / 40), int(timestamp / 40))
        else:
            self._log.info("20ns or less glitch detected")
            return await self._tdc_falling_edge_monitoring(
                rising_timestamp=rising_timestamp,
                i_trig_rising=i_trig_rising,
                i_trig_falling=i_trig_falling
            )
    
    def register_bank(self, read_enable: int, write_enable: int, address: int, write_data: int = 0) -> Tuple[int, int]:
        address = RegAddr(address)
        if read_enable == 1 and write_enable == 0:
            return self._handle_read(address=address)
        elif write_enable == 1 and read_enable == 0:
            return self._handle_write(address=address, write_data=write_data)
        else:
            raise ValueError('read_enable and write_enable cannot be equal')
            
    def _handle_read(self, address: RegAddr) -> Tuple[int, int]:
        write_ack = 0
        if address not in [RegAddr.CLEAR_SYNC_FLAG]:
            self._read_data = self._register_bank[hex(address.value)]
        return (write_ack, self._read_data)
    
    def _handle_write(self, address: RegAddr,  write_data: int):
        write_ack = 0
        if address in [RegAddr.TDC_THRESH]:
            self._register_bank[hex(address.value)] = write_data
            write_ack = 1
        if address in [RegAddr.EN_COUNT_RATE, RegAddr.EN_EVENT_COUNT_RATE, RegAddr.SRC_SEL, RegAddr.CLEAR_SYNC_FLAG]:
            self._register_bank[hex(address.value)] = write_data & 0x00000001
            write_ack = 1
        if address in [RegAddr.DATA_MODE, RegAddr.BIAS_MODE]:
            self._register_bank[hex(address.value)] = write_data & 0x00000003
            write_ack = 1
        if address in [RegAddr.CHANNEL_EN_BITS]:
            self._register_bank[hex(address.value)] = write_data & 0x0000FFFF
            write_ack = 1
        if address in [RegAddr.SYNC_FLAG_ERR, RegAddr.PRODUCT_VER_ID]:
            write_ack = 1
        return (write_ack, self._read_data)
