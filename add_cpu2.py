#!/usr/bin/env python3
"""Add second Z80 CPU components to kz80 PCB file."""

import sys

pcb_path = sys.argv[1] if len(sys.argv) > 1 else '/home/alex/Downloads/retroshield-hw-master/hardware/kz80/kz80.pcb'

with open(pcb_path, 'r') as f:
    pcb = f.read()

# 1. Double the board width
pcb = pcb.replace(
    'PCB["" 55880000nm 53340000nm]',
    'PCB["" 111760000nm 53340000nm]',
    1
)

# 2. Update outline to match new board width
pcb = pcb.replace(
    'Line[55880000nm 0 0 0 254000nm 508000nm "clearline"]',
    'Line[111760000nm 0 0 0 254000nm 508000nm "clearline"]'
)
pcb = pcb.replace(
    'Line[55880000nm 53340000nm 55880000nm 0 254000nm 508000nm "clearline"]',
    'Line[111760000nm 53340000nm 111760000nm 0 254000nm 508000nm "clearline"]'
)
pcb = pcb.replace(
    'Line[0 53340000nm 55880000nm 53340000nm 254000nm 508000nm "clearline"]',
    'Line[0 53340000nm 111760000nm 53340000nm 254000nm 508000nm "clearline"]'
)

# 3. New element footprints for CPU2 section
new_elements = r"""
Element["" "HEADER36_1" "J2" "unknown" 58420000nm 2540000nm -1270000nm 45085000nm 0 100 ""]
(
	Pin[0 0 1524000nm 762000nm 1676400nm 965200nm "+5V" "1" "square,connected"]
	Pin[0 2540000nm 1524000nm 762000nm 1676400nm 965200nm "PA0-22" "2" ""]
	Pin[0 5080000nm 1524000nm 762000nm 1676400nm 965200nm "PA2-24" "3" ""]
	Pin[0 7620000nm 1524000nm 762000nm 1676400nm 965200nm "PA4-26" "4" ""]
	Pin[0 10160000nm 1524000nm 762000nm 1676400nm 965200nm "PA6-28" "5" ""]
	Pin[0 12700000nm 1524000nm 762000nm 1676400nm 965200nm "PC7-30" "6" ""]
	Pin[0 15240000nm 1524000nm 762000nm 1676400nm 965200nm "PC5-32" "7" ""]
	Pin[0 17780000nm 1524000nm 762000nm 1676400nm 965200nm "PC3-34" "8" ""]
	Pin[0 20320000nm 1524000nm 762000nm 1676400nm 965200nm "PC1-36" "9" ""]
	Pin[0 22860000nm 1524000nm 762000nm 1676400nm 965200nm "PD7-38" "10" ""]
	Pin[0 25400000nm 1524000nm 762000nm 1676400nm 965200nm "PG1-40" "11" ""]
	Pin[0 27940000nm 1524000nm 762000nm 1676400nm 965200nm "PL7-42" "12" ""]
	Pin[0 30480000nm 1524000nm 762000nm 1676400nm 965200nm "PL5-44" "13" ""]
	Pin[0 33020000nm 1524000nm 762000nm 1676400nm 965200nm "PL3-46" "14" ""]
	Pin[0 35560000nm 1524000nm 762000nm 1676400nm 965200nm "PL1-48" "15" ""]
	Pin[0 38100000nm 1524000nm 762000nm 1676400nm 965200nm "PB3-50" "16" ""]
	Pin[0 40640000nm 1524000nm 762000nm 1676400nm 965200nm "PB1-52" "17" ""]
	Pin[0 43180000nm 1524000nm 762000nm 1676400nm 965200nm "GND" "18" "thermal(0X,1X)"]
	Pin[2540000nm 43180000nm 1524000nm 762000nm 1676400nm 965200nm "GND" "19" "thermal(0X,1X)"]
	Pin[2540000nm 40640000nm 1524000nm 762000nm 1676400nm 965200nm "53-PB0" "20" ""]
	Pin[2540000nm 38100000nm 1524000nm 762000nm 1676400nm 965200nm "51-PB2" "21" ""]
	Pin[2540000nm 35560000nm 1524000nm 762000nm 1676400nm 965200nm "49-PL0" "22" ""]
	Pin[2540000nm 33020000nm 1524000nm 762000nm 1676400nm 965200nm "47-PL2" "23" ""]
	Pin[2540000nm 30480000nm 1524000nm 762000nm 1676400nm 965200nm "45-PL4" "24" ""]
	Pin[2540000nm 27940000nm 1524000nm 762000nm 1676400nm 965200nm "43-PL6" "25" ""]
	Pin[2540000nm 25400000nm 1524000nm 762000nm 1676400nm 965200nm "41-PG0" "26" ""]
	Pin[2540000nm 22860000nm 1524000nm 762000nm 1676400nm 965200nm "39-PG2" "27" ""]
	Pin[2540000nm 20320000nm 1524000nm 762000nm 1676400nm 965200nm "37-PC0" "28" ""]
	Pin[2540000nm 17780000nm 1524000nm 762000nm 1676400nm 965200nm "35-PC2" "29" ""]
	Pin[2540000nm 15240000nm 1524000nm 762000nm 1676400nm 965200nm "33-PC4" "30" ""]
	Pin[2540000nm 12700000nm 1524000nm 762000nm 1676400nm 965200nm "31-PC6" "31" ""]
	Pin[2540000nm 10160000nm 1524000nm 762000nm 1676400nm 965200nm "29-PA7" "32" ""]
	Pin[2540000nm 7620000nm 1524000nm 762000nm 1676400nm 965200nm "27-PA5" "33" ""]
	Pin[2540000nm 5080000nm 1524000nm 762000nm 1676400nm 965200nm "25-PA3" "34" ""]
	Pin[2540000nm 2540000nm 1524000nm 762000nm 1676400nm 965200nm "23-PA1" "35" ""]
	Pin[2540000nm 0 1524000nm 762000nm 1676400nm 965200nm "+5V" "36" "connected"]
	ElementLine [-1270000nm -1270000nm -1270000nm 44450000nm 254000nm]
	ElementLine [-1270000nm 44450000nm 3810000nm 44450000nm 254000nm]
	ElementLine [3810000nm 44450000nm 3810000nm -1270000nm 254000nm]
	ElementLine [3810000nm -1270000nm -1270000nm -1270000nm 254000nm]
	ElementLine [-1270000nm 1270000nm 1270000nm 1270000nm 254000nm]
	ElementLine [1270000nm 1270000nm 1270000nm -1270000nm 254000nm]

	)

Element["" "DIP40" "U2" "unknown" 86360000nm 2540000nm 6985000nm -1905000nm 0 100 ""]
(
	Pin[0 0 1524000nm 762000nm 1676400nm 711200nm "A11" "1" "square"]
	Pin[0 2540000nm 1524000nm 762000nm 1676400nm 711200nm "A12" "2" ""]
	Pin[0 5080000nm 1524000nm 762000nm 1676400nm 711200nm "A13" "3" ""]
	Pin[0 7620000nm 1524000nm 762000nm 1676400nm 711200nm "A14" "4" ""]
	Pin[0 10160000nm 1524000nm 762000nm 1676400nm 711200nm "A15" "5" ""]
	Pin[0 12700000nm 1524000nm 762000nm 1676400nm 711200nm "CLK" "6" ""]
	Pin[0 15240000nm 1524000nm 762000nm 1676400nm 711200nm "D4" "7" ""]
	Pin[0 17780000nm 1524000nm 762000nm 1676400nm 711200nm "D3" "8" ""]
	Pin[0 20320000nm 1524000nm 762000nm 1676400nm 711200nm "D5" "9" ""]
	Pin[0 22860000nm 1524000nm 762000nm 1676400nm 711200nm "D6" "10" ""]
	Pin[0 25400000nm 1524000nm 762000nm 1676400nm 711200nm "VCC" "11" "connected"]
	Pin[0 27940000nm 1524000nm 762000nm 1676400nm 711200nm "D2" "12" ""]
	Pin[0 30480000nm 1524000nm 762000nm 1676400nm 711200nm "D7" "13" ""]
	Pin[0 33020000nm 1524000nm 762000nm 1676400nm 711200nm "D0" "14" ""]
	Pin[0 35560000nm 1524000nm 762000nm 1676400nm 711200nm "D1" "15" ""]
	Pin[0 38100000nm 1524000nm 762000nm 1676400nm 711200nm "_INT_" "16" ""]
	Pin[0 40640000nm 1524000nm 762000nm 1676400nm 711200nm "_NMI_" "17" ""]
	Pin[0 43180000nm 1524000nm 762000nm 1676400nm 711200nm "_HALT_" "18" ""]
	Pin[0 45720000nm 1524000nm 762000nm 1676400nm 711200nm "_MREQ_" "19" ""]
	Pin[0 48260000nm 1524000nm 762000nm 1676400nm 711200nm "_IORQ_" "20" ""]
	Pin[15240000nm 48260000nm 1524000nm 762000nm 1676400nm 711200nm "_RD_" "21" ""]
	Pin[15240000nm 45720000nm 1524000nm 762000nm 1676400nm 711200nm "_WR_" "22" ""]
	Pin[15240000nm 43180000nm 1524000nm 762000nm 1676400nm 711200nm "_BUSAK_" "23" ""]
	Pin[15240000nm 40640000nm 1524000nm 762000nm 1676400nm 711200nm "_WAIT_" "24" "connected"]
	Pin[15240000nm 38100000nm 1524000nm 762000nm 1676400nm 711200nm "_BUSRQ_" "25" "connected"]
	Pin[15240000nm 35560000nm 1524000nm 762000nm 1676400nm 711200nm "_RESET_" "26" ""]
	Pin[15240000nm 33020000nm 1524000nm 762000nm 1676400nm 711200nm "_M1_" "27" ""]
	Pin[15240000nm 30480000nm 1524000nm 762000nm 1676400nm 711200nm "_RFSH_" "28" ""]
	Pin[15240000nm 27940000nm 1524000nm 762000nm 1676400nm 711200nm "GND" "29" "thermal(1X)"]
	Pin[15240000nm 25400000nm 1524000nm 762000nm 1676400nm 711200nm "A0" "30" ""]
	Pin[15240000nm 22860000nm 1524000nm 762000nm 1676400nm 711200nm "A1" "31" ""]
	Pin[15240000nm 20320000nm 1524000nm 762000nm 1676400nm 711200nm "A2" "32" ""]
	Pin[15240000nm 17780000nm 1524000nm 762000nm 1676400nm 711200nm "A3" "33" ""]
	Pin[15240000nm 15240000nm 1524000nm 762000nm 1676400nm 711200nm "A4" "34" ""]
	Pin[15240000nm 12700000nm 1524000nm 762000nm 1676400nm 711200nm "A5" "35" ""]
	Pin[15240000nm 10160000nm 1524000nm 762000nm 1676400nm 711200nm "A6" "36" ""]
	Pin[15240000nm 7620000nm 1524000nm 762000nm 1676400nm 711200nm "A7" "37" ""]
	Pin[15240000nm 5080000nm 1524000nm 762000nm 1676400nm 711200nm "A8" "38" ""]
	Pin[15240000nm 2540000nm 1524000nm 762000nm 1676400nm 711200nm "A9" "39" ""]
	Pin[15240000nm 0 1524000nm 762000nm 1676400nm 711200nm "A10" "40" ""]
	ElementLine [-1270000nm -1270000nm -1270000nm 49530000nm 254000nm]
	ElementLine [-1270000nm 49530000nm 16510000nm 49530000nm 254000nm]
	ElementLine [16510000nm 49530000nm 16510000nm -1270000nm 254000nm]
	ElementLine [-1270000nm -1270000nm 6350000nm -1270000nm 254000nm]
	ElementLine [8890000nm -1270000nm 16510000nm -1270000nm 254000nm]
	ElementArc [7620000nm -1270000nm 1270000nm 1270000nm 0 180 254000nm]

	)

Element["" "0805" "C4" "100NF" 65405000nm 2540000nm -800100nm 977900nm 0 100 ""]
(
	Pad[899922nm -99822nm 899922nm 99822nm 1299972nm 508000nm 1452372nm "1" "1" "square"]
	Pad[-899922nm -99822nm -899922nm 99822nm 1299972nm 508000nm 1452372nm "2" "2" "square,connected"]
	ElementLine [-99822nm 699770nm 99822nm 699770nm 203200nm]
	ElementLine [-99822nm -699770nm 99822nm -699770nm 203200nm]

	)

Element["" "0805" "C5" "22PF" 76200000nm 16510000nm -2567178nm -800100nm 0 100 ""]
(
	Pad[-99822nm -899922nm 99822nm -899922nm 1299972nm 508000nm 1452372nm "1" "1" "square"]
	Pad[-99822nm 899922nm 99822nm 899922nm 1299972nm 508000nm 1452372nm "2" "2" "square"]
	ElementLine [699770nm -99822nm 699770nm 99822nm 203200nm]
	ElementLine [-699770nm -99822nm -699770nm 99822nm 203200nm]

	)

Element["" "0805" "R2" "33" 63500000nm 49530000nm 1739900nm -1308100nm 0 100 ""]
(
	Pad[-99822nm 899922nm 99822nm 899922nm 1299972nm 508000nm 1452372nm "1" "1" "square"]
	Pad[-99822nm -899922nm 99822nm -899922nm 1299972nm 508000nm 1452372nm "2" "2" "square"]
	ElementLine [-699770nm -99822nm -699770nm 99822nm 203200nm]
	ElementLine [699770nm -99822nm 699770nm 99822nm 203200nm]

	)

"""

# Insert new elements before Layer(1 "top")
pcb = pcb.replace('Layer(1 "top")', new_elements + 'Layer(1 "top")')

# 4. Update existing +5V net to include new components
pcb = pcb.replace(
    '\tNet("+5V" "(unknown)")\n\t(\n\t\tConnect("C1-2")\n\t\tConnect("C2-2")\n\t\tConnect("J1-1")\n\t\tConnect("J1-36")\n\t\tConnect("LED1-1")\n\t\tConnect("U1-11")\n\t\tConnect("U1-24")\n\t\tConnect("U1-25")\n\t)',
    '\tNet("+5V" "(unknown)")\n\t(\n\t\tConnect("C1-2")\n\t\tConnect("C2-2")\n\t\tConnect("C4-2")\n\t\tConnect("J1-1")\n\t\tConnect("J1-36")\n\t\tConnect("J2-1")\n\t\tConnect("J2-36")\n\t\tConnect("LED1-1")\n\t\tConnect("U1-11")\n\t\tConnect("U1-24")\n\t\tConnect("U1-25")\n\t\tConnect("U2-11")\n\t\tConnect("U2-24")\n\t\tConnect("U2-25")\n\t)'
)

# Update existing GND net
pcb = pcb.replace(
    '\tNet("GND" "(unknown)")\n\t(\n\t\tConnect("C1-1")\n\t\tConnect("C2-1")\n\t\tConnect("C3-2")\n\t\tConnect("J1-18")\n\t\tConnect("J1-19")\n\t\tConnect("U1-29")\n\t)',
    '\tNet("GND" "(unknown)")\n\t(\n\t\tConnect("C1-1")\n\t\tConnect("C2-1")\n\t\tConnect("C3-2")\n\t\tConnect("C4-1")\n\t\tConnect("C5-2")\n\t\tConnect("J1-18")\n\t\tConnect("J1-19")\n\t\tConnect("J2-18")\n\t\tConnect("J2-19")\n\t\tConnect("U1-29")\n\t\tConnect("U2-29")\n\t)'
)

# 5. Build new nets for CPU2 signals
cpu2_nets = ""

# Control signal nets
ctrl_pins = {
    '\\_INT_2\\_': ('J2-16', 'U2-16'),
    '\\_IORQ_2\\_': ('J2-27', 'U2-20'),
    '\\_MREQ_2\\_': ('J2-26', 'U2-19'),
    '\\_NMI_2\\_': ('J2-21', 'U2-17'),
    '\\_RD_2\\_': ('J2-20', 'U2-21'),
    '\\_RESET_2\\_': ('J2-10', 'U2-26'),
    '\\_WR_2\\_': ('J2-11', 'U2-22'),
}
for net_name, (j_pin, u_pin) in sorted(ctrl_pins.items()):
    cpu2_nets += f'\tNet("{net_name}" "(unknown)")\n\t(\n\t\tConnect("{j_pin}")\n\t\tConnect("{u_pin}")\n\t)\n'

# Address bus nets
j_addr = {0:2,1:35,2:3,3:34,4:4,5:33,6:5,7:32,8:28,9:9,10:29,11:8,12:30,13:7,14:31,15:6}
u_addr = {0:30,1:31,2:32,3:33,4:34,5:35,6:36,7:37,8:38,9:39,10:40,11:1,12:2,13:3,14:4,15:5}
for i in range(16):
    cpu2_nets += f'\tNet("A{i}_2" "(unknown)")\n\t(\n\t\tConnect("J2-{j_addr[i]}")\n\t\tConnect("U2-{u_addr[i]}")\n\t)\n'

# Data bus nets
j_data = {0:22,1:15,2:23,3:14,4:24,5:13,6:25,7:12}
u_data = {0:14,1:15,2:12,3:8,4:7,5:9,6:10,7:13}
for i in range(8):
    cpu2_nets += f'\tNet("D{i}_2" "(unknown)")\n\t(\n\t\tConnect("J2-{j_data[i]}")\n\t\tConnect("U2-{u_data[i]}")\n\t)\n'

# Clock nets
cpu2_nets += '\tNet("CLK_2" "(unknown)")\n\t(\n\t\tConnect("C5-1")\n\t\tConnect("R2-1")\n\t\tConnect("U2-6")\n\t)\n'
cpu2_nets += '\tNet("CLK_2_R" "(unknown)")\n\t(\n\t\tConnect("J2-17")\n\t\tConnect("R2-2")\n\t)\n'

# BUSAK_2 (active output, no header pin in this design)
cpu2_nets += '\tNet("\\_BUSAK_2\\_" "(unknown)")\n\t(\n\t\tConnect("U2-23")\n\t)\n'

# Insert new nets before the final closing )
last_paren = pcb.rfind(')')
pcb = pcb[:last_paren] + cpu2_nets + pcb[last_paren:]

with open(pcb_path, 'w') as f:
    f.write(pcb)

print("PCB file updated successfully with CPU2 components and nets")
