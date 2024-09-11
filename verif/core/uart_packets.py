from dataclasses import dataclass, field
from cocotb.binary import BinaryValue
from base_uart_agent import UartConfig
from cocotb.log import SimLog
from enum import Enum
from logging import Logger

class UartTxCmd(Enum):
    READ = 0x0
    WRITE = 0x1
    
class RegAddr(Enum):
    DATA_MODE = 0x00  # RW
    BIAS_MODE = 0x01  # RW
    EN_COUNT_RATE = 0x02  # RW
    EN_EVENT_COUNT_RATE = 0x03  # RW
    TDC_THRESH = 0x04  # RW
    SRC_SEL = 0x05  # RW
    SYNC_FLAG_ERR = 0x06  # R
    CLEAR_SYNC_FLAG = 0x07  # W
    CHANNEL_EN_BITS = 0x08  # RW
    PRODUCT_VER_ID = 0x09  # R

@dataclass
class UartTxPktStruct:
    cmd_pos: tuple[int, int] = field(default_factory=lambda: (43, 48))
    res_pos: tuple[int, int] = field(default_factory=lambda: (40, 43))
    addr_pos: tuple[int, int] = field(default_factory=lambda: (32, 40))
    data_pos: tuple[int, int] = field(default_factory=lambda: (0, 32))

class UartTxPckt(BinaryValue):
    def __init__(self, cmd: UartTxCmd, addr: RegAddr, data: int, uart_config: UartConfig):
        self.cmd: UartTxCmd = cmd
        self.addr: RegAddr = addr
        self.data: int = data
        self.uart_config: UartConfig = uart_config
        self.message: int = (
            (cmd.value << self.uart_config.cmd_pos[0])
            + (addr.value << self.uart_config.addr_pos[0])
            + (data << self.uart_config.data_pos[0])
        )
        super(UartTxPckt, self).__init__(
            value=self.message,
            n_bits=self.uart_config.packet_size,
            bigEndian=self.uart_config.endianness,
        )
        self._log: Logger = SimLog("cocotb.%s", (type(self).__qualname__))

    def log_pkt(self) -> None:
        self._log.info("CMD: %s", self.cmd)
        self._log.info("RES: %s", "0x0")
        self._log.info("ADDR: %s", self.addr)
        self._log.info("DATA: %s", hex(self.data))


class UartRxType(Enum):
    NACK = 0x0
    ACK_READ = 0x1
    ACK_WRITE = 0x2
    EVENT = 0x3

@dataclass
class UartRxPktStruct:
    type_pos: tuple[int, int] = field(default_factory=lambda: (43, 48))
    res1_pos: tuple[int, int] = field(default_factory=lambda: (40, 43))
    num_pos: tuple[int, int] = field(default_factory=lambda: (32, 40))
    chan_pos: tuple[int, int] = field(default_factory=lambda: (0, 32))
    res0_pos: tuple[int, int] = field(default_factory=lambda: (40, 43))
    data_pos: tuple[int, int] = field(default_factory=lambda: (40, 43))


class UartRxPckt(BinaryValue):
    def __init__(self, rx_pkt_bytes: bytes, uart_config: UartConfig):
        self.uart_config: UartConfig = uart_config
        super().__init__(
            value=rx_pkt_bytes.value,
            n_bits=self.uart_config.packet_size,
            bigEndian=self.uart_config.big_endian
        )
        pkt_str = self.binstr[::-1]

        type_start, type_end = self.uart_config.rx_pkt_struct.type_pos
        res1_start, res1_end = self.uart_config.rx_pkt_struct.res1_pos
        num_start, num_end = self.uart_config.rx_pkt_struct.num_pos
        chan_start, chan_end = self.uart_config.rx_pkt_struct.chan_pos
        res0_start, res0_end = self.uart_config.rx_pkt_struct.res0_pos
        data_start, data_end = self.uart_config.rx_pkt_struct.chan_pos

        self.type: UartRxType = UartRxType(int(pkt_str[type_start:type_end][::-1], 2))
        self.res1: str = hex(int(pkt_str[res1_start:res1_end][::-1], 2))
        self.num: str = hex(int(pkt_str[num_start:num_end][::-1], 2))
        self.chan: str = hex(int(pkt_str[chan_start:chan_end][::-1], 2))
        self.res0: str = hex(int(pkt_str[res0_start:res0_end][::-1], 2))
        self.data: str = hex(int(pkt_str[data_start:data_end][::-1], 2))
        self._log: Logger = SimLog("cocotb.%s",  (type(self).__qualname__))

    def log_pkt(self):
        self._log.info("TYPE: %s", self.type)
        self._log.info("RES1: %s", self.res1)
        self._log.info("NUM: %s", self.num)
        self._log.info("CHAN: %s", self.chan)
        self._log.info("RES0: %s", self.res0)
        self._log.info("DATA: %s", self.data)
