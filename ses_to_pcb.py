#!/usr/bin/env python3
"""Parse Freerouting SES file and inject routes into pcb-rnd PCB file as copper traces."""
import sys
import re

ses_file = sys.argv[1]
pcb_file = sys.argv[2]

# Parse SES file to extract wire paths
with open(ses_file, 'r') as f:
    ses = f.read()

# Extract all wire paths from network_out section
# Format: (wire (path layer_name width x1 y1 x2 y2 ... xn yn))
# Also extract vias: (via pstk_N x y)

# Map SES layer names to pcb-rnd layer numbers
layer_map = {
    '3__top_copper': 1,      # top copper
    '6__bottom_copper': 2,   # bottom copper (solder side)
}

# Parse wires
wires = []  # list of (layer_num, width, [(x1,y1), (x2,y2), ...])
vias = []   # list of (x, y)

# Find network_out section
net_out_match = re.search(r'\(network_out\s', ses)
if not net_out_match:
    print("ERROR: no network_out found in SES")
    sys.exit(1)

# Extract all wire paths
for wire_match in re.finditer(r'\(wire\s*\(path\s+(\S+)\s+(\d+)((?:\s+-?\d+)+)\s*\)\s*\)', ses):
    layer_name = wire_match.group(1)
    width = int(wire_match.group(2))
    coords_str = wire_match.group(3).strip()
    coords = [int(x) for x in coords_str.split()]

    layer_num = layer_map.get(layer_name)
    if layer_num is None:
        print(f"WARNING: unknown layer {layer_name}")
        continue

    points = []
    for i in range(0, len(coords), 2):
        points.append((coords[i], coords[i+1]))

    wires.append((layer_num, width, points))

# Extract vias
for via_match in re.finditer(r'\(via\s+\S+\s+(-?\d+)\s+(-?\d+)\s*\)', ses):
    x = int(via_match.group(1))
    y = int(via_match.group(2))
    vias.append((x, y))

print(f"Parsed {len(wires)} wires and {len(vias)} vias from SES file")

# Read PCB file
with open(pcb_file, 'r') as f:
    pcb = f.read()

# pcb-rnd coordinate system: origin top-left, y increases downward
# SES coordinate system: origin bottom-left, y increases upward
# Need to find board height to convert y coordinates
board_match = re.search(r'PCB\["[^"]*"\s+(\d+)nm\s+(\d+)nm\]', pcb)
if not board_match:
    print("ERROR: could not find PCB dimensions")
    sys.exit(1)

board_width = int(board_match.group(1))
board_height = int(board_match.group(2))

# SES uses the same coordinate system as DSN export from pcb-rnd
# pcb-rnd DSN export: origin at bottom-left, y increases upward
# pcb-rnd internal: origin at top-left, y increases downward
# So y_pcb = board_height - y_ses

def ses_to_pcb_coords(x, y):
    """Convert SES coordinates to pcb-rnd coordinates."""
    # SES coordinates are in the same units as PCB (nanometers here based on resolution mm 1000000)
    # Actually, SES resolution is mm with 1000000 units per mm
    # But our PCB file uses nm units
    # SES coords are already in nm (the resolution line says mm 1000000, meaning 1mm = 1000000 units)
    # And pcb-rnd uses nm, where 1mm = 1000000nm
    # So units match! But y-axis is flipped.
    return (x, board_height - y)

# Generate PCB Line entries for each layer
layer_lines = {1: [], 2: []}

for layer_num, width, points in wires:
    for i in range(len(points) - 1):
        x1_ses, y1_ses = points[i]
        x2_ses, y2_ses = points[i + 1]
        x1, y1 = ses_to_pcb_coords(x1_ses, y1_ses)
        x2, y2 = ses_to_pcb_coords(x2_ses, y2_ses)
        # clearance = 2 * width (standard)
        clearance = 508000  # 0.508mm standard clearance
        line = f'\tLine[{x1}nm {y1}nm {x2}nm {y2}nm {width}nm {clearance}nm "clearline"]'
        if layer_num not in layer_lines:
            layer_lines[layer_num] = []
        layer_lines[layer_num].append(line)

# Generate via entries
via_entries = []
for x_ses, y_ses in vias:
    x, y = ses_to_pcb_coords(x_ses, y_ses)
    # Standard via: size=914400nm, drill=508000nm, mask=1066800nm, clearance=508000nm
    via_entry = f'Via[{x}nm {y}nm 914400nm 508000nm 1066800nm 508000nm "" ""]'
    via_entries.append(via_entry)

print(f"Generated {sum(len(v) for v in layer_lines.values())} trace segments and {len(via_entries)} vias")

# Insert lines into the correct Layer blocks in the PCB file
# Layer(1 "top") gets top copper traces
# Layer(2 "bottom") gets bottom copper traces

lines = pcb.split('\n')
output = []
i = 0
via_inserted = False

while i < len(lines):
    line = lines[i]
    output.append(line)

    # Insert vias before Layer section (they go at the top level)
    if not via_inserted and re.match(r'^Layer\(1 ', line):
        # Insert vias before Layer(1
        output.pop()  # remove the Layer line we just added
        for ve in via_entries:
            output.append(ve)
        output.append(line)  # re-add the Layer line
        via_inserted = True

    # Check if this is a Layer opening with "("
    layer_match = re.match(r'^Layer\((\d+)\s', line)
    if layer_match:
        layer_num = int(layer_match.group(1))
        # Next line should be "("
        i += 1
        if i < len(lines) and lines[i].strip() == '(':
            output.append(lines[i])  # the "("
            # Insert our lines for this layer
            if layer_num in layer_lines:
                for trace_line in layer_lines[layer_num]:
                    output.append(trace_line)
            i += 1
            continue

    i += 1

with open(pcb_file, 'w') as f:
    f.write('\n'.join(output))

print(f"Successfully injected routes into {pcb_file}")
