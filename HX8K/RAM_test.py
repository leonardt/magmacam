import magma as m
import mantle
from rom import ROM8, ROM16
from pipeline import Pipeline, MEM, ReadRom
from mantle.lattice.ice40 import ROMB, SB_LUT4
from mantle.util.edge import falling, rising
from loam.boards.hx8kboard import HX8KBoard

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm


hx8kboard = HX8KBoard()
hx8kboard.Clock.on()
hx8kboard.D1.on()
hx8kboard.D2.on()
hx8kboard.D3.on()
hx8kboard.D4.on()
hx8kboard.D5.on()
hx8kboard.D6.on()
hx8kboard.D7.on()
hx8kboard.D8.on()

hx8kboard.J2[9].output().on()
hx8kboard.J2[10].output().on()
# hx8kboard.J2[11].output().on()
# hx8kboard.J2[12].output().on()

main = hx8kboard.main()

# transformed row format data
'''
0.) [0, 0, 128, 384, 960, 2016, 1840, 1048, 3096, 3128, 3184, 4064, 1984, 768, 0, 0]
1.) [0, 0, 0, 64, 64, 64, 192, 128, 128, 384, 256, 256, 768, 512, 0, 0]
2.) [0, 0, 192, 992, 32, 32, 32, 32, 64, 2016, 4094, 3840, 3072, 0, 0, 0]
3.) [0, 0, 0, 1920, 2016, 96, 224, 192, 192, 96, 32, 224, 1984, 3584, 0, 0]
4.) [0, 0, 0, 32, 32, 2080, 2080, 2080, 4064, 96, 64, 64, 64, 96, 0, 0]
5.) [0, 0, 0, 8, 2044, 3584, 7168, 896, 192, 96, 48, 96, 192, 2944, 1536, 0]
6.) [0, 64, 192, 384, 384, 768, 768, 512, 992, 864, 864, 960, 256, 0, 0, 0]
7.) [0, 0, 0, 0, 960, 4064, 48, 32, 96, 192, 192, 384, 768, 512, 1536, 0]
8.) [0, 0, 0, 240, 4080, 3120, 3680, 1984, 960, 960, 576, 1632, 1632, 992, 384, 0]
9.) [0, 0, 0, 0, 960, 2016, 1632, 1632, 2016, 960, 224, 224, 224, 224, 64, 0]
'''

img_list = [0, 64, 192, 384, 384, 768, 768, 512, 992, 864, 864, 960, 256, 0, 0, 0]

# from arducam
#img_list = [0, 0, 0, 0, 64, 57440, 50720, 50976, 50592, 64576, 28672, 0, 0, 0, 0, 32768] # 3, last col->first col
#img_list = [0, 0, 192, 480, 816, 528, 528, 528, 528, 1552, 1552, 560, 880, 992, 448, 0] # 0

num_data = [m.uint(img_list[i], 16) for i in range(16)]

# decrease the frequency to avoid timing violation
counter = mantle.Counter(4)
sclk = counter.O[-1]
rom_idx = mantle.Counter(4, has_ce=True)


full = mantle.SRFF(has_ce=True)
check = mantle.EQ(4)(rom_idx.O, m.bits(15, 4))
full(check, 0)
m.wire(falling(sclk), full.CE)
rom_ce = rising(sclk) & ~full.O
m.wire(rom_ce, rom_idx.CE)

rom = ROM16(4, num_data, rom_idx.O)

pipeline = Pipeline()

m.wire(sclk, pipeline.CLK)
m.wire(rom.O, pipeline.DATA)
m.wire(rom_idx.O, pipeline.WADDR)
m.wire(~full.O, pipeline.WE)
m.wire(full.O, pipeline.RUN)
m.wire(pipeline.O[:4], m.bits([main.D1, main.D2, main.D3, main.D4]))
# light 5 indicates the end of prediction
m.wire(pipeline.D, main.D5)

m.wire(0, main.D6)
m.wire(0, main.D7)
m.wire(0, main.D8)

m.wire(sclk,      main.J2_9)
m.wire(rom_ce,  main.J2_10) # valid
# m.wire(rescale.UART,      main.J2_11)
# m.wire(rescale.DONE,      main.J2_12)
