# J2 Wiring Guide: Arduino Mega to Second Z80 (U2)

## Overview

The J2 header is a 2x6 pin block that provides the control interface for the second Z80 processor (U2) on the Dual Z80 RetroShield board. The RetroShield's J1 header (40-pin) handles the shared data/address bus and U1 control signals using Arduino Mega pins D22-D53. J2 breaks out U2's independent control signals, which need to be wired to the Mega's free pins D0-D21.

## J2 Physical Layout

```
        Left      Right
Row 1:  [1]+5V    [2]GND
Row 2:  [3]CLK    [4]RESET
Row 3:  [5]INT    [6]NMI
Row 4:  [7]MREQ   [8]IORQ
Row 5:  [9]RD     [10]WR
Row 6:  [11]BUSRQ [12]BUSAK
```

Pin 1 is marked with a square pad.

## J2 Pinout

| J2 Pin | Signal | Z80-2 Pin | Direction | Description |
|--------|--------|-----------|-----------|-------------|
| 1 | +5V | - | Power | +5V supply |
| 2 | GND | - | Power | Ground |
| 3 | CLK_2 | U2-6 | Mega -> U2 | Clock input for second Z80 |
| 4 | RESET_2 | U2-26 | Mega -> U2 | Reset (active low) |
| 5 | INT_2 | U2-16 | Mega -> U2 | Interrupt request (active low) |
| 6 | NMI_2 | U2-17 | Mega -> U2 | Non-maskable interrupt (active low) |
| 7 | MREQ_2 | U2-19 | U2 -> Mega | Memory request (active low) |
| 8 | IORQ_2 | U2-20 | U2 -> Mega | I/O request (active low) |
| 9 | RD_2 | U2-21 | U2 -> Mega | Read strobe (active low) |
| 10 | WR_2 | U2-22 | U2 -> Mega | Write strobe (active low) |
| 11 | BUSRQ_2 | U2-25 | Mega -> U2 | Bus request (active low) |
| 12 | BUSAK_2 | U2-23 | U2 -> Mega | Bus acknowledge (active low) |

## Recommended Wiring

The RetroShield J1 header uses Mega pins D22-D53. Pins D0-D21 are free. Avoid D0/D1 (Serial) and D14-D21 (Serial1/2/3 TX/RX) if you need serial communication.

| J2 Pin | Signal | Mega Pin | Notes |
|--------|--------|----------|-------|
| 1 | +5V | +5V | Power rail |
| 2 | GND | GND | Ground rail |
| 3 | CLK_2 | **D9** | Timer1 OC1A — hardware PWM for stable clock |
| 4 | RESET_2 | **D4** | Drive LOW to hold U2 in reset |
| 5 | INT_2 | **D5** | Drive LOW to trigger maskable interrupt |
| 6 | NMI_2 | **D6** | Drive LOW to trigger non-maskable interrupt |
| 7 | MREQ_2 | **D7** | Read to monitor U2 memory requests |
| 8 | IORQ_2 | **D8** | Read to monitor U2 I/O requests |
| 9 | RD_2 | **D10** | Read to monitor U2 read cycles |
| 10 | WR_2 | **D11** | Read to monitor U2 write cycles |
| 11 | BUSRQ_2 | **D12** | Drive LOW to request U2 releases the bus |
| 12 | BUSAK_2 | **D13** | Read — goes LOW when U2 has released the bus |

## Clock Generation

D9 is recommended for CLK_2 because it is the Timer1 OC1A output, which can generate a precise hardware clock signal without CPU overhead.

### 4 MHz Clock

```cpp
// Timer1 CTC mode, toggle OC1A (D9) on compare match
// 16MHz / (2 * (1+1)) = 4MHz
TCCR1A = _BV(COM1A0);
TCCR1B = _BV(WGM12) | _BV(CS10);  // CTC mode, no prescaler
OCR1A = 1;
```

### Other Clock Speeds

| OCR1A | Frequency | Notes |
|-------|-----------|-------|
| 0 | 8 MHz | Maximum — may be too fast for some Z80 variants |
| 1 | 4 MHz | Standard Z80 clock speed |
| 3 | 2 MHz | Half speed — useful for debugging |
| 7 | 1 MHz | Slow — good for step-by-step observation |

Formula: `f = 16MHz / (2 * (OCR1A + 1))`

## Minimum Wiring

To get U2 running, you need at minimum:

- **+5V** (J2-1) and **GND** (J2-2) — power
- **CLK_2** (J2-3) — clock source
- **RESET_2** (J2-4) — release from reset to start execution

## Bus Coordination

To switch between U1 and U2 on the shared bus:

1. Assert BUSRQ_2 LOW (J2-11) to ask U2 to release the bus
2. Wait for BUSAK_2 LOW (J2-12) to confirm U2 has released
3. U1 now has exclusive bus access
4. Release BUSRQ_2 HIGH to give the bus back to U2

The RetroShield firmware manages U1's bus access through the standard BUSRQ/BUSAK mechanism on J1. Coordinating both processors requires managing both bus request/acknowledge handshakes so only one Z80 drives the address and data bus at a time.
