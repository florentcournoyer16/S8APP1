import pydevd_pycharm

from dataclasses import dataclass
from typing import Any, Union, List, Optional
from logging import Logger
from os import environ

from cocotb import test
from cocotb.clock import Clock
from cocotb.handle import ModifiableObject, HierarchyObject
from cocotb.log import SimLog
from verif.tests.uart_driver import UartDriver, UartConfig


@dataclass
class DutConfig:
    reset: int = 0
    clk: Clock = 10
    clk_units = "ns"
    in_sig: int = 0
    reset_cyclic: int = 0
    sipms: List[2] = [0, 0]
    clk_MHz: int = 100


class TestInterface:
    def __init__(self, dut_config: DutConfig, uart_config: UartConfig):
        self._logger: Logger = SimLog("cocotb.Test")
        self.dut_config: DutConfig = dut_config
        self.uart_driver: UartDriver = UartDriver(uart_config)

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
    def uart_driver(self) -> UartDriver:
        if self._uart_driver is None:
            raise ValueError("property uart_config is not initialized")
        return self._uart_driver

    @uart_driver.setter
    def uart_config(self, uart_driver: UartConfig) -> None:
        if not isinstance(uart_driver, UartConfig):
            raise ValueError("property uart_config must be of type UartConfig")
        self._uart_driver = uart_driver

    def gen_config(self):
        PYCHARMDEBUG = environ.get("PYCHARMDEBUG")
        self._logger.info(f"PYCHARMDEBUG={PYCHARMDEBUG}")
        if PYCHARMDEBUG == "enabled":
            pydevd_pycharm.settrace(
                "localhost", port=50100, stdoutToServer=True, stderrToServer=True
            )
            self._logger.info("DEBUGGER ENTRY POINT")
        self._logger.info("ASK MARC-ANDRE FOR ANYTHING ELSE")

    def build_env(self, dut: HierarchyObject):
        dut.in_sig.value = self.dut_config.in_sig
        dut.resetCyclic.value = self.dut_config.resetCyclic
        dut.sipms.integer = self.dut_config.sipms
        dut.clkMHz.value = self.dut_config.clkMhz
        self.uart_driver.attach(dut.in_sig, dut.out_sig, dut.clk)

    def reset(self) -> None:
        pass

    def load_config(self) -> None:
        pass

    @test
    def run(self, dut: HierarchyObject):
        self.gen_config()
        self.build_env(dut)
        self.test()

    def test(self):
        raise NotImplementedError("override this test in daughter class")


uart_config = UartConfig(baud_rate=1000)

mytest = TestInterface()
