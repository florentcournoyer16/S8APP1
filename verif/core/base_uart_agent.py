from dataclasses import dataclass, field
from enum import Enum
from cocotbext.uart import UartSource, UartSink
from cocotb.handle import ModifiableObject
from typing import Optional, Union
from cocotb import start
from cocotb import Coroutine
from cocotb.binary import BinaryValue
from bitarray.util import int2ba, ba2int
from cocotb.triggers import ClockCycles
from cocotb.log import SimLog
from uart_packets import UartRxPckt, UartTxPckt, UartTxCmd, RegAddr, UartConfig, UartRxType
from cocotb.triggers import Event
from cocotb.queue import Queue

class TDCChannel(Enum):
    CHAN0 = 0x0
    CHAN1 = 0x1

CRC8_START = 0x0D
CRC_POLY = 0xC6

class BaseUartAgent:
    def __init__(
        self,
        uart_config: UartConfig,
    ):
        self.uart_config = uart_config
        self._uart_source: Optional[UartSource] = None
        self._uart_sink: Optional[UartSink] = None
        self._dut_clk: Optional[ModifiableObject] = None
        self._log = SimLog("cocotb.%s" % type(self).__qualname__)
        self.test_is_running = 1
        self.tdc_events: Queue[UartRxPckt] = Queue()
        self.reg_events: Queue[UartRxPckt] = Queue()


    @property
    def uart_config(self) -> UartConfig:
        if self._uart_config is None:
            raise ValueError("property uart_config is not initialized")
        return self._uart_config

    @uart_config.setter
    def uart_config(self, uart_config: UartConfig) -> None:
        if not isinstance(uart_config, UartConfig):
            raise TypeError("property uart_config must be of type UartConfig")
        self._uart_config = uart_config

    def _calc_crc8(self, bytes_array: bytes) -> int:
        current_crc = CRC8_START
        for byte in bytes_array:
            crc = int2ba(current_crc, 8)
            data_bits = int2ba(byte, 8)
            poly = int2ba(CRC_POLY, 8)
            for j in range(7, -1, -1):
                if crc[7] != data_bits[j]:
                    crc = (crc >> 1) ^ poly
                else:
                    crc >>= 1
            current_crc = ba2int(crc)
        return current_crc

    def attach(self, in_sig: ModifiableObject, out_sig: ModifiableObject, dut_clk: ModifiableObject) -> None:
        self._uart_source = UartSource(
            data=in_sig,
            baud=self.uart_config.baud_rate,
            bits=self.uart_config.frame_size,
        )
        self._uart_sink = UartSink(
            data=out_sig,
            baud=self.uart_config.baud_rate,
            bits=self.uart_config.frame_size,
        )
        self._dut_clk = dut_clk

    async def transaction(self, cmd: UartTxCmd, addr: RegAddr, data: int = 0, timeout_cycles: int = 1000, retries: int = 60) -> UartRxPckt:
        response: Coroutine = await start(self._wait_for_response(timeout_cycles, retries))

        tx_pkt: BinaryValue = UartTxPckt(
            cmd=cmd,
            addr=addr,
            data=data,
            uart_config=self.uart_config
        )
        self._log.info("Preparing to send message:")
        tx_pkt.log_pkt()

        await self._uart_source.write(tx_pkt.buff)
        await self._uart_source.wait()

        raw_crc8 = self._calc_crc8(tx_pkt.buff)
        crc8_pkt = BinaryValue(
            value=raw_crc8,
            n_bits=self._uart_config.frame_size,
            bigEndian=self._uart_config.big_endian
        )
        await self._uart_source.write(crc8_pkt.buff)
        # self._uart_source.clear()
        # self._uart_sink.clear()
        rx_pkt: UartRxPckt = await response
        return rx_pkt

    async def _wait_for_response(self, timeout_cycles: int, retries: int) -> Union[UartRxPckt, None]:
        try_counter = 1
        while (try_counter < retries) and (self.reg_events.qsize() < 1):
            await ClockCycles(self._dut_clk, timeout_cycles, rising=True)
            try_counter += 1

        if try_counter == retries:
            self._log.error(
                "Timeout after a wait of %d clock cycles",
                int(timeout_cycles * retries)
            )
            return None
            # raise RuntimeError("Timeout after a wait of %d clock cycles", int(timeout_cycles * retries)")

        self._log.info("After a wait of %s clock cycles, received message:", str(timeout_cycles * try_counter))

        return await self.reg_events.get()

    async def listen_tdc(self, channel: TDCChannel) -> tuple[UartRxPckt, UartRxPckt]:
        response: Coroutine = await start(self._wait_for_tdc())
        rx_pkts: tuple[UartRxPckt] = await response
        return rx_pkts

    async def _wait_for_tdc(self, timeout_cycles: int = 1000, num_of_events = 1) -> list[UartRxPckt]:
        pkts: list[UartRxPckt] = []
        try_counter = 1
        while (len(pkts) < num_of_events):
            if(self.tdc_events.qsize() > 0):
                pkts.append(await self.tdc_events.get())
            await ClockCycles(self._dut_clk, timeout_cycles, rising=True)
            try_counter += 1

        self._log.info("After a wait of %s clock cycles, received message:", str(timeout_cycles * try_counter))

        return pkts

    async def sink_uart(self, timeout_cycles: int = 1000):
        nb_bytes_expected = int(self.uart_config.packet_size / self._uart_config.frame_size + 1)
        while(self.test_is_running):
            while (self._uart_sink.count() < nb_bytes_expected):
                await ClockCycles(self._dut_clk, timeout_cycles, rising=True)

            pkt_bytes = bytes(await self._uart_sink.read(count=int(self.uart_config.packet_size / self._uart_config.frame_size)))
            await self._uart_sink.read(count=1) # crc8 byte
            pkt: UartRxPckt = UartRxPckt(
                rx_pkt_bytes=pkt_bytes,
                uart_config=self.uart_config
            )

            if(pkt.type == UartRxType.EVENT):
                await self.tdc_events.put(pkt)
            elif(pkt.type == UartRxType.ACK_READ):
                await self.reg_events.put(pkt)
                self._log.info("ACK_READ received")
            elif(pkt.type == UartRxType.ACK_WRITE):
                await self.reg_events.put(pkt)
                self._log.info("ACK_WRITE received")
            elif(pkt.type == UartRxType.NACK):
                await self.reg_events.put(pkt)
                self._log.info("NACK received")
            else:
                await self.reg_events.put(pkt)

            pkt.log_pkt()