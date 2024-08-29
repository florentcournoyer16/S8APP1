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
from cocotb import start
from cocotb.triggers import ClockCycles

@dataclass
class DutConfig:
    reset: int = 0
    clk: int = 10
    clk_units = "ns"
    in_sig: int = 0
    reset_cyclic: int = 0
    sipms: List[int] = field(default_factory=lambda: [0, 0])
    clk_MHz: bool = 0


class BaseEnvironment:
    def __init__(
        self,
        test_name: str,
        dut: HierarchyObject,
        dut_config: DutConfig,
        uart_config: UartConfig,
    ):
        self.test_name = test_name
        self.logger: Logger = SimLog("cocotb.Test")
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

    def gen_config(self) -> None:
        PYCHARMDEBUG = environ.get("PYCHARMDEBUG")
        self.logger.info(f"PYCHARMDEBUG={PYCHARMDEBUG}")
        if PYCHARMDEBUG == "enabled":
            pydevd_pycharm.settrace(
                "localhost", port=50100, stdoutToServer=True, stderrToServer=True
            )
            self.logger.info("DEBUGGER ENTRY POINT")
        self.logger.info("ASK MARC-ANDRE FOR ANYTHING ELSE")

    def build_env(self) -> None:
        self.__dut__.in_sig.value = self.dut_config.in_sig
        self.__dut__.resetCyclic.value = self.dut_config.reset_cyclic
        self.__dut__.sipms.integer = self.dut_config.sipms
        self.__dut__.clkMHz.value = self.dut_config.clk_MHz
        self.uart_agent.attach(
            in_sig=self.__dut__.in_sig,
            out_sig=self.__dut__.out_sig,
            clk=self.__dut__.clk,
        )

    async def reset(self) -> None:
        self.__dut__.reset.value = 1
        await start(Clock(self.__dut__.clk, 10, units="ns").start())
        await ClockCycles(self.__dut__.clk, 10, rising=True)
        self.__dut__.reset.value = 0

    def load_config(self) -> None:
        pass

    async def run(self):
        self.logger.info(f"Starting test : {self.test_name}")
        self.gen_config()
        self.build_env()
        await self.reset()
        self.load_config()
        await self.test()

    async def test(self):
        raise NotImplementedError("override this test in daughter class")
