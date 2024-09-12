from base_monitor import BaseMonitor
from cocotb.handle import SimHandleBase
from typing import Dict

class UartMonitor(BaseMonitor):
    def __init__(self, clk: SimHandleBase, valid: SimHandleBase, datas: Dict[str, SimHandleBase]):
        super().__init__(clk=clk, valid=valid, datas=datas)

    