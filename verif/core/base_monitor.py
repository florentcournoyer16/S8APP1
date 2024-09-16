# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# adapted from https://github.com/cocotb/cocotb/blob/stable/1.9/examples/matrix_multiplier/tests/test_matrix_multiplier.py

from typing import Any, Dict

import cocotb
from cocotb.handle import SimHandleBase
from cocotb.queue import Queue
from cocotb.triggers import RisingEdge
from cocotb.log import SimLog


class BaseMonitor:
    def __init__(
        self, clk: SimHandleBase, datas: Dict[str, SimHandleBase], logger_name: str
    ):
        self.values = Queue[Dict[str, int]]()
        self._clk = clk
        self._datas = datas
        self._coro = None  # is monitor running? False if "None"

        self._log = SimLog("cocotb.%s" %  logger_name)

    def start(self) -> None:
        if self._coro is not None:
            raise RuntimeError("Monitor already started")
        self._coro = cocotb.start_soon(self._run())

    def stop(self) -> None:
        if self._coro is None:
            raise RuntimeError("Monitor never started")
        self._coro.kill()
        self._coro = None

    async def _run(self) -> None:
        raise NotImplementedError("Override this method in daughter class")

    def _sample(self) -> Dict[str, Any]:
        """
        Samples the data signals and builds a transaction object

        Return value is what is stored in queue. Meant to be overriden by the user.
        """
        # possible messages to test monitor
        # self._log.info("use this to print some information at info level")
        # self._log.info({name: hex(handle.value) for name, handle in self._datas.items()})

        # for loop going through all the values in the signals to sample (see constructor)
        return {name: handle.value for name, handle in self._datas.items()}
