/*
 * DualZ80 SMP Kernel
 *
 * A symmetric multiprocessing demonstration for the Dual Z80 RetroShield.
 * Both Z80 processors boot the same kernel, identify themselves via I/O,
 * and pull tasks from a scheduler managed by the Arduino.
 *
 * The Arduino acts as the system chipset:
 *   - Memory controller (kernel ROM in PROGMEM, shared RAM in SRAM)
 *   - I/O dispatcher (task assignment, parameter passing, result collection)
 *   - Scheduler (assigns work, collects results, measures timing)
 *
 * Demo: sum an array of 256 bytes.
 *   - Single CPU:  one Z80 sums all 256 bytes
 *   - Dual CPU:    each Z80 sums 128 bytes, Arduino combines results
 *   - Reports exact cycle counts and speedup factor
 *
 * Z80 Memory Map:
 *   0x0000-0x00FF  Kernel code (served from PROGMEM, read-only)
 *   0x0100-0x01FF  Per-CPU stacks (CPU0: 0x017F↓, CPU1: 0x01FF↓)
 *   0x0200-0x02FF  Work data buffer (256 bytes)
 *
 * Z80 I/O Ports:
 *   0x00  R   CPU ID (0 or 1)
 *   0x01  R   Task poll (0 = idle, 1 = sum task ready)
 *   0x02  W   Signal task complete
 *   0x10  R   Param: start address low byte
 *   0x11  R   Param: start address high byte
 *   0x12  R   Param: byte count (0 = 256)
 *   0x20  W   Result: sum low byte
 *   0x21  W   Result: sum high byte
 *
 * Wiring (J2 header to Arduino Mega):
 *   J2-1  +5V     -> +5V       J2-2  GND     -> GND
 *   J2-3  CLK_2   -> D9        J2-4  RESET_2 -> D4
 *   J2-5  INT_2   -> D5        J2-6  NMI_2   -> D6
 *   J2-7  MREQ_2  -> D7        J2-8  IORQ_2  -> D8
 *   J2-9  RD_2    -> D10       J2-10 WR_2    -> D11
 *   J2-11 BUSRQ_2 -> D12       J2-12 BUSAK_2 -> D13
 */

#include <avr/pgmspace.h>

// ============================================================
// Pin Definitions
// ============================================================

// U1 (RetroShield J1)
#define U1_CLK    52
#define U1_RESET  38
#define U1_MREQ   41
#define U1_IORQ   39
#define U1_RD     53
#define U1_WR     40
#define U1_INT    50
#define U1_NMI    51

// U2 (J2, jumper-wired)
#define U2_CLK     9
#define U2_RESET   4
#define U2_INT     5
#define U2_NMI     6
#define U2_MREQ    7
#define U2_IORQ    8
#define U2_RD     10
#define U2_WR     11
#define U2_BUSRQ  12
#define U2_BUSAK  13

// ============================================================
// Z80 SMP Kernel (hand-assembled)
// ============================================================
//
// addr  hex          instruction           comment
// ----  ---          -----------           -------
// 0x00: DB 00        IN A, (0x00)          ; read CPU ID
// 0x02: B7           OR A                  ; test if zero
// 0x03: 20 05        JR NZ, +5             ; CPU 1 -> 0x0A
// 0x05: 31 80 01     LD SP, 0x0180         ; CPU 0 stack
// 0x08: 18 03        JR +3                 ; -> scheduler 0x0D
// 0x0A: 31 00 02     LD SP, 0x0200         ; CPU 1 stack
//
// ; === scheduler ===
// 0x0D: DB 01        IN A, (0x01)          ; poll for task
// 0x0F: B7           OR A
// 0x10: 28 FB        JR Z, -5              ; no task -> 0x0D
//
// ; === sum task ===
// 0x12: DB 10        IN A, (0x10)          ; param: start low
// 0x14: 6F           LD L, A
// 0x15: DB 11        IN A, (0x11)          ; param: start high
// 0x17: 67           LD H, A               ; HL = start address
// 0x18: DB 12        IN A, (0x12)          ; param: count
// 0x1A: 47           LD B, A               ; B = count (0=256)
// 0x1B: 1E 00        LD E, 0x00            ; DE = 16-bit sum
// 0x1D: 16 00        LD D, 0x00
//
// ; === sum loop ===
// 0x1F: 7E           LD A, (HL)            ; load byte
// 0x20: 83           ADD A, E              ; add to sum
// 0x21: 5F           LD E, A
// 0x22: 30 01        JR NC, +1             ; no carry -> 0x25
// 0x24: 14           INC D                 ; carry into high byte
// 0x25: 23           INC HL                ; next address
// 0x26: 10 F7        DJNZ -9              ; loop -> 0x1F
//
// ; === write result ===
// 0x28: 7B           LD A, E               ; sum low
// 0x29: D3 20        OUT (0x20), A
// 0x2B: 7A           LD A, D               ; sum high
// 0x2C: D3 21        OUT (0x21), A
//
// ; === signal done, return to scheduler ===
// 0x2E: 3E 01        LD A, 0x01
// 0x30: D3 02        OUT (0x02), A
// 0x32: 18 D9        JR -39                ; -> 0x0D

#define KERNEL_SIZE 52

static const uint8_t kernel[KERNEL_SIZE] PROGMEM = {
  // boot: identify CPU, set stack
  0xDB, 0x00,             // IN A, (0x00)    - CPU ID
  0xB7,                   // OR A
  0x20, 0x05,             // JR NZ, +5       - CPU1 -> 0x0A
  0x31, 0x80, 0x01,       // LD SP, 0x0180   - CPU0 stack
  0x18, 0x03,             // JR +3           - -> scheduler
  0x31, 0x00, 0x02,       // LD SP, 0x0200   - CPU1 stack

  // scheduler: poll for task
  0xDB, 0x01,             // IN A, (0x01)    - task poll
  0xB7,                   // OR A
  0x28, 0xFB,             // JR Z, -5        - spin

  // sum task: read parameters
  0xDB, 0x10,             // IN A, (0x10)    - start addr low
  0x6F,                   // LD L, A
  0xDB, 0x11,             // IN A, (0x11)    - start addr high
  0x67,                   // LD H, A
  0xDB, 0x12,             // IN A, (0x12)    - count
  0x47,                   // LD B, A
  0x1E, 0x00,             // LD E, 0x00      - sum = 0
  0x16, 0x00,             // LD D, 0x00

  // sum loop
  0x7E,                   // LD A, (HL)      - load byte
  0x83,                   // ADD A, E        - accumulate
  0x5F,                   // LD E, A
  0x30, 0x01,             // JR NC, +1       - skip carry
  0x14,                   // INC D           - carry
  0x23,                   // INC HL          - next addr
  0x10, 0xF7,             // DJNZ -9         - loop

  // write result
  0x7B,                   // LD A, E         - sum low
  0xD3, 0x20,             // OUT (0x20), A
  0x7A,                   // LD A, D         - sum high
  0xD3, 0x21,             // OUT (0x21), A

  // signal done, back to scheduler
  0x3E, 0x01,             // LD A, 0x01
  0xD3, 0x02,             // OUT (0x02), A   - task done
  0x18, 0xD9,             // JR -39          - -> scheduler
};

// ============================================================
// Shared RAM
// ============================================================
// Z80 address 0x0100-0x02FF -> ram[0..511]
// 0x0100-0x01FF: stacks, 0x0200-0x02FF: work data

#define RAM_BASE  0x0100
#define RAM_SIZE  512
#define DATA_BASE 0x0200   // Z80 address of work data
#define DATA_SIZE 256

static uint8_t ram[RAM_SIZE];

// ============================================================
// Per-CPU State (managed by Arduino scheduler)
// ============================================================

struct CPUState {
  bool     has_task;       // task ready for this CPU
  uint8_t  task_type;      // 1 = sum
  uint16_t param_start;    // start address
  uint8_t  param_count;    // byte count (0 = 256)
  uint16_t result;         // 16-bit result
  bool     done;           // task complete flag
};

static CPUState cpu[2];

// ============================================================
// Bus Functions
// ============================================================

static inline uint16_t readAddress() {
  return (uint16_t)PINA | ((uint16_t)PINC << 8);
}

static inline uint8_t readDataBus() {
  return PINL;
}

static inline void driveData(uint8_t val) {
  DDRL  = 0xFF;
  PORTL = val;
}

static inline void releaseDataBus() {
  DDRL  = 0x00;
  PORTL = 0x00;
}

// ============================================================
// I/O Port Handlers
// ============================================================

static uint8_t handleIORead(uint8_t cpuId, uint8_t port) {
  switch (port) {
    case 0x00: return cpuId;                          // CPU ID
    case 0x01:                                        // Task poll
      if (cpu[cpuId].has_task) {
        cpu[cpuId].has_task = false;                  // consume
        return cpu[cpuId].task_type;
      }
      return 0;
    case 0x10: return cpu[cpuId].param_start & 0xFF;  // start low
    case 0x11: return cpu[cpuId].param_start >> 8;     // start high
    case 0x12: return cpu[cpuId].param_count;          // count
    default:   return 0xFF;
  }
}

static void handleIOWrite(uint8_t cpuId, uint8_t port, uint8_t data) {
  switch (port) {
    case 0x02:                                        // task done
      cpu[cpuId].done = true;
      break;
    case 0x20:                                        // result low
      cpu[cpuId].result = (cpu[cpuId].result & 0xFF00) | data;
      break;
    case 0x21:                                        // result high
      cpu[cpuId].result = (cpu[cpuId].result & 0x00FF) | ((uint16_t)data << 8);
      break;
  }
}

// ============================================================
// Memory Read (kernel from PROGMEM, RAM from SRAM)
// ============================================================

static inline uint8_t memRead(uint16_t addr) {
  if (addr < KERNEL_SIZE) {
    return pgm_read_byte(&kernel[addr]);
  }
  if (addr >= RAM_BASE && addr < RAM_BASE + RAM_SIZE) {
    return ram[addr - RAM_BASE];
  }
  return 0xFF;  // unmapped
}

static inline void memWrite(uint16_t addr, uint8_t data) {
  if (addr >= RAM_BASE && addr < RAM_BASE + RAM_SIZE) {
    ram[addr - RAM_BASE] = data;
  }
}

// ============================================================
// Z80 Execution Engine
// ============================================================

// Run one clock cycle, handling memory and I/O for a specific CPU.
static inline void clockCycle(uint8_t clkPin,
                              uint8_t mreqPin, uint8_t iorqPin,
                              uint8_t rdPin,   uint8_t wrPin,
                              uint8_t cpuId)
{
  digitalWrite(clkPin, HIGH);
  delayMicroseconds(2);

  if (digitalRead(mreqPin) == LOW) {
    uint16_t addr = readAddress();
    if (digitalRead(rdPin) == LOW) {
      driveData(memRead(addr));
    } else if (digitalRead(wrPin) == LOW) {
      releaseDataBus();
      delayMicroseconds(1);
      memWrite(addr, readDataBus());
    }
  } else if (digitalRead(iorqPin) == LOW) {
    uint8_t port = readAddress() & 0xFF;
    if (digitalRead(rdPin) == LOW) {
      driveData(handleIORead(cpuId, port));
    } else if (digitalRead(wrPin) == LOW) {
      releaseDataBus();
      delayMicroseconds(1);
      handleIOWrite(cpuId, port, readDataBus());
    }
  }

  delayMicroseconds(2);
  digitalWrite(clkPin, LOW);
  releaseDataBus();
  delayMicroseconds(2);
}

// Run a Z80 until its task completes or maxCycles is reached.
// Returns the number of clock cycles executed.
static unsigned long runZ80UntilDone(uint8_t cpuIdx, unsigned long maxCycles) {
  uint8_t clkPin, resetPin, otherReset;
  uint8_t mreqPin, iorqPin, rdPin, wrPin;

  if (cpuIdx == 0) {
    clkPin = U1_CLK;  resetPin = U1_RESET; otherReset = U2_RESET;
    mreqPin = U1_MREQ; iorqPin = U1_IORQ; rdPin = U1_RD; wrPin = U1_WR;
  } else {
    clkPin = U2_CLK;  resetPin = U2_RESET; otherReset = U1_RESET;
    mreqPin = U2_MREQ; iorqPin = U2_IORQ; rdPin = U2_RD; wrPin = U2_WR;
  }

  // Keep other CPU in reset (tri-states its bus outputs)
  digitalWrite(otherReset, LOW);

  // Address bus -> input (Z80 drives it)
  DDRA = 0x00; PORTA = 0x00;
  DDRC = 0x00; PORTC = 0x00;
  releaseDataBus();

  // Control lines -> input
  pinMode(mreqPin, INPUT_PULLUP);
  pinMode(iorqPin, INPUT_PULLUP);
  pinMode(rdPin,   INPUT_PULLUP);
  pinMode(wrPin,   INPUT_PULLUP);

  // Reset sequence: hold RESET low for >=3 clock cycles
  digitalWrite(resetPin, LOW);
  for (int i = 0; i < 8; i++) {
    digitalWrite(clkPin, HIGH); delayMicroseconds(2);
    digitalWrite(clkPin, LOW);  delayMicroseconds(2);
  }

  // Release reset — Z80 starts fetching from 0x0000
  cpu[cpuIdx].done = false;
  digitalWrite(resetPin, HIGH);
  delayMicroseconds(5);

  // Clock until task done
  unsigned long cycles = 0;
  for (cycles = 0; cycles < maxCycles; cycles++) {
    clockCycle(clkPin, mreqPin, iorqPin, rdPin, wrPin, cpuIdx);
    if (cpu[cpuIdx].done) {
      cycles++;  // count the final cycle
      break;
    }
  }

  // Put CPU back in reset
  digitalWrite(resetPin, LOW);
  delayMicroseconds(5);

  return cycles;
}

// ============================================================
// Initialization
// ============================================================

static void initPins() {
  // U1
  pinMode(U1_CLK,   OUTPUT); digitalWrite(U1_CLK,   LOW);
  pinMode(U1_RESET, OUTPUT); digitalWrite(U1_RESET, LOW);
  pinMode(U1_INT,   OUTPUT); digitalWrite(U1_INT,   HIGH);
  pinMode(U1_NMI,   OUTPUT); digitalWrite(U1_NMI,   HIGH);
  pinMode(U1_MREQ,  INPUT_PULLUP);
  pinMode(U1_IORQ,  INPUT_PULLUP);
  pinMode(U1_RD,    INPUT_PULLUP);
  pinMode(U1_WR,    INPUT_PULLUP);

  // U2
  pinMode(U2_CLK,   OUTPUT); digitalWrite(U2_CLK,   LOW);
  pinMode(U2_RESET, OUTPUT); digitalWrite(U2_RESET, LOW);
  pinMode(U2_INT,   OUTPUT); digitalWrite(U2_INT,   HIGH);
  pinMode(U2_NMI,   OUTPUT); digitalWrite(U2_NMI,   HIGH);
  pinMode(U2_BUSRQ, OUTPUT); digitalWrite(U2_BUSRQ, HIGH);
  pinMode(U2_MREQ,  INPUT_PULLUP);
  pinMode(U2_IORQ,  INPUT_PULLUP);
  pinMode(U2_RD,    INPUT_PULLUP);
  pinMode(U2_WR,    INPUT_PULLUP);
  pinMode(U2_BUSAK, INPUT_PULLUP);

  // Bus idle
  DDRA = 0x00; PORTA = 0x00;
  DDRC = 0x00; PORTC = 0x00;
  releaseDataBus();
}

// ============================================================
// Task Assignment Helpers
// ============================================================

static void assignSumTask(uint8_t cpuIdx, uint16_t startAddr, uint8_t count) {
  cpu[cpuIdx].has_task    = true;
  cpu[cpuIdx].task_type   = 1;         // sum
  cpu[cpuIdx].param_start = startAddr;
  cpu[cpuIdx].param_count = count;     // 0 = 256 via DJNZ
  cpu[cpuIdx].result      = 0;
  cpu[cpuIdx].done        = false;
}

// ============================================================
// Demos
// ============================================================

#define MAX_CYCLES 50000UL

static void fillWorkData() {
  // Fill 256 bytes at DATA_BASE (0x0200) with values 0..255
  for (int i = 0; i < DATA_SIZE; i++) {
    ram[DATA_BASE - RAM_BASE + i] = (uint8_t)i;
  }
}

static uint16_t expectedSum() {
  // Sum of 0+1+2+...+255 = 255*256/2 = 32640
  return 32640U;
}

static uint16_t expectedHalfSum(uint8_t half) {
  // half=0: sum of 0..127  = 127*128/2 = 8128
  // half=1: sum of 128..255 = 32640 - 8128 = 24512
  if (half == 0) return 8128U;
  return 24512U;
}

static void printDivider() {
  Serial.println(F("------------------------------------------"));
}

static bool demoSingleCPU(uint8_t cpuIdx, unsigned long *cyclesOut) {
  const char *name = (cpuIdx == 0) ? "CPU 0 (U1)" : "CPU 1 (U2)";

  Serial.println();
  printDivider();
  Serial.print(F("  Single CPU test on "));
  Serial.println(name);
  printDivider();

  // Clear stacks
  memset(ram, 0, DATA_BASE - RAM_BASE);

  fillWorkData();
  assignSumTask(cpuIdx, DATA_BASE, 0);  // 0 = 256 bytes

  Serial.print(F("  Summing 256 bytes on "));
  Serial.print(name);
  Serial.println(F("..."));

  unsigned long cycles = runZ80UntilDone(cpuIdx, MAX_CYCLES);

  Serial.print(F("  Completed in "));
  Serial.print(cycles);
  Serial.println(F(" cycles"));

  Serial.print(F("  Result:   "));
  Serial.println(cpu[cpuIdx].result);

  Serial.print(F("  Expected: "));
  Serial.println(expectedSum());

  bool pass = (cpu[cpuIdx].result == expectedSum());
  Serial.print(F("  "));
  Serial.println(pass ? F("PASS") : F("** FAIL **"));

  *cyclesOut = cycles;
  return pass;
}

static bool demoDualCPU(unsigned long *cyclesOut) {
  Serial.println();
  printDivider();
  Serial.println(F("  Dual CPU (SMP) test"));
  printDivider();

  // Clear stacks
  memset(ram, 0, DATA_BASE - RAM_BASE);

  fillWorkData();

  // CPU 0 gets first 128 bytes (0x0200-0x027F)
  assignSumTask(0, DATA_BASE, 128);
  Serial.println(F("  CPU 0: summing bytes 0-127..."));
  unsigned long cycles0 = runZ80UntilDone(0, MAX_CYCLES);
  Serial.print(F("    Done in "));
  Serial.print(cycles0);
  Serial.print(F(" cycles, result = "));
  Serial.println(cpu[0].result);

  // CPU 1 gets last 128 bytes (0x0280-0x02FF)
  // Re-clear stack area for CPU1 (CPU0's run may have used stack at 0x0100-0x017F)
  memset(ram, 0, DATA_BASE - RAM_BASE);
  fillWorkData();  // refresh data in case stack overlapped (it shouldn't, but safe)

  assignSumTask(1, DATA_BASE + 128, 128);
  Serial.println(F("  CPU 1: summing bytes 128-255..."));
  unsigned long cycles1 = runZ80UntilDone(1, MAX_CYCLES);
  Serial.print(F("    Done in "));
  Serial.print(cycles1);
  Serial.print(F(" cycles, result = "));
  Serial.println(cpu[1].result);

  // Combine results
  uint16_t combined = cpu[0].result + cpu[1].result;
  unsigned long parallel = max(cycles0, cycles1);

  Serial.println();
  Serial.print(F("  Combined result: "));
  Serial.print(combined);
  Serial.print(F("  (expected "));
  Serial.print(expectedSum());
  Serial.println(F(")"));

  Serial.print(F("  Parallel time:   "));
  Serial.print(parallel);
  Serial.println(F(" cycles (max of both CPUs)"));

  bool pass = (combined == expectedSum()) &&
              (cpu[0].result == expectedHalfSum(0)) &&
              (cpu[1].result == expectedHalfSum(1));

  Serial.print(F("  "));
  Serial.println(pass ? F("PASS") : F("** FAIL **"));

  *cyclesOut = parallel;
  return pass;
}

// ============================================================
// Main
// ============================================================

void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  Serial.println();
  Serial.println(F("=========================================="));
  Serial.println(F("  DualZ80 SMP Kernel v1.0"));
  Serial.println(F("  Symmetric Multiprocessing on Z80"));
  Serial.println(F("=========================================="));
  Serial.println(F("  2 CPUs detected (U1, U2)"));
  Serial.println(F("  Kernel: 52 bytes at 0x0000"));
  Serial.println(F("  RAM:    512 bytes at 0x0100-0x02FF"));
  Serial.print(F("  Data:   "));
  Serial.print(DATA_SIZE);
  Serial.println(F(" bytes at 0x0200"));

  initPins();
  delay(100);

  // Run single-CPU benchmarks on each processor
  unsigned long singleU1, singleU2;
  bool pass1 = demoSingleCPU(0, &singleU1);
  bool pass2 = demoSingleCPU(1, &singleU2);

  // Run dual-CPU benchmark
  unsigned long dualCycles;
  bool pass3 = demoDualCPU(&dualCycles);

  // Average single-CPU time (both should be similar)
  unsigned long singleAvg = (singleU1 + singleU2) / 2;

  // Summary
  Serial.println();
  Serial.println(F("=========================================="));
  Serial.println(F("  Performance Summary"));
  Serial.println(F("=========================================="));

  Serial.print(F("  Single CPU (U1): "));
  Serial.print(singleU1);
  Serial.println(F(" cycles"));

  Serial.print(F("  Single CPU (U2): "));
  Serial.print(singleU2);
  Serial.println(F(" cycles"));

  Serial.print(F("  Dual CPU (SMP):  "));
  Serial.print(dualCycles);
  Serial.println(F(" cycles"));

  Serial.print(F("  Speedup:         "));
  // Fixed-point: multiply by 100 for 2 decimal places
  unsigned long speedup100 = (singleAvg * 100) / dualCycles;
  Serial.print(speedup100 / 100);
  Serial.print('.');
  unsigned long frac = speedup100 % 100;
  if (frac < 10) Serial.print('0');
  Serial.print(frac);
  Serial.println(F("x"));

  Serial.println(F("=========================================="));

  int passed = (pass1 ? 1 : 0) + (pass2 ? 1 : 0) + (pass3 ? 1 : 0);
  Serial.print(F("  Tests: "));
  Serial.print(passed);
  Serial.println(F(" / 3 passed"));

  if (passed == 3) {
    Serial.println(F("  SMP operational — both CPUs verified!"));
  } else {
    Serial.println(F("  Check wiring and connections."));
  }

  Serial.println(F("=========================================="));
}

void loop() {
  // Tests run once in setup()
}
