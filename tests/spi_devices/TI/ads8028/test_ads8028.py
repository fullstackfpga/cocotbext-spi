"""
Copyright (c) 2021 Spencer Chang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import logging
import os

import cocotb_test.simulator

import cocotb
from cocotb.triggers import Timer
from cocotb.regression import TestFactory

from cocotbext.spi import SpiMaster, SpiSignals, SpiConfig
from cocotbext.spi.devices.TI import ADS8028


class TB:
    def __init__(self, dut):
        self.dut = dut
        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)

        self.signals = SpiSignals(
            sclk=dut.sclk,
            mosi=dut.mosi,
            miso=dut.miso,
            cs=dut.ncs,
            cs_active_low=True
        )

        self.config = SpiConfig(
            word_width=16,
            sclk_freq=25e6,
            cpol=False,
            cpha=True,
            msb_first=True
        )

        self.source = SpiMaster(self.signals, self.config)
        self.sink = ADS8028(self.signals)


@cocotb.test()
async def run_test_ads8028(dut):
    tb = TB(dut)
    await Timer(10, 'us')

    address_mask = 0xF000
    data_mask = 0x0FFF

    await tb.source.write([tb.sink.create_spi_word("write", 0b111100011100100)])
    _ = await tb.source.read()

    await Timer(20, units='ns')

    await tb.source.write([tb.sink.create_spi_word("read", 0x0000)])
    _ = await tb.source.read()

    await Timer(20, units='ns')

    await tb.source.write([tb.sink.create_spi_word("read", 0x0000)])
    ain0 = (await tb.source.read())[0]
    assert ain0 & address_mask == 0 << 12
    assert ain0 & data_mask == 0

    await Timer(20, units='ns')

    await tb.source.write([tb.sink.create_spi_word("read", 0x0000)])
    ain1 = (await tb.source.read())[0]
    assert ain1 & address_mask == 1 << 12
    assert ain1 & data_mask == 1

    await Timer(5, 'us')

# cocotb-test

tests_dir = os.path.dirname(__file__)


def test_ads8028(request):
    dut = "test_ads8028"
    module = os.path.splitext(os.path.basename(__file__))[0]
    toplevel = dut

    verilog_sources = [
        os.path.join(tests_dir, f"{dut}.v")
    ]

    parameters = {}

    extra_env = {f'PARAM_{k}': str(v) for k, v in parameters.items()}

    sim_build = os.path.join(tests_dir, "sim_build",
                             request.node.name.replace('[', '-').replace(']', ''))

    cocotb_test.simulator.run(
        python_search=[tests_dir],
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        parameters=parameters,
        sim_build=sim_build,
        extra_env=extra_env,
    )
