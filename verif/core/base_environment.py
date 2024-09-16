import pydevd_pycharm

from dataclasses import dataclass, field
from typing import List
from os import environ
from cocotb.clock import Clock
from cocotb.handle import HierarchyObject
from cocotb import start
from cocotb.triggers import ClockCycles
from cocotb.log import SimLog
from base_mmc import BaseMMC
from base_uart_agent import BaseUartAgent, UartConfig

@dataclass
class DutConfig:
    reset: int = 0
    clk: int = 10
    clk_units = "ns"
    in_sig: int = 0
    reset_cyclic: int = 0
    sipm0: int = 0
    sipm1: int = 0
    clk_MHz: bool = 0


class BaseEnvironment:
    def __init__(
        self,
        dut: HierarchyObject,
        dut_config: DutConfig,
        uart_config: UartConfig,
        test_name: str,
        logger_name: str,
    ):
        self._dut: HierarchyObject = dut
        self.dut_config: DutConfig = dut_config
        self._uart_agent: BaseUartAgent = self._set_uart_agent(uart_config)
        self._test_name: str = test_name
        self._mmc_list: List[BaseMMC] = []
        self._log = SimLog("cocotb.%s" % logger_name)

    @property
    def dut_config(self) -> DutConfig:
        if self._dut_config is None:
            raise ValueError("Property dut_config is not initialized")
        return self._dut_config

    @dut_config.setter
    def dut_config(self, dut_config: DutConfig) -> None:
        if not isinstance(dut_config, DutConfig):
            raise TypeError("Property dut_config must be of type DutConfig")
        self._dut_config = dut_config

    def _set_uart_agent(self, uart_config: UartConfig) -> BaseUartAgent:
        return BaseUartAgent(uart_config)

    def _gen_config(self) -> None:
        pycharm_debug = environ.get("PYCHARMDEBUG")
        self._log.info("PYCHARMDEBUG=%s", pycharm_debug)
        if pycharm_debug == "enabled":
            pydevd_pycharm.settrace(
                "localhost",
                port=5052,
                stdoutToServer=True,
                stderrToServer=True
            )
            self._log.info("Debugger entry point")

    def _build_env(self) -> None:
        self._dut.in_sig.value = self.dut_config.in_sig
        self._dut.resetCyclic.value = self.dut_config.reset_cyclic
        self._dut.sipms[0].value = self.dut_config.sipm0
        self._dut.sipms[1].value = self.dut_config.sipm0
        self._dut.clkMHz.value = self.dut_config.clk_MHz
        self._uart_agent.attach(
            in_sig=self._dut.in_sig,
            out_sig=self._dut.out_sig,
            dut_clk=self._dut.clk,
        )

    async def _reset(self) -> None:
        self._dut.reset.value = 1
        await start(Clock(self._dut.clk, 10, units="ns").start())
        await ClockCycles(self._dut.clk, 10, rising=True)
        self._dut.reset.value = 0

    def _load_config(self) -> None:
        pass

    async def _test(self, name):
        raise NotImplementedError("Override this method in daughter class")

    async def run(self, names:list[str]=['']) -> None:
        self._log.info("Starting test: %s", self._test_name)
        self._gen_config()
        self._build_env()
        self._uart_agent.start_uart_rx_listenner()
        for mmc in self._mmc_list:
            mmc.start()
        await self._reset()
        self._load_config()
        await self._test(names=names)
        for mmc in self._mmc_list:
            mmc.stop()
        self._uart_agent.stop_uart_rx_listenner()
        
