from dataclasses import dataclass
from cocotbext.uart import UartSource, UartSink
from cocotb.handle import ModifiableObject, HierarchyObject
from typing import Tuple, Optional
from cocotb.clock import Clock


@dataclass
class UartConfig:
    baud_rate: int = 9600
    packet_size: int = 8
    endian: bool = False


class UartAgent:
    def __init__(
        self,
        uart_config: UartConfig,
    ):
        self.uart_config = uart_config
        self.uart_source: Optional[UartSource] = None
        self.uart_sink: Optional[UartSink] = None
        self.dut_clk: Optional[Clock] = None

    @property
    def uart_config(self) -> UartConfig:
        if self._uart_config is None:
            raise ValueError("property uart_config is not initialized")
        return self._uart_config

    @uart_config.setter
    def uart_config(self, uart_config):
        if not isinstance(uart_config, UartConfig):
            raise ValueError("property uart_config must be of type UartConfig")
        self._uart_config = uart_config

    @property
    def uart_source(self) -> UartConfig:
        if self._uart_source is None:
            raise ValueError("property uart_source is not initialized")
        return self._uart_source

    @uart_source.setter
    def uart_source(self, uart_source):
        if not isinstance(uart_source, UartSource):
            raise ValueError("property uart_source must be of type UartSource")
        self._uart_source = uart_source

    @property
    def uart_sink(self) -> UartSink:
        if self._uart_sink is None:
            raise ValueError("property uart_sink is not initialized")
        return self._uart_sink

    @uart_sink.setter
    def uart_sink(self, uart_sink):
        if not isinstance(uart_sink, UartSink):
            raise ValueError("property uart_sink must be of type UartSink")
        self._uart_sink = uart_sink

    @property
    def dut_clk(self) -> Clock:
        if self._dut_clk is None:
            raise ValueError("property dut_clk is not initialized")
        return self._dut_clk

    @dut_clk.setter
    def dut_clk(self, dut_clk):
        if not isinstance(dut_clk, UartSink):
            raise ValueError("property dut_clk must be of type Clock")
        self._dut_clk = dut_clk

    def attach(self, in_sig: ModifiableObject, out_sig: ModifiableObject, clk: Clock):
        self.uart_source = UartSource(
            data=in_sig,
            baud=self.uart_config.baud_rate,
            bits=self.uart_config.packet_size,
        )
        self.uart_sink = UartSink(
            data=out_sig,
            baud=self.uart_config.baud_rate,
            bits=self.uart_config.packet_size,
        )
        self._dut_clk = clk

    def write(self, wait=1000):
        pass
