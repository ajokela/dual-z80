# Adding a Second Z80 Processor to the RetroShield Board

## Complete Build Log

This document details every step taken to modify the RetroShield Z80 (kz80) board design to support dual Z80 processors sharing a single Arduino Mega header, using command-line EDA tools over SSH.

---

## Table of Contents

1. [Project Background](#project-background)
2. [Environment Setup](#environment-setup)
3. [Understanding the Original Design](#understanding-the-original-design)
4. [Architecture Decision: Shared Bus](#architecture-decision-shared-bus)
5. [Creating the Control Header Symbol](#creating-the-control-header-symbol)
6. [Designing the CPU2 Schematic](#designing-the-cpu2-schematic)
7. [Modifying the PCB Layout](#modifying-the-pcb-layout)
8. [Autorouting with Freerouting](#autorouting-with-freerouting)
9. [Importing Routes Back into the PCB](#importing-routes-back-into-the-pcb)
10. [Generating Gerber Files](#generating-gerber-files)
11. [Adding Silkscreen Text](#adding-silkscreen-text)
12. [Final File Summary](#final-file-summary)

---

## Project Background

The RetroShield Z80 is an open-source hardware project by Erturk Kocalar (8bitforce.com) that allows a real Z80 CPU to be controlled by an Arduino Mega 2560. The Arduino emulates memory and I/O, while the Z80 executes real instructions on actual silicon. The original design uses a single Z80 CPU connected to the Arduino Mega through a 2x18 pin header (36 pins), carrying address bus (A0-A15), data bus (D0-D7), and control signals (CLK, RESET, INT, NMI, MREQ, IORQ, RD, WR).

The goal of this project was to add a second Z80 processor to the board, allowing dual-CPU operation controlled by a single Arduino Mega.

The project files are located on a remote Linux machine at `alex@192.168.0.219` in the directory `~/Downloads/retroshield-hw-master/hardware/kz80/`.

All work was performed entirely via SSH using command-line tools — no GUI was used at any point.

---

## Environment Setup

### Remote Machine Access

All work was done over SSH to a remote Ubuntu 24.04 machine:

```
sshpass -p 'frankhead' ssh -o StrictHostKeyChecking=accept-new alex@192.168.0.219
```

### Tool Installation

The original project was built with classic gEDA tools (gschem, pcb, gsch2pcb), which are no longer packaged for Ubuntu 24.04. We installed modern replacements:

- **lepton-eda** — Modern fork of gEDA for schematic capture. Provides `lepton-schematic`, `lepton-sch2pcb`, `lepton-netlist`, and `lepton-cli`.
- **pcb-rnd** — PCB layout editor (already installed as part of the ringdove suite). Used for Gerber export and DSN export.
- **gerbv** — Gerber file viewer for verification.
- **Freerouting** — Java-based autorouter (`/tmp/freerouting.jar`), downloaded separately. Processes Specctra DSN files and outputs SES session files.
- **make** — Installed via `apt-get install make`.

### Makefile Updates

The project Makefile (`~/Downloads/retroshield-hw-master/hardware/kz80/makefile`) was updated from classic gEDA commands to lepton-eda equivalents:

- `gschem` → `lepton-schematic`
- `gsch2pcb` → `lepton-sch2pcb`
- `pcb` → `pcb-rnd`

The `renamepcb` script (`../../bin/renamepcb`) was rewritten in Python 3 to handle pcb-rnd's different Gerber output filename format (e.g., `kz80.top.copper.none.3.gbr` instead of the old `kz80.top.gbr`).

---

## Understanding the Original Design

### Original Schematic (kz80.sch)

The original single-page schematic contains:

| Component | Description |
|-----------|-------------|
| **U1** | Z80 CPU (DIP-40 package) |
| **J1** | 2x18 pin header (HEADER36_1 footprint) connecting to Arduino Mega pins 22-53 |
| **C1** | 100nF decoupling capacitor (0805) |
| **C2** | 100nF decoupling capacitor (0805) |
| **C3** | 22pF clock capacitor (0805) |
| **R1** | 33Ω clock series resistor (0805) |
| **R3** | 680Ω LED current-limiting resistor (0805) |
| **LED1** | Red LED (LED3 footprint) for bus activity indication |

The schematic uses gEDA format (text-based `.sch` files) with bus rippers connecting the address bus (ADDR) and data bus (DATA) to individual signal nets (A0-A15, D0-D7). Control signals (CLK, RESET, INT, NMI, MREQ, IORQ, RD, WR) are connected directly between the Z80 and the J1 header pins.

### J1 Header Pin Mapping (Arduino Mega Pins 22-53)

The 2x18 header maps to specific Arduino Mega port pins:

```
Pin 1:  +5V                    Pin 36: +5V
Pin 2:  PA0 (Arduino 22)       Pin 35: PA1 (Arduino 23)
Pin 3:  PA2 (Arduino 24)       Pin 34: PA3 (Arduino 25)
Pin 4:  PA4 (Arduino 26)       Pin 33: PA5 (Arduino 27)
Pin 5:  PA6 (Arduino 28)       Pin 32: PA7 (Arduino 29)
Pin 6:  PC7 (Arduino 30)       Pin 31: PC6 (Arduino 31)
Pin 7:  PC5 (Arduino 32)       Pin 30: PC4 (Arduino 33)
Pin 8:  PC3 (Arduino 34)       Pin 29: PC2 (Arduino 35)
Pin 9:  PC1 (Arduino 36)       Pin 28: PC0 (Arduino 37)
Pin 10: PD7 (Arduino 38)       Pin 27: PG2 (Arduino 39)
Pin 11: PG1 (Arduino 40)       Pin 26: PG0 (Arduino 41)
Pin 12: PL7 (Arduino 42)       Pin 25: PL6 (Arduino 43)
Pin 13: PL5 (Arduino 44)       Pin 24: PL4 (Arduino 45)
Pin 14: PL3 (Arduino 46)       Pin 23: PL2 (Arduino 47)
Pin 15: PL1 (Arduino 48)       Pin 22: PL0 (Arduino 49)
Pin 16: PB3 (Arduino 50)       Pin 21: PB2 (Arduino 51)
Pin 17: PB1 (Arduino 52)       Pin 20: PB0 (Arduino 53)
Pin 18: GND                    Pin 19: GND
```

### Original PCB (kz80.pcb)

The original PCB is 55.88mm × 53.34mm, a two-layer board with:
- Top copper (Layer 1) carrying most signal traces
- Bottom copper (Layer 2) as ground/power plane with some signal routing
- Through-hole components: J1 (2x18 header), U1 (DIP-40 Z80)
- SMD components: C1, C2, C3 (0805 caps), R1, R3 (0805 resistors), LED1

The PCB file format is pcb-rnd's text-based `.pcb` format, containing Element blocks (component footprints with pins/pads), Layer blocks (copper traces as Line entries), Via entries, and a NetList section defining electrical connectivity.

### Original Netlist

The original design has 37 nets:
- Power: `+5V`, `GND`
- Address bus: `A0` through `A15` (16 nets)
- Data bus: `D0` through `D7` (8 nets)
- Control signals: `\_INT\_`, `\_NMI\_`, `\_MREQ\_`, `\_IORQ\_`, `\_RD\_`, `\_WR\_`, `\_RESET\_`
- Clock: `CLK`, `CLK_E_R`
- LED: `BA_R`, `BA_LED`

---

## Architecture Decision: Shared Bus

### Initial (Incorrect) Approach

The first attempt added a second Z80 with its own independent 2x18 header (J2), giving each CPU completely separate address, data, and control buses. This would have required two Arduino Megas or a single Arduino Mega with enough pins for both CPUs independently.

This approach was rejected because:
1. The RetroShield is designed to plug into a **single** Arduino Mega
2. Having two large 36-pin headers would make the board too large
3. It doesn't reflect how real multi-processor Z80 systems worked

### Correct Approach: Shared Bus with Independent Control

After analysis, we determined the Arduino Mega 2560 has enough I/O pins for a shared-bus dual Z80 design:

**Currently used by J1:** Pins 22-53 = 32 I/O pins
**Remaining available:** Pins 2-21 (20 pins) + A0-A15 (16 analog pins usable as digital) = 36 pins

The shared-bus approach requires only ~10 additional pins for CPU2's control signals, well within the 36 available.

**Design principles:**
- Both Z80s share the same address bus (A0-A15) and data bus (D0-D7) through J1
- Each Z80 has independent control signals for bus arbitration
- A small supplementary 2x6 header (J2, 12 pins) carries CPU2's control signals to the Arduino's remaining pins
- The Arduino firmware manages bus arbitration using BUSRQ/BUSACK signals, giving each CPU its turn on the shared bus — this mirrors how real multi-processor Z80 systems operated

**J2 Pin Assignment (2x6 header, 12 pins):**

```
Pin 1:  +5V         Pin 2:  GND
Pin 3:  CLK_2       Pin 4:  RESET_2
Pin 5:  INT_2       Pin 6:  NMI_2
Pin 7:  MREQ_2      Pin 8:  IORQ_2
Pin 9:  RD_2        Pin 10: WR_2
Pin 11: BUSRQ_2     Pin 12: BUSAK_2
```

---

## Creating the Control Header Symbol

A new gEDA symbol file was created for the 2x6 control header: `symbols/ctrlhdr2x6-1.sym`.

This symbol defines a rectangular component body (1400×2000 mils) with:
- 6 pins on the left side (pins 1, 3, 5, 7, 9, 11)
- 6 pins on the right side (pins 2, 4, 6, 8, 10, 12)
- Pin spacing: 300 mils (matching standard 0.1" pitch)
- Pin labels matching the control signal names (CLK, RESET, INT, NMI, MREQ, IORQ, RD, WR, BUSRQ, BUSAK, +5V, GND)
- Footprint attribute: `HEADER12_1`
- Device attribute: `CTRLHDR2X6`

The symbol file was written locally and transferred to the remote machine via SCP:

```bash
scp ctrlhdr2x6-1.sym alex@192.168.0.219:~/Downloads/retroshield-hw-master/hardware/kz80/symbols/
```

---

## Designing the CPU2 Schematic

A new schematic page was created: `kz80_cpu2.sch` (page 2 of 2).

### Multi-Page Schematic Net Sharing

In gEDA/lepton-eda, nets with the same name on different schematic pages are automatically connected. This is the key mechanism that makes the shared bus work:

- Page 1 (`kz80.sch`): J1 header pins connect to nets named `A0`, `A1`, ..., `A15`, `D0`, `D1`, ..., `D7`
- Page 2 (`kz80_cpu2.sch`): U2's address and data pins connect to nets with the **same names** (`A0`, `A1`, ..., `A15`, `D0`, `D1`, ..., `D7`)
- The netlister automatically merges these into shared nets

### CPU2 Schematic Components

| Component | Description | Notes |
|-----------|-------------|-------|
| **U2** | Z80 CPU (DIP-40, z80-1.sym) | Same symbol as U1 |
| **J2** | 2x6 control header (ctrlhdr2x6-1.sym) | New custom symbol |
| **C4** | 100nF decoupling capacitor (0805) | For U2's VCC pin |
| **C5** | 22pF clock capacitor (0805) | For U2's CLK circuit |
| **R2** | 33Ω series resistor (0805) | CLK_2 signal conditioning |

### Schematic Connections

**Shared bus connections (same net names as page 1):**
- U2 address pins → bus rippers → ADDR bus → nets A0-A15
- U2 data pins → bus rippers → DATA bus → nets D0-D7

**Independent control signals (new nets with `_2` suffix):**
- J2 pin 3 → `CLK_2` → R2 → `CLK_2_R` → U2 CLK (pin 6)
- J2 pin 4 → `\_RESET_2\_` → U2 RESET (pin 26)
- J2 pin 5 → `\_INT_2\_` → U2 INT (pin 16)
- J2 pin 6 → `\_NMI_2\_` → U2 NMI (pin 17)
- U2 MREQ (pin 19) → `\_MREQ_2\_` → J2 pin 7
- U2 IORQ (pin 20) → `\_IORQ_2\_` → J2 pin 8
- U2 RD (pin 21) → `\_RD_2\_` → J2 pin 9
- U2 WR (pin 22) → `\_WR_2\_` → J2 pin 10
- J2 pin 11 → `\_BUSRQ_2\_` → U2 BUSRQ (pin 25)
- U2 BUSAK (pin 23) → `\_BUSAK_2\_` → J2 pin 12

**Power connections:**
- J2 pin 1 (+5V) and J2 pin 2 (GND) for header power
- U2 VCC (pin 11) and U2 GND (pin 29) tied to +5V and GND
- U2 WAIT (pin 24) tied to +5V (active low, so high = not waiting)
- C4 across U2's power pins for decoupling
- C5 on U2's clock circuit

### Project File Update

The `project` file was updated to include both schematic pages:

```
schematics kz80.sch kz80_cpu2.sch
output-name kz80
```

---

## Modifying the PCB Layout

Since `lepton-sch2pcb` had issues finding footprints in pcb-rnd's library paths, we used a Python script (`add_cpu2_shared.py`) to directly modify the PCB file. This approach was more reliable for programmatic PCB manipulation.

### Step 1: Restore Original PCB

The original PCB was restored from backup to ensure a clean starting point:

```bash
cp kz80.pcb.bak kz80.pcb
```

### Step 2: Run the PCB Modification Script

The Python script (`/tmp/add_cpu2_shared.py`) performed the following modifications:

#### Board Size

Widened the board from 55.88mm × 53.34mm to **86.36mm × 53.34mm** (+30.48mm to accommodate the second Z80 and control header):

```python
content = content.replace(
    'PCB["" 55880000nm 53340000nm]',
    'PCB["" 86360000nm 53340000nm]'
)
```

#### New Element Footprints

Five new Element blocks were inserted into the PCB file, placed on the right half of the widened board:

**U2 — Z80 DIP-40** (placed at x=62mm, y=2.54mm):
- 40 through-hole pins in dual-inline configuration
- Pin spacing: 2.54mm (100 mil)
- Row spacing: 15.24mm (600 mil)
- Pin diameter: 1.524mm, drill: 0.965mm
- Silk outline with pin 1 indicator notch

**J2 — 2x6 Header** (placed at x=58mm, y=2.54mm):
- 12 through-hole pins in 2×6 configuration
- Pin spacing: 2.54mm (100 mil)
- Row spacing: 2.54mm (100 mil)
- Pin 1 marked as square pad
- Silk outline with pin 1 corner mark

**C4 — 100nF Capacitor** (0805 SMD, placed at x=72mm, y=2.54mm):
- Two SMD pads, 0805 footprint
- Connected to +5V and GND for U2 decoupling

**C5 — 22pF Capacitor** (0805 SMD, placed at x=60mm, y=16.51mm):
- Two SMD pads, 0805 footprint
- Part of U2's clock circuit

**R2 — 33Ω Resistor** (0805 SMD, placed at x=58mm, y=49.53mm):
- Two SMD pads, 0805 footprint
- Series resistor in CLK_2 path

#### Netlist Updates

The script modified the NetList section of the PCB file in two ways:

**1. Added U2 pins to existing shared nets:**

For each shared net (A0-A15, D0-D7, +5V, GND), the script found the net block and inserted additional `Connect("U2-xx")` entries. For example, the A0 net went from:

```
Net("A0" "(unknown)")
(
    Connect("J1-2")
    Connect("U1-30")
)
```

To:

```
Net("A0" "(unknown)")
(
    Connect("J1-2")
    Connect("U1-30")
    Connect("U2-30")
)
```

The +5V net received: `U2-11` (VCC), `U2-24` (WAIT, tied high), `C4-2`, `J2-1`
The GND net received: `U2-29` (GND), `C4-1`, `C5-2`, `J2-2`

**2. Created 11 new nets for CPU2 control signals:**

```
\_BUSAK_2\_  → J2-12, U2-23
\_BUSRQ_2\_ → J2-11, U2-25
\_INT_2\_    → J2-5, U2-16
\_IORQ_2\_  → J2-8, U2-20
\_MREQ_2\_  → J2-7, U2-19
\_NMI_2\_   → J2-6, U2-17
\_RD_2\_    → J2-9, U2-21
\_RESET_2\_ → J2-4, U2-26
\_WR_2\_    → J2-10, U2-22
CLK_2       → C5-1, R2-1, U2-6
CLK_2_R     → J2-3, R2-2
```

**Total nets after modification: 48** (37 original + 11 new)

### Step 3: Strip Existing Traces

Before autorouting, all existing copper traces (Line entries inside Layer blocks) were removed using a second Python script (`strip_traces.py`). This was necessary because:

1. The existing traces only connected the original single-CPU components
2. Freerouting needs to route from scratch to properly handle the shared bus topology
3. The existing traces caused "net not found" warnings in Freerouting's DSN import because pcb-rnd's DSN exporter uses different net name encoding

The script parsed the PCB file line by line, identifying Layer blocks and removing all `Line[...]` entries within them while preserving `ElementLine[...]` entries (which are part of component footprints, not copper traces).

---

## Autorouting with Freerouting

### DSN Export

The modified PCB (with new components but no traces) was exported to Specctra DSN format using pcb-rnd's command-line exporter:

```bash
pcb-rnd -x dsn kz80.pcb
```

This produced `kz80.dsn` (16KB — much smaller than the 41KB version that included existing traces).

### Running Freerouting

Freerouting was run in headless mode with a maximum of 20 routing passes:

```bash
java -jar /tmp/freerouting.jar -de kz80.dsn -do kz80.ses -mp 20
```

**Routing progress:**
- Passes 1-10: Initial routing, 3-4 seconds per pass
- Passes 11-20: Refinement, 3-5 seconds per pass
- Passes 21-59: Optimization (Freerouting continued beyond the 20-pass limit to optimize trace length)
- Final convergence at pass 59 with the message: "There were only 10.60 track length increase in the last 5 passes, so it's very likely that autorouter can't improve the result further."

**Total routing time: ~3 minutes** (compared to 40+ minutes when existing traces confused the router)

The router produced `kz80.ses` (53KB), containing all routed wire paths and via placements.

### First Attempt (Failed)

The initial autorouting attempt included the original board's existing traces in the DSN export. This caused Freerouting to spend 50+ seconds per pass trying to work around traces it couldn't associate with nets (all those "net not found" warnings). After 48 passes and 40 minutes, it was still failing to route several nets. The solution was to strip all traces first and let Freerouting route from a clean slate.

---

## Importing Routes Back into the PCB

### The Challenge

pcb-rnd's SES import functionality requires the GUI — it doesn't work in headless/CLI mode. Multiple approaches were attempted:

1. `pcb-rnd -x ses` — SES is not a valid export format (it's an import)
2. `pcb-rnd --import-ses` — Launched the GUI and hung waiting for display interaction
3. `xvfb-run pcb-rnd -a "ImportSes(...)"` — GTK widget errors, also hung

### The Solution: Custom SES-to-PCB Converter

A Python script (`ses_to_pcb.py`) was written to parse the Freerouting SES file and inject the routes directly into the pcb-rnd PCB file as copper trace Line entries.

**SES File Format:**

The SES file contains a `(routes ...)` section with `(network_out ...)` containing wire definitions:

```
(net A0
  (wire
    (path 3__top_copper 254000
      x1 y1
      x2 y2
      ...
      xn yn
    )
  )
)
```

Each wire is a polyline path on a specific copper layer with a given trace width.

**Coordinate System Conversion:**

The SES file uses a coordinate system with the origin at the bottom-left (y increases upward), while pcb-rnd uses origin at the top-left (y increases downward). The conversion is:

```python
y_pcb = board_height - y_ses
```

Both systems use nanometers as the unit (1mm = 1,000,000 units).

**Layer Mapping:**

```python
layer_map = {
    '3__top_copper': 1,       # Layer(1 "top")
    '6__bottom_copper': 2,    # Layer(2 "bottom")
}
```

**Via Handling:**

Vias in the SES file are simple `(via pstk_N x y)` entries. These were converted to pcb-rnd Via entries with standard dimensions:

```
Via[x y 914400nm 508000nm 1066800nm 508000nm "" ""]
```
(914.4µm pad, 508µm drill, 1066.8µm mask opening, 508µm clearance)

**Results:**

The converter successfully extracted and injected:
- **191 wires** decomposed into **897 individual trace segments**
- **82 vias** for layer transitions

---

## Generating Gerber Files

### Gerber Export

pcb-rnd's command-line Gerber exporter was used:

```bash
pcb-rnd -x gerber --all-layers kz80.pcb
```

This produced 11 Gerber files with pcb-rnd's verbose naming convention.

### File Renaming

The `renamepcb` script (Python 3) renamed files to standard Gerber extensions used by PCB fabrication houses:

| pcb-rnd Output | Standard Extension | Layer |
|----------------|-------------------|-------|
| `kz80.top.copper.none.3.gbr` | `kz80.gtl` | Top copper |
| `kz80.bottom.copper.none.6.gbr` | `kz80.gbl` | Bottom copper |
| `kz80.top.mask.none.2.gbr` | `kz80.gts` | Top solder mask |
| `kz80.bottom.mask.none.7.gbr` | `kz80.gbs` | Bottom solder mask |
| `kz80.top.silk.none.1.gbr` | `kz80.gto` | Top silkscreen |
| `kz80.bottom.silk.none.8.gbr` | `kz80.gbo` | Bottom silkscreen |
| `kz80.top.paste.none.0.gbr` | `kz80.gtp` | Top solder paste |
| `kz80.bottom.paste.none.9.gbr` | `kz80.gbp` | Bottom solder paste |
| `kz80.global.boundary.uroute.5.gbr` | `kz80.gko` | Board outline |
| `kz80.global.virtual.pdrill.none.gbr` | `kz80.drl` | Drill file |

### Zip Archive

All Gerber files were packaged into `kz80_gerbers.zip` (35KB) for submission to PCB fabrication services.

---

## Adding Silkscreen Text

### URL Addition

The text `tinycomputers.io` was added to the top silkscreen layer (Layer 5) directly below the existing `www.8bitforce.com` text.

The existing text was located at:
```
Text[8065700nm 23120800nm 0 100 "www.8bitforce.com" "clearline"]
```

The new text was placed 2.54mm below (y offset +2540000nm) with identical formatting:
```
Text[8065700nm 25660800nm 0 100 "tinycomputers.io" "clearline"]
```

Parameters: x=8065700nm, y=25660800nm, direction=0 (horizontal), scale=100, flags="clearline" (text clears copper beneath it).

Gerber files were regenerated after this change.

---

## Final File Summary

### Files on Remote Machine (`~/Downloads/retroshield-hw-master/hardware/kz80/`)

| File | Description |
|------|-------------|
| `kz80.sch` | Original schematic — CPU1, J1 header, passives, LED (unchanged) |
| `kz80_cpu2.sch` | New schematic — CPU2 with shared bus and J2 control header |
| `symbols/ctrlhdr2x6-1.sym` | New gEDA symbol for 2x6 control header |
| `symbols/z80-1.sym` | Existing Z80 CPU symbol (unchanged) |
| `symbols/megahdr2x18-1.sym` | Existing Arduino Mega header symbol (unchanged) |
| `project` | Updated project file listing both schematic pages |
| `kz80.pcb` | Final routed PCB with both CPUs (897 traces, 82 vias) |
| `kz80.pcb.bak` | Backup of original single-CPU PCB |
| `kz80.dsn` | Specctra DSN export (input to autorouter) |
| `kz80.ses` | Freerouting session file (autorouter output) |
| `kz80_gerbers.zip` | Production-ready Gerber files |
| `gerbers/` | Individual Gerber files (gtl, gbl, gts, gbs, gto, gbo, gtp, gbp, gko, drl) |
| `makefile` | Updated build file using lepton-eda commands |

### Board Specifications

| Parameter | Original | Dual CPU |
|-----------|----------|----------|
| Board width | 55.88mm | 86.36mm |
| Board height | 53.34mm | 53.34mm |
| Layers | 2 | 2 |
| Z80 CPUs | 1 | 2 |
| Header pins | 36 (J1) | 36 (J1) + 12 (J2) = 48 |
| Nets | 37 | 48 |
| Through-hole components | 2 (U1, J1) | 4 (U1, U2, J1, J2) |
| SMD components | 6 (C1-C3, R1, R3, LED1) | 9 (C1-C5, R1-R2, R3, LED1) |

### Helper Scripts Used

| Script | Location | Purpose |
|--------|----------|---------|
| `add_cpu2_shared.py` | `/tmp/` (remote) | Adds CPU2 elements and nets to PCB file |
| `strip_traces.py` | `/tmp/` (remote) | Removes all copper traces from PCB file |
| `ses_to_pcb.py` | `/tmp/` (remote) | Converts Freerouting SES routes to pcb-rnd Line entries |
| `renamepcb` | `../../bin/` (remote) | Renames pcb-rnd Gerber files to standard extensions |
