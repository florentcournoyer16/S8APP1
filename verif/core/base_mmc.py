# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# adapted from https://github.com/cocotb/cocotb/blob/stable/1.9/examples/matrix_multiplier/tests/test_matrix_multiplier.py

from typing import Any, Dict, List, Optional, Tuple

from cocotb import start_soon, Task
from cocotb.clock import Clock
from cocotb.handle import SimHandleBase
from cocotb.queue import Queue
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.log import SimLog
from base_monitor import BaseMonitor
from logging import Logger


class BaseMMC:
    """
    Reusable checker of a checker instance

    Args
        logicblock_instance: handle to an instance of a logic block
    """
    def __init__(self, logicblock_instance: SimHandleBase, logger_name: str):
        self._logicblock: SimHandleBase = logicblock_instance
        self._input_mon, self._output_mon = self._set_monitors()
        self._checkercoro: Optional[Task] = None
        self._log = SimLog("cocotb.MMC.%s" % logger_name)

    def start(self) -> None:
        """Starts monitors, model, and checker coroutine"""
        if self._checkercoro is not None:
            raise RuntimeError("Monitor already started")
        self._input_mon.start()
        self._output_mon.start()
        self._checkercoro = start_soon(self._checker())

    def stop(self) -> None:
        """Stops everything"""
        if self._checkercoro is None:
            raise RuntimeError("Monitor never started")
        self._input_mon.stop()
        self._output_mon.stop()
        self._checkercoro.kill()
        self._checkercoro = None

    def _set_monitors(self) -> tuple[BaseMonitor, BaseMonitor]:
        raise NotImplementedError("override this method in daughter class")

    def _model(self) -> bool:
        raise NotImplementedError("override this method in daughter class")

    async def _checker(self) -> None:
        raise NotImplementedError("override this method in daughter class")