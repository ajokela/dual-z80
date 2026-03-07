#!/usr/bin/env python3
"""Strip all copper traces (Line entries in Layer blocks) from PCB file, keeping elements and netlist."""
import sys
import re

pcb_file = sys.argv[1]
with open(pcb_file, 'r') as f:
    content = f.read()

# Remove all Line[...] entries from Layer blocks (these are the copper traces)
# Keep ElementLine entries (those are inside Element blocks)
# Layer lines look like: \tLine[...] inside Layer(...) blocks

# Strategy: find Layer blocks and remove Line entries within them
lines = content.split('\n')
output = []
in_layer = False
layer_depth = 0

i = 0
while i < len(lines):
    line = lines[i]

    # Detect start of Layer block
    if re.match(r'^Layer\(\d+', line):
        in_layer = True
        layer_depth = 0
        output.append(line)
        i += 1
        continue

    if in_layer:
        # Track parentheses depth
        if line.strip() == '(':
            layer_depth += 1
            output.append(line)
            i += 1
            continue
        if line.strip() == ')':
            layer_depth -= 1
            if layer_depth <= 0:
                in_layer = False
            output.append(line)
            i += 1
            continue

        # Skip Line entries (traces) inside layer blocks
        if re.match(r'\s*Line\[', line):
            i += 1
            continue

        output.append(line)
    else:
        # Skip autorouted vias (914400nm size from ses_to_pcb.py)
        if re.match(r'^Via\[.*914400nm', line):
            i += 1
            continue
        output.append(line)

    i += 1

with open(pcb_file, 'w') as f:
    f.write('\n'.join(output))

print("Stripped all traces from PCB file.")
