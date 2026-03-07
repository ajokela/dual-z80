#!/usr/bin/env python3
"""
Modify the original kz80.pcb to add a second Z80 CPU with shared bus architecture.
- Shared address bus (A0-A15) and data bus (D0-D7)
- Small 2x6 header (J2) for CPU2 control signals
- U2 (Z80 DIP40), C4 (100nF), C5 (22pF), R2 (33 ohm)
"""

import sys
import re

pcb_file = sys.argv[1]

with open(pcb_file, 'r') as f:
    content = f.read()

# 1. Widen the board from 55880000nm to 86360000nm (~86mm, +30mm for CPU2)
content = content.replace(
    'PCB["" 55880000nm 53340000nm]',
    'PCB["" 86360000nm 53340000nm]'
)

# 2. Find insertion point: before the Layer section, after all existing Elements
# We'll insert new elements right before "Layer(1"
layer_match = re.search(r'^Layer\(1 ', content, re.MULTILINE)
if not layer_match:
    print("ERROR: Could not find Layer(1 in PCB file")
    sys.exit(1)

insert_pos = layer_match.start()

# U2 - Z80 DIP40, placed at x=62000000nm (~62mm), y=2540000nm (same y as U1)
u2_element = '''Element["" "DIP40" "U2" "unknown" 62000000nm 2540000nm 6985000nm -1905000nm 0 100 ""]
(
\tPin[0 0 1524000nm 762000nm 1676400nm 711200nm "A11" "1" "square"]
\tPin[0 2540000nm 1524000nm 762000nm 1676400nm 711200nm "A12" "2" ""]
\tPin[0 5080000nm 1524000nm 762000nm 1676400nm 711200nm "A13" "3" ""]
\tPin[0 7620000nm 1524000nm 762000nm 1676400nm 711200nm "A14" "4" ""]
\tPin[0 10160000nm 1524000nm 762000nm 1676400nm 711200nm "A15" "5" ""]
\tPin[0 12700000nm 1524000nm 762000nm 1676400nm 711200nm "CLK" "6" ""]
\tPin[0 15240000nm 1524000nm 762000nm 1676400nm 711200nm "D4" "7" ""]
\tPin[0 17780000nm 1524000nm 762000nm 1676400nm 711200nm "D3" "8" ""]
\tPin[0 20320000nm 1524000nm 762000nm 1676400nm 711200nm "D5" "9" ""]
\tPin[0 22860000nm 1524000nm 762000nm 1676400nm 711200nm "D6" "10" ""]
\tPin[0 25400000nm 1524000nm 762000nm 1676400nm 711200nm "VCC" "11" "connected"]
\tPin[0 27940000nm 1524000nm 762000nm 1676400nm 711200nm "D2" "12" ""]
\tPin[0 30480000nm 1524000nm 762000nm 1676400nm 711200nm "D7" "13" ""]
\tPin[0 33020000nm 1524000nm 762000nm 1676400nm 711200nm "D0" "14" ""]
\tPin[0 35560000nm 1524000nm 762000nm 1676400nm 711200nm "D1" "15" ""]
\tPin[0 38100000nm 1524000nm 762000nm 1676400nm 711200nm "_INT_" "16" ""]
\tPin[0 40640000nm 1524000nm 762000nm 1676400nm 711200nm "_NMI_" "17" ""]
\tPin[0 43180000nm 1524000nm 762000nm 1676400nm 711200nm "_HALT_" "18" ""]
\tPin[0 45720000nm 1524000nm 762000nm 1676400nm 711200nm "_MREQ_" "19" ""]
\tPin[0 48260000nm 1524000nm 762000nm 1676400nm 711200nm "_IORQ_" "20" ""]
\tPin[15240000nm 48260000nm 1524000nm 762000nm 1676400nm 711200nm "_RD_" "21" ""]
\tPin[15240000nm 45720000nm 1524000nm 762000nm 1676400nm 711200nm "_WR_" "22" ""]
\tPin[15240000nm 43180000nm 1524000nm 762000nm 1676400nm 711200nm "_BUSAK_" "23" ""]
\tPin[15240000nm 40640000nm 1524000nm 762000nm 1676400nm 711200nm "_WAIT_" "24" "connected"]
\tPin[15240000nm 38100000nm 1524000nm 762000nm 1676400nm 711200nm "_BUSRQ_" "25" "connected"]
\tPin[15240000nm 35560000nm 1524000nm 762000nm 1676400nm 711200nm "_RESET_" "26" ""]
\tPin[15240000nm 33020000nm 1524000nm 762000nm 1676400nm 711200nm "_M1_" "27" ""]
\tPin[15240000nm 30480000nm 1524000nm 762000nm 1676400nm 711200nm "_RFSH_" "28" ""]
\tPin[15240000nm 27940000nm 1524000nm 762000nm 1676400nm 711200nm "GND" "29" ""]
\tPin[15240000nm 25400000nm 1524000nm 762000nm 1676400nm 711200nm "A0" "30" ""]
\tPin[15240000nm 22860000nm 1524000nm 762000nm 1676400nm 711200nm "A1" "31" ""]
\tPin[15240000nm 20320000nm 1524000nm 762000nm 1676400nm 711200nm "A2" "32" ""]
\tPin[15240000nm 17780000nm 1524000nm 762000nm 1676400nm 711200nm "A3" "33" ""]
\tPin[15240000nm 15240000nm 1524000nm 762000nm 1676400nm 711200nm "A4" "34" ""]
\tPin[15240000nm 12700000nm 1524000nm 762000nm 1676400nm 711200nm "A5" "35" ""]
\tPin[15240000nm 10160000nm 1524000nm 762000nm 1676400nm 711200nm "A6" "36" ""]
\tPin[15240000nm 7620000nm 1524000nm 762000nm 1676400nm 711200nm "A7" "37" ""]
\tPin[15240000nm 5080000nm 1524000nm 762000nm 1676400nm 711200nm "A8" "38" ""]
\tPin[15240000nm 2540000nm 1524000nm 762000nm 1676400nm 711200nm "A9" "39" ""]
\tPin[15240000nm 0 1524000nm 762000nm 1676400nm 711200nm "A10" "40" ""]
\tElementLine [-1270000nm -1270000nm -1270000nm 49530000nm 254000nm]
\tElementLine [-1270000nm 49530000nm 16510000nm 49530000nm 254000nm]
\tElementLine [16510000nm 49530000nm 16510000nm -1270000nm 254000nm]
\tElementLine [-1270000nm -1270000nm 6350000nm -1270000nm 254000nm]
\tElementLine [8890000nm -1270000nm 16510000nm -1270000nm 254000nm]
\tElementArc [7620000nm -1270000nm 1270000nm 1270000nm 0 180 254000nm]

\t)

'''

# J2 - 2x6 header for CPU2 control signals
# Place at x=58000000nm (~58mm), y=2540000nm
# 2x6 pin header, 2.54mm pitch
# Pin numbering: left column 1,3,5,7,9,11; right column 2,4,6,8,10,12
j2_element = '''Element["" "HEADER12_1" "J2" "unknown" 58000000nm 2540000nm -1270000nm 13970000nm 0 100 ""]
(
\tPin[0 0 1524000nm 762000nm 1676400nm 965200nm "+5V" "1" "square,connected"]
\tPin[2540000nm 0 1524000nm 762000nm 1676400nm 965200nm "GND" "2" ""]
\tPin[0 2540000nm 1524000nm 762000nm 1676400nm 965200nm "CLK_2" "3" ""]
\tPin[2540000nm 2540000nm 1524000nm 762000nm 1676400nm 965200nm "RESET_2" "4" ""]
\tPin[0 5080000nm 1524000nm 762000nm 1676400nm 965200nm "INT_2" "5" ""]
\tPin[2540000nm 5080000nm 1524000nm 762000nm 1676400nm 965200nm "NMI_2" "6" ""]
\tPin[0 7620000nm 1524000nm 762000nm 1676400nm 965200nm "MREQ_2" "7" ""]
\tPin[2540000nm 7620000nm 1524000nm 762000nm 1676400nm 965200nm "IORQ_2" "8" ""]
\tPin[0 10160000nm 1524000nm 762000nm 1676400nm 965200nm "RD_2" "9" ""]
\tPin[2540000nm 10160000nm 1524000nm 762000nm 1676400nm 965200nm "WR_2" "10" ""]
\tPin[0 12700000nm 1524000nm 762000nm 1676400nm 965200nm "BUSRQ_2" "11" ""]
\tPin[2540000nm 12700000nm 1524000nm 762000nm 1676400nm 965200nm "BUSAK_2" "12" ""]
\tElementLine [-1270000nm -1270000nm -1270000nm 13970000nm 254000nm]
\tElementLine [-1270000nm 13970000nm 3810000nm 13970000nm 254000nm]
\tElementLine [3810000nm 13970000nm 3810000nm -1270000nm 254000nm]
\tElementLine [3810000nm -1270000nm -1270000nm -1270000nm 254000nm]
\tElementLine [-1270000nm 1270000nm 1270000nm 1270000nm 254000nm]
\tElementLine [1270000nm 1270000nm 1270000nm -1270000nm 254000nm]

\t)

'''

# C4 - 100nF decoupling cap (0805) near U2, at x=72000000nm y=2540000nm
c4_element = '''Element["" "0805" "C4" "100NF" 72000000nm 2540000nm -800100nm 977900nm 0 100 ""]
(
\tPad[899922nm -99822nm 899922nm 99822nm 1299972nm 508000nm 1452372nm "1" "1" "square"]
\tPad[-899922nm -99822nm -899922nm 99822nm 1299972nm 508000nm 1452372nm "2" "2" "square,connected"]
\tElementLine [-99822nm 699770nm 99822nm 699770nm 203200nm]
\tElementLine [-99822nm -699770nm 99822nm -699770nm 203200nm]

\t)

'''

# C5 - 22pF clock cap (0805) near U2 CLK, at x=60000000nm y=16510000nm
c5_element = '''Element["" "0805" "C5" "22PF" 60000000nm 16510000nm -2567178nm -800100nm 0 100 ""]
(
\tPad[-99822nm -899922nm 99822nm -899922nm 1299972nm 508000nm 1452372nm "1" "1" "square"]
\tPad[-99822nm 899922nm 99822nm 899922nm 1299972nm 508000nm 1452372nm "2" "2" "square"]
\tElementLine [699770nm -99822nm 699770nm 99822nm 203200nm]
\tElementLine [-699770nm -99822nm -699770nm 99822nm 203200nm]

\t)

'''

# R2 - 33 ohm clock resistor (0805) near U2, at x=58000000nm y=49530000nm
r2_element = '''Element["" "0805" "R2" "33" 58000000nm 49530000nm 1739900nm -1308100nm 0 100 ""]
(
\tPad[-99822nm 899922nm 99822nm 899922nm 1299972nm 508000nm 1452372nm "1" "1" "square"]
\tPad[-99822nm -899922nm 99822nm -899922nm 1299972nm 508000nm 1452372nm "2" "2" "square"]
\tElementLine [-699770nm -99822nm -699770nm 99822nm 203200nm]
\tElementLine [699770nm -99822nm 699770nm 99822nm 203200nm]

\t)

'''

new_elements = u2_element + j2_element + c4_element + c5_element + r2_element
content = content[:insert_pos] + new_elements + content[insert_pos:]

# 3. Update the netlist - add U2 pins to shared nets and create new control nets

# Find the closing of NetList
netlist_end = content.rfind(')')
# The last ) before EOF closes the NetList block. But let's be more precise.
# Find "NetList()" and work from there
netlist_start = content.find('NetList()')

# Add U2 connections to existing shared nets
# For each shared net, add a Connect("U2-pin") line

# Map: net_name -> list of U2 pin numbers to add
shared_net_additions = {
    '+5V': ['U2-11', 'U2-24', 'U2-25', 'C4-2', 'J2-1'],
    'GND': ['U2-29', 'C4-1', 'C5-2', 'J2-2'],
    'A0': ['U2-30'],
    'A1': ['U2-31'],
    'A2': ['U2-32'],
    'A3': ['U2-33'],
    'A4': ['U2-34'],
    'A5': ['U2-35'],
    'A6': ['U2-36'],
    'A7': ['U2-37'],
    'A8': ['U2-38'],
    'A9': ['U2-39'],
    'A10': ['U2-40'],
    'A11': ['U2-1'],
    'A12': ['U2-2'],
    'A13': ['U2-3'],
    'A14': ['U2-4'],
    'A15': ['U2-5'],
    'D0': ['U2-14'],
    'D1': ['U2-15'],
    'D2': ['U2-12'],
    'D3': ['U2-8'],
    'D4': ['U2-7'],
    'D5': ['U2-9'],
    'D6': ['U2-10'],
    'D7': ['U2-13'],
}

# For each shared net, find the closing ) of that net block and insert new Connect lines before it
for net_name, pins in shared_net_additions.items():
    # Escape for regex - net names in PCB file use \\_name\\_ format for active-low
    if net_name == '+5V':
        pattern = r'(Net\("\+5V" "\(unknown\)"\)\n\t\()'
    elif net_name == 'GND':
        pattern = r'(Net\("GND" "\(unknown\)"\)\n\t\()'
    else:
        escaped = re.escape(net_name)
        pattern = r'(Net\("' + escaped + r'" "\(unknown\)"\)\n\t\()'

    match = re.search(pattern, content)
    if match:
        # Find the closing ) for this net block
        net_block_start = match.start()
        # Find next "\t)" after the opening
        close_pos = content.find('\n\t)', net_block_start + len(match.group(0)))
        if close_pos >= 0:
            insert_lines = ''
            for pin in pins:
                insert_lines += f'\n\t\tConnect("{pin}")'
            content = content[:close_pos] + insert_lines + content[close_pos:]
    else:
        print(f"WARNING: Could not find net {net_name} in PCB file")

# 4. Add new nets for CPU2 control signals (before the final closing of NetList)
new_nets = '''
\tNet("\\\\_BUSAK_2\\\\_" "(unknown)")
\t(
\t\tConnect("J2-12")
\t\tConnect("U2-23")
\t)
\tNet("\\\\_BUSRQ_2\\\\_" "(unknown)")
\t(
\t\tConnect("J2-11")
\t\tConnect("U2-25")
\t)
\tNet("\\\\_INT_2\\\\_" "(unknown)")
\t(
\t\tConnect("J2-5")
\t\tConnect("U2-16")
\t)
\tNet("\\\\_IORQ_2\\\\_" "(unknown)")
\t(
\t\tConnect("J2-8")
\t\tConnect("U2-20")
\t)
\tNet("\\\\_MREQ_2\\\\_" "(unknown)")
\t(
\t\tConnect("J2-7")
\t\tConnect("U2-19")
\t)
\tNet("\\\\_NMI_2\\\\_" "(unknown)")
\t(
\t\tConnect("J2-6")
\t\tConnect("U2-17")
\t)
\tNet("\\\\_RD_2\\\\_" "(unknown)")
\t(
\t\tConnect("J2-9")
\t\tConnect("U2-21")
\t)
\tNet("\\\\_RESET_2\\\\_" "(unknown)")
\t(
\t\tConnect("J2-4")
\t\tConnect("U2-26")
\t)
\tNet("\\\\_WR_2\\\\_" "(unknown)")
\t(
\t\tConnect("J2-10")
\t\tConnect("U2-22")
\t)
\tNet("CLK_2" "(unknown)")
\t(
\t\tConnect("C5-1")
\t\tConnect("R2-1")
\t\tConnect("U2-6")
\t)
\tNet("CLK_2_R" "(unknown)")
\t(
\t\tConnect("J2-3")
\t\tConnect("R2-2")
\t)
'''

# Find the final closing parenthesis of the NetList block
# The NetList block ends with a line containing just ")"
# Find the last occurrence of "\n)" which closes NetList()
last_close = content.rfind('\n)')
if last_close >= 0:
    content = content[:last_close] + new_nets + content[last_close:]
else:
    print("ERROR: Could not find end of NetList")
    sys.exit(1)

# Remove U2-25 from +5V net since BUSRQ_2 also connects there
# Actually, U2-25 is _BUSRQ_ which in the original is tied to +5V (active low, so pulling high = no bus request)
# For CPU2, we want BUSRQ_2 to be controllable, so remove U2-25 from +5V
# Let's fix: remove U2-25 from +5V and U2-24 from +5V (WAIT should also be controllable)
# Actually, looking at original: U1-24 (WAIT) and U1-25 (BUSRQ) are in +5V net (tied high = inactive)
# For CPU2, we want bus arbitration, so BUSRQ_2 needs to be separate. WAIT can stay tied high.
# So remove U2-25 from +5V (it's in BUSRQ_2 net), keep U2-24 in +5V

# U2-25 was added to both +5V and BUSRQ_2 nets. Remove from +5V.
content = content.replace('\t\tConnect("U2-25")\n\t\tConnect("C4-2")', '\t\tConnect("C4-2")')

with open(pcb_file, 'w') as f:
    f.write(content)

print("PCB file updated successfully with shared-bus dual Z80 design.")
print("New components: U2 (Z80), J2 (2x6 header), C4, C5, R2")
print("Shared nets: A0-A15, D0-D7, +5V, GND")
print("New nets: CLK_2, CLK_2_R, RESET_2, INT_2, NMI_2, MREQ_2, IORQ_2, RD_2, WR_2, BUSRQ_2, BUSAK_2")
