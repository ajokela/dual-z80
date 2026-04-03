/*
 * Dual Z80 RetroShield Test Sketch
 *
 * Tests both Z80 processors on the Dual Z80 RetroShield board.
 * The Arduino Mega emulates shared RAM and serves as the memory
 * subsystem for both processors. There is no external RAM — the
 * Arduino responds to Z80 bus cycles in real time.
 *
 * Wiring: J2 header to Arduino Mega free pins (D0-D21):
 *   J2-1  +5V     -> +5V
 *   J2-2  GND     -> GND
 *   J2-3  CLK_2   -> D9
 *   J2-4  RESET_2 -> D4
 *   J2-5  INT_2   -> D5
 *   J2-6  NMI_2   -> D6
 *   J2-7  MREQ_2  -> D7
 *   J2-8  IORQ_2  -> D8
 *   J2-9  RD_2    -> D10
 *   J2-10 WR_2    -> D11
 *   J2-11 BUSRQ_2 -> D12
 *   J2-12 BUSAK_2 -> D13
 *
 * Bus Architecture:
 *   Address bus A0-A15 : PORTA (D22-D29) + PORTC (D30-D37) — shared
 *   Data bus D0-D7     : PORTL (D42-D49) — shared
 *   U1 control signals : on RetroShield J1 header pins
 *   U2 control signals : on J2 header (wired to D4-D13)
 *
 * Tests:
 *   1. U1 Solo  — U1 writes 0xDE to address 0x0080
 *   2. U2 Solo  — U2 writes 0xAD to address 0x0081
 *   3. Persist  — both signatures remain in shared RAM
 *   4. Relay    — U1 writes a value, U2 reads and transforms it
 */

// ============================================================
// U1 Control Pins (RetroShield J1)
// ============================================================
#define U1_CLK    52  // PB1, through R1 to U1 pin 6
#define U1_RESET  38  // PD7, U1 pin 26
#define U1_MREQ   41  // PG0, U1 pin 19
#define U1_IORQ   39  // PG2, U1 pin 20
#define U1_RD     53  // PB0, U1 pin 21
#define U1_WR     40  // PG1, U1 pin 22
#define U1_INT    50  // PB3, U1 pin 16
#define U1_NMI    51  // PB2, U1 pin 17

// ============================================================
// U2 Control Pins (J2 header, jumper-wired)
// ============================================================
#define U2_CLK     9  // Through R2 to U2 pin 6
#define U2_RESET   4  // U2 pin 26
#define U2_INT     5  // U2 pin 16
#define U2_NMI     6  // U2 pin 17
#define U2_MREQ    7  // U2 pin 19
#define U2_IORQ    8  // U2 pin 20
#define U2_RD     10  // U2 pin 21
#define U2_WR     11  // U2 pin 22
#define U2_BUSRQ  12  // U2 pin 25
#define U2_BUSAK  13  // U2 pin 23

// ============================================================
// Emulated RAM (shared between both Z80s)
// ============================================================
#define RAM_SIZE 256
static byte ram[RAM_SIZE];

// ============================================================
// Low-Level Bus Functions
// ============================================================

// Address bus: PORTA = A0-A7, PORTC = A8-A15
// Data bus:    PORTL = D0-D7

static inline uint16_t readAddress() {
  return (uint16_t)PINA | ((uint16_t)PINC << 8);
}

static inline uint8_t readDataBus() {
  return PINL;
}

static inline void driveData(uint8_t val) {
  DDRL  = 0xFF;   // data bus -> output
  PORTL = val;
}

static inline void releaseDataBus() {
  DDRL  = 0x00;   // data bus -> input (tri-state)
  PORTL = 0x00;   // no pull-ups
}

// ============================================================
// Z80 Execution Engine
// ============================================================

// One clock cycle: toggle CLK, handle memory if MREQ active.
// mreqPin/rdPin/wrPin select which Z80's control lines to watch.
static void clockCycle(uint8_t clkPin,
                       uint8_t mreqPin, uint8_t rdPin, uint8_t wrPin)
{
  // CLK rising edge — Z80 puts address & control on bus
  digitalWrite(clkPin, HIGH);
  delayMicroseconds(2);

  // Respond to bus requests
  if (digitalRead(mreqPin) == LOW) {
    uint16_t addr = readAddress();
    if (addr < RAM_SIZE) {
      if (digitalRead(rdPin) == LOW) {
        // Z80 reads memory — Arduino drives data bus
        driveData(ram[addr]);
      } else if (digitalRead(wrPin) == LOW) {
        // Z80 writes memory — Arduino captures data bus
        releaseDataBus();
        delayMicroseconds(1);
        ram[addr] = readDataBus();
      }
    }
  }

  delayMicroseconds(2);

  // CLK falling edge
  digitalWrite(clkPin, LOW);
  releaseDataBus();
  delayMicroseconds(2);
}

// Run one Z80 for `cycles` clock ticks.
// The OTHER Z80 is held in reset so it doesn't drive the shared bus.
static void runZ80(uint8_t cpu, int cycles) {
  uint8_t clkPin, resetPin, mreqPin, rdPin, wrPin;
  uint8_t otherReset;

  if (cpu == 1) {
    clkPin   = U1_CLK;   resetPin = U1_RESET;
    mreqPin  = U1_MREQ;  rdPin    = U1_RD;  wrPin = U1_WR;
    otherReset = U2_RESET;
  } else {
    clkPin   = U2_CLK;   resetPin = U2_RESET;
    mreqPin  = U2_MREQ;  rdPin    = U2_RD;  wrPin = U2_WR;
    otherReset = U1_RESET;
  }

  // Keep the other Z80 in reset (bus tri-stated)
  digitalWrite(otherReset, LOW);

  // Address bus -> input (Z80 will drive it)
  DDRA = 0x00;  PORTA = 0x00;
  DDRC = 0x00;  PORTC = 0x00;
  releaseDataBus();

  // Control lines -> input (Z80 drives MREQ/RD/WR)
  pinMode(mreqPin, INPUT_PULLUP);
  pinMode(rdPin,   INPUT_PULLUP);
  pinMode(wrPin,   INPUT_PULLUP);

  // Release Z80 from reset (needs >=3 clocks while RESET is low first)
  digitalWrite(resetPin, LOW);
  for (int i = 0; i < 6; i++) {
    digitalWrite(clkPin, HIGH);
    delayMicroseconds(2);
    digitalWrite(clkPin, LOW);
    delayMicroseconds(2);
  }
  digitalWrite(resetPin, HIGH);
  delayMicroseconds(5);

  // Execute
  for (int i = 0; i < cycles; i++) {
    clockCycle(clkPin, mreqPin, rdPin, wrPin);
  }

  // Put Z80 back in reset
  digitalWrite(resetPin, LOW);
  delayMicroseconds(5);
}

// ============================================================
// Initialization
// ============================================================

static void initPins() {
  // U1 control
  pinMode(U1_CLK,   OUTPUT); digitalWrite(U1_CLK,   LOW);
  pinMode(U1_RESET, OUTPUT); digitalWrite(U1_RESET, LOW);
  pinMode(U1_INT,   OUTPUT); digitalWrite(U1_INT,   HIGH);  // inactive
  pinMode(U1_NMI,   OUTPUT); digitalWrite(U1_NMI,   HIGH);  // inactive
  pinMode(U1_MREQ,  INPUT_PULLUP);
  pinMode(U1_IORQ,  INPUT_PULLUP);
  pinMode(U1_RD,    INPUT_PULLUP);
  pinMode(U1_WR,    INPUT_PULLUP);

  // U2 control
  pinMode(U2_CLK,   OUTPUT); digitalWrite(U2_CLK,   LOW);
  pinMode(U2_RESET, OUTPUT); digitalWrite(U2_RESET, LOW);
  pinMode(U2_INT,   OUTPUT); digitalWrite(U2_INT,   HIGH);  // inactive
  pinMode(U2_NMI,   OUTPUT); digitalWrite(U2_NMI,   HIGH);  // inactive
  pinMode(U2_BUSRQ, OUTPUT); digitalWrite(U2_BUSRQ, HIGH);  // inactive
  pinMode(U2_MREQ,  INPUT_PULLUP);
  pinMode(U2_IORQ,  INPUT_PULLUP);
  pinMode(U2_RD,    INPUT_PULLUP);
  pinMode(U2_WR,    INPUT_PULLUP);
  pinMode(U2_BUSAK, INPUT_PULLUP);

  // Bus idle
  DDRA = 0x00;  PORTA = 0x00;
  DDRC = 0x00;  PORTC = 0x00;
  releaseDataBus();
}

static void clearRAM() {
  memset(ram, 0x00, RAM_SIZE);
}

// ============================================================
// Test Helpers
// ============================================================

static void loadProgram(const uint8_t *prog, uint8_t len, uint16_t base) {
  for (uint8_t i = 0; i < len && (base + i) < RAM_SIZE; i++) {
    ram[base + i] = prog[i];
  }
}

static void printHex(uint8_t val) {
  if (val < 0x10) Serial.print('0');
  Serial.print(val, HEX);
}

static void printResult(const char *name, bool pass) {
  Serial.print("  ");
  Serial.print(name);
  Serial.print(": ");
  Serial.println(pass ? "PASS" : "** FAIL **");
}

static void dumpRAM(uint16_t start, uint16_t len) {
  for (uint16_t i = start; i < start + len && i < RAM_SIZE; i++) {
    Serial.print("  [0x");
    if (i < 0x10) Serial.print('0');
    Serial.print(i, HEX);
    Serial.print("] = 0x");
    printHex(ram[i]);
    Serial.println();
  }
}

// ============================================================
// Test Programs (Z80 machine code)
// ============================================================

// Program 1: LD A,0xDE ; LD (0x0080),A ; HALT
//   Writes 0xDE to address 0x0080, then halts.
static const uint8_t prog_write_DE[] = {
  0x3E, 0xDE,             // LD A, 0xDE
  0x32, 0x80, 0x00,       // LD (0x0080), A
  0x76                    // HALT
};

// Program 2: LD A,0xAD ; LD (0x0081),A ; HALT
//   Writes 0xAD to address 0x0081, then halts.
static const uint8_t prog_write_AD[] = {
  0x3E, 0xAD,             // LD A, 0xAD
  0x32, 0x81, 0x00,       // LD (0x0081), A
  0x76                    // HALT
};

// Program 3: LD A,(0x0080) ; INC A ; LD (0x0082),A ; HALT
//   Reads from 0x0080, increments, writes to 0x0082, then halts.
static const uint8_t prog_relay[] = {
  0x3A, 0x80, 0x00,       // LD A, (0x0080)
  0x3C,                   // INC A
  0x32, 0x82, 0x00,       // LD (0x0082), A
  0x76                    // HALT
};

// Program 4: Counter — increment (0x0090) ten times, then halt
//   LD B,10 ; loop: LD A,(0x0090) ; INC A ; LD (0x0090),A ; DJNZ loop ; HALT
static const uint8_t prog_counter[] = {
  0x06, 0x0A,             // LD B, 10
  // loop (offset 2):
  0x3A, 0x90, 0x00,       // LD A, (0x0090)
  0x3C,                   // INC A
  0x32, 0x90, 0x00,       // LD (0x0090), A
  0x10, 0xF7,             // DJNZ loop (-9 = back to offset 2)
  0x76                    // HALT
};

// ============================================================
// Tests
// ============================================================

// Enough cycles for any of our short programs to finish.
// An instruction fetch is 4 T-states, memory access 3 T-states.
// Worst case: ~12 instructions × ~20 T-states each = ~240.
// 500 gives comfortable margin.
#define RUN_CYCLES 500

static bool test1_u1_solo() {
  Serial.println("\n--- Test 1: U1 Solo ---");
  Serial.println("  Loading: LD A,0xDE ; LD (0x0080),A ; HALT");

  clearRAM();
  loadProgram(prog_write_DE, sizeof(prog_write_DE), 0x0000);

  Serial.println("  Running U1 for 500 cycles...");
  runZ80(1, RUN_CYCLES);

  Serial.print("  RAM[0x0080] = 0x"); printHex(ram[0x80]); Serial.println();
  bool pass = (ram[0x80] == 0xDE);
  printResult("U1 wrote 0xDE to 0x0080", pass);
  return pass;
}

static bool test2_u2_solo() {
  Serial.println("\n--- Test 2: U2 Solo ---");
  Serial.println("  Loading: LD A,0xAD ; LD (0x0081),A ; HALT");

  clearRAM();
  loadProgram(prog_write_AD, sizeof(prog_write_AD), 0x0000);

  Serial.println("  Running U2 for 500 cycles...");
  runZ80(2, RUN_CYCLES);

  Serial.print("  RAM[0x0081] = 0x"); printHex(ram[0x81]); Serial.println();
  bool pass = (ram[0x81] == 0xAD);
  printResult("U2 wrote 0xAD to 0x0081", pass);
  return pass;
}

static bool test3_persistence() {
  Serial.println("\n--- Test 3: Shared RAM Persistence ---");
  Serial.println("  U1 writes 0xDE to 0x0080, then U2 writes 0xAD to 0x0081.");
  Serial.println("  Verify both values persist in shared RAM.");

  clearRAM();

  // Phase 1: U1 writes
  loadProgram(prog_write_DE, sizeof(prog_write_DE), 0x0000);
  runZ80(1, RUN_CYCLES);
  Serial.print("  After U1: RAM[0x0080]=0x"); printHex(ram[0x80]); Serial.println();

  // Phase 2: load new program at 0x0000, run U2
  // (U1's write to 0x0080 is in ram[] and must survive the program reload
  //  because the new program only occupies 0x0000-0x0005)
  loadProgram(prog_write_AD, sizeof(prog_write_AD), 0x0000);
  runZ80(2, RUN_CYCLES);
  Serial.print("  After U2: RAM[0x0080]=0x"); printHex(ram[0x80]);
  Serial.print("  RAM[0x0081]=0x"); printHex(ram[0x81]); Serial.println();

  bool pass = (ram[0x80] == 0xDE) && (ram[0x81] == 0xAD);
  printResult("Both signatures present", pass);
  return pass;
}

static bool test4_relay() {
  Serial.println("\n--- Test 4: Relay Between Processors ---");
  Serial.println("  U1 reads 0x0080, increments, writes to 0x0082.");
  Serial.println("  Then U2 does the same, producing a second increment.");

  clearRAM();
  ram[0x80] = 0x42;  // Seed value

  // Phase 1: U1 runs relay program
  loadProgram(prog_relay, sizeof(prog_relay), 0x0000);
  Serial.print("  Seed: RAM[0x0080]=0x"); printHex(ram[0x80]); Serial.println();

  runZ80(1, RUN_CYCLES);
  Serial.print("  After U1: RAM[0x0082]=0x"); printHex(ram[0x82]); Serial.println();
  bool pass1 = (ram[0x82] == 0x43);  // 0x42 + 1

  // Phase 2: copy U1's output as new input, run U2
  ram[0x80] = ram[0x82];  // feed U1's result back as input
  loadProgram(prog_relay, sizeof(prog_relay), 0x0000);

  runZ80(2, RUN_CYCLES);
  Serial.print("  After U2: RAM[0x0082]=0x"); printHex(ram[0x82]); Serial.println();
  bool pass2 = (ram[0x82] == 0x44);  // 0x43 + 1

  bool pass = pass1 && pass2;
  printResult("U1 produced 0x43, U2 produced 0x44", pass);
  return pass;
}

static bool test5_counter() {
  Serial.println("\n--- Test 5: Loop Counter ---");
  Serial.println("  Each Z80 increments RAM[0x0090] ten times via DJNZ loop.");

  clearRAM();
  loadProgram(prog_counter, sizeof(prog_counter), 0x0000);

  runZ80(1, RUN_CYCLES);
  Serial.print("  After U1: RAM[0x0090]=0x"); printHex(ram[0x90]); Serial.println();
  bool pass1 = (ram[0x90] == 10);

  // Reset counter, run U2
  ram[0x90] = 0;
  loadProgram(prog_counter, sizeof(prog_counter), 0x0000);
  runZ80(2, RUN_CYCLES);
  Serial.print("  After U2: RAM[0x0090]=0x"); printHex(ram[0x90]); Serial.println();
  bool pass2 = (ram[0x90] == 10);

  bool pass = pass1 && pass2;
  printResult("Both Z80s counted to 10", pass);
  return pass;
}

// ============================================================
// Main
// ============================================================

void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  Serial.println("==========================================");
  Serial.println("  Dual Z80 RetroShield — Hardware Test");
  Serial.println("==========================================");

  initPins();
  delay(100);

  int passed = 0;
  int total  = 5;

  if (test1_u1_solo())    passed++;
  if (test2_u2_solo())    passed++;
  if (test3_persistence()) passed++;
  if (test4_relay())       passed++;
  if (test5_counter())     passed++;

  Serial.println("\n==========================================");
  Serial.print("  Results: ");
  Serial.print(passed);
  Serial.print(" / ");
  Serial.print(total);
  Serial.println(" tests passed");

  if (passed == total) {
    Serial.println("  Both Z80 processors verified working!");
  } else {
    Serial.println("  Some tests failed — check wiring.");
  }
  Serial.println("==========================================");
}

void loop() {
  // Nothing — tests run once in setup()
}
