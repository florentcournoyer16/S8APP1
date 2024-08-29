import pydevd_pycharm

from dataclasses import dataclass, field
from typing import Any, Union, List, Optional
from logging import Logger
from os import environ
from cocotbext.uart import UartSource, UartSink
from cocotb import test
from cocotb.clock import Clock
from cocotb.handle import ModifiableObject, HierarchyObject
from cocotb.log import SimLog
from uart_agent import UartAgent, UartConfig


@dataclass
class DutConfig:
    reset: int = 0
    clk: int = 10
    clk_units = "ns"
    in_sig: int = 0
    reset_cyclic: int = 0
    sipms: List[int] = field(default_factory=lambda: [0, 0])
    clk_MHz: bool = 0


class TestInterface:
    def __init__(
        self, dut: HierarchyObject, dut_config: DutConfig, uart_config: UartConfig
    ):
        self.__logger__: Logger = SimLog("cocotb.Test")
        self.__dut__: HierarchyObject = dut
        self.dut_config: DutConfig = dut_config
        self.uart_agent: UartAgent = UartAgent(uart_config)

    @property
    def dut_config(self) -> DutConfig:
        if self._dut_config is None:
            raise ValueError("property dut_config is not initialized")
        return self._dut_config

    @dut_config.setter
    def dut_config(self, dut_config: DutConfig) -> None:
        if not isinstance(dut_config, DutConfig):
            raise ValueError("property dut_config must be of type DutConfig")
        self._dut_config = dut_config

    @property
    def uart_agent(self) -> UartAgent:
        if self._uart_agent is None:
            raise ValueError("property uart_agent is not initialized")
        return self._uart_agent

    @uart_agent.setter
    def uart_agent(self, uart_agent: UartAgent) -> None:
        if not isinstance(uart_agent, UartAgent):
            raise ValueError("property uart_agent must be of type UartAgent")
        self._uart_agent = uart_agent

    def gen_config(self):
        PYCHARMDEBUG = environ.get("PYCHARMDEBUG")
        self.__logger__.info(f"PYCHARMDEBUG={PYCHARMDEBUG}")
        if PYCHARMDEBUG == "enabled":
            pydevd_pycharm.settrace(
                "localhost", port=50100, stdoutToServer=True, stderrToServer=True
            )
            self.__logger__.info("DEBUGGER ENTRY POINT")
        self.__logger__.info("ASK MARC-ANDRE FOR ANYTHING ELSE")

    def build_env(self):
        self.__dut__.in_sig.value = self.dut_config.in_sig
        self.__dut__.resetCyclic.value = self.dut_config.reset_cyclic
        self.__dut__.sipms.integer = self.dut_config.sipms
        self.__dut__.clkMHz.value = self.dut_config.clk_MHz
        self.uart_agent.attach(
            self.__dut__.in_sig, self.__dut__.out_sig, self.__dut__.clk
        )

    def reset(self) -> None:
        pass

    def load_config(self) -> None:
        pass

    def run(self):
        self.gen_config()
        self.build_env()
        self.test()

    def test(self):
        raise NotImplementedError("override this test in daughter class")
