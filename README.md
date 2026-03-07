# Dual Z80 RetroShield Board

A modified [RetroShield](https://www.8bitforce.com/) kz80 board that adds a second Z80 processor in a shared-bus architecture. Both CPUs share address (A0–A15) and data (D0–D7) buses through a single Arduino Mega header, while CPU2 gets independent control signals via a small 2x6 pin header.

## Features

- **Shared-bus architecture** — single Arduino Mega header, no duplication
- **Independent CPU2 control** — CLK, RESET, INT, NMI, MREQ, IORQ, RD, WR, BUSRQ, BUSAK via J2
- **2-layer PCB** — 86.36mm × 53.34mm, autorouted with Freerouting
- **Production-ready** — Gerbers, BOM, and pick-and-place centroid included

## Board Layout

| Component | Description |
|-----------|-------------|
| U1 | Z80 CPU #1 (original) |
| U2 | Z80 CPU #2 (added) |
| J1 | Arduino Mega 2x18 header (shared buses) |
| J2 | 2x6 pin header (CPU2 control signals) |
| C1–C2, C4 | 100nF decoupling capacitors (0805) |
| C3, C5 | 22pF clock capacitors (0805) |
| R1, R2 | 33Ω clock series resistors (0805) |
| R3 | 680Ω LED current limiting resistor (0805) |
| LED1 | Bus activity indicator (3mm red) |

## J2 Pinout (CPU2 Control Header)

| Pin | Signal | Pin | Signal |
|-----|--------|-----|--------|
| 1 | +5V | 2 | GND |
| 3 | CLK_2 | 4 | RESET_2 |
| 5 | INT_2 | 6 | NMI_2 |
| 7 | MREQ_2 | 8 | IORQ_2 |
| 9 | RD_2 | 10 | WR_2 |
| 11 | BUSRQ_2 | 12 | BUSAK_2 |

## Files

### Production
- `kz80_production.zip` — Gerbers + BOM + centroid (ready for PCBWay/JLCPCB)
- `kz80_gerbers.zip` — Gerber files only
- `kz80_bom.csv` — Bill of materials (SMD components only)
- `kz80_centroid.csv` — Pick-and-place file

### Source
- `kz80.sch` — Main schematic (CPU1 + shared buses)
- `kz80_cpu2.sch` — CPU2 schematic page
- `kz80.pcb` — Routed PCB (pcb-rnd format)
- `*.sym` — gEDA/lepton-eda symbols

### Scripts
- `add_cpu2_shared.py` — Adds CPU2 elements and nets to the PCB
- `strip_traces.py` — Strips routed traces/vias for clean re-routing
- `ses_to_pcb.py` — Imports Freerouting SES output into pcb-rnd PCB format

### Documentation
- `dual_z80_build_log.md` — Detailed step-by-step build log

## Tools Used

- [lepton-eda](https://github.com/lepton-eda/lepton-eda) — Schematic capture
- [pcb-rnd](http://repo.hu/projects/pcb-rnd/) — PCB layout
- [Freerouting](https://github.com/freerouting/freerouting) — Autorouter

## License

BSD 3-Clause License. See [LICENSE](LICENSE).
