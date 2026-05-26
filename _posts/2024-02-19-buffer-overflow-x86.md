---
title: "Buffer Overflow Project on x86"
date: 2024-02-19 18:00:00 -0500
categories: [Binary Exploitation, Reverse Engineering]
tags: [Buffer Overflow, x86, GDB, Radare2, Ghidra, NASM, Fuzzing, Python, Assembly, Project]
description: Working notes on x86 internals leading into buffer overflow exploitation, file and checksec triage, radare2 and GDB usage, NASM data types, the stack and control flow, Ghidra decompilation, and a Python socket-based fuzzer.
image:
  path: /assets/img/blog/buffer-overflow-x86/image5.png
  alt: "Stack instructions in NASM showing push and pop operations against EBP and ESP."
---

This post collects my working notes on x86 internals and early-stage buffer overflow exploration, file and section triage, radare2 and GDB usage, NASM data types, the stack and control flow, a Ghidra-decompiled function, and a small Python socket fuzzer.

---

## File Triage

```bash
#file reverse
reverse: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked,
for GNU/Linux 2.6.26, BuildID[sha1]=2499fd87be4131907bb5e7f4c66ab2c4f9589969, stripped
```

| Feature                 | Stripped Binary                              | Non-Stripped Binary                                                |
| ----------------------- | -------------------------------------------- | ------------------------------------------------------------------ |
| Debugging Symbols       | Removed during build                         | Retained, includes function names, line numbers, variable names    |
| Size                    | Smaller                                      | Larger                                                             |
| Purpose                 | Production                                   | Development and testing                                            |
| Debugging and Analysis  | Limited                                      | Comprehensive                                                      |
| Performance             | Slightly better                              | Slightly reduced                                                   |

Stripped binaries are harder to reverse-engineer, debug, and exploit because the symbol information is gone. Non-stripped binaries make analysis easier but are also easier for defenders to detect.

```bash
#checksec --file reverse
#ropper --file reverse
```

---

## Radare2

```bash
#r2 reverse
```

| Command       | Usage                       |
| ------------- | --------------------------- |
| `aaa`         | Perform automatic analysis  |
| `pd [arg]`    | Disassemble code            |
| `afl`         | List all functions          |
| `s [address]` | Seek to address             |
| `V`           | Enter visual mode           |
| `w`           | Write changes to file       |
| `q`           | Quit radare2                |
| `?`           | Display help menu           |
| `iz`          | Search for strings          |

After `aaa`, jump to main with `s main`, view the function with `pdf`, switch to graph view with `V`, and pull readable strings with `iz`.

---

## NASM Data Types

![Data type declarations in NASM assembly.](/assets/img/blog/buffer-overflow-x86/image1.png)

Assemble and link a 32-bit ELF:

```bash
#nasm -f elf32 datatypes.nasm -o datatypes.o
#ld -m elf_i386 datatypes.o -o datatypes
#./datatypes
```

`nasm` produces a 32-bit ELF object; `ld` links it into an executable for the 32-bit Intel x86 architecture.

---

## GDB Basics

![GDB session attached to the datatypes binary.](/assets/img/blog/buffer-overflow-x86/image2.png)

Useful commands:

```
#info functions
#disassemble _start
#break _start
#run
```

Breaking at `_start` pauses the program before any startup code runs, useful for examining initial state or stepping through initialization.

![info variables in GDB listing the program's variables.](/assets/img/blog/buffer-overflow-x86/image3.png)

![Examining variable contents with the x command.](/assets/img/blog/buffer-overflow-x86/image4.png)

The `x` command examines memory. Formatting options include `b` (byte), `h` (half-word, 2 bytes), `w` (word, 4 bytes), `g` (giant, 8 bytes), `i` (instruction), `s` (null-terminated string), `c` (character), `u`/`d`/`o`/`x` (unsigned decimal, signed decimal, octal, hex). Options combine, so `x/4xw` displays 4 words in hex.

### Endianness

Little endian stores the least significant byte first; big endian stores the most significant byte first.

```
gdb-peda$ x/3bx &var1
0x804a000: 0x01 0x34 0x12

gdb-peda$ x/4bx &var3
0x804a003: 0x78 0x56 0x34 0x12
```

`0x804a000` is the address; the bytes that follow are the values at offset 0, 1, 2 in hex.

---

## The Stack

The stack is a LIFO data structure with two operations: PUSH (placing the book) and POP (taking the book). `EBP` is the base pointer (base of stack), `ESP` is the stack pointer (top of stack). The stack grows from higher to lower memory addresses, so PUSH decrements the address by 4 and POP increments it by 4.

![NASM stack walkthrough with push and pop instructions against eax, ebx, and var1.](/assets/img/blog/buffer-overflow-x86/image5.png)

Reading the instructions:

1. `mov eax, 2` puts the immediate value 2 into `eax`.
2. `push 0x3` pushes 0x3 onto the stack.
3. `push 0x7` pushes 0x7 onto the stack.
4. `pop eax` pops the top into `eax`, so `eax = 0x7`.
5. `pop ebx` pops the next into `ebx`, so `ebx = 0x3`.
6. `push WORD [var1]` pushes a 2-byte value from `var1`.
7. `pop ebx` pops it into `ebx`.
8. `push DWORD [var1]` pushes a 4-byte value from `var1`.
9. `pop ebx` pops it into `ebx`.
10. `mov eax, 1` and `mov ebx, 0` then `int 0x80` makes the `sys_exit` syscall with a 0 status, terminating the program.

![Register state after executing the stack instructions.](/assets/img/blog/buffer-overflow-x86/image6.png)

---

## Control Flow

Controlling program flow means changing the value of the instruction pointer (`EIP`). `EIP` cannot be changed by a normal `mov`. Only an unconditional jump can change `EIP` directly.

![Control flow instructions in NASM.](/assets/img/blog/buffer-overflow-x86/image7.png)

```
#jmp 0x12345678
```

Instructions between the `jmp` and the target are skipped.

```
#CMP ebx, 20
```

`CMP` subtracts 20 from `ebx` and sets the flags, but does not store the result and does not change `EIP` directly. The conditional jumps then act on those flags:

- `jg` jump if greater
- `jge` jump if greater or equal
- `jl` jump if less
- `jle` jump if less or equal
- `je` / `jz` jump if equal / zero

Example:

```nasm
global _start
section .text
_start:
  mov eax, 30
  mov ebx, 20
  jmp temp
  mov eax, 40
temp:
  mov ecx, 50
  mov edx, 10
```

The `jmp temp` unconditionally jumps to the `temp` label, skipping `mov eax, 40`.

Always check the registers after each instruction.

### Loops

![Loop instructions in NASM.](/assets/img/blog/buffer-overflow-x86/image8.png)

![Loop code listing.](/assets/img/blog/buffer-overflow-x86/image9.png)

---

## When Fuzzing is Required

Fuzzing finds vulnerabilities, including buffer overflows, by feeding invalid, unexpected, or random input to a program.

| Situation                        | Fuzzing Necessary?                                                |
| -------------------------------- | ----------------------------------------------------------------- |
| Complex Input Handling           | Yes, to explore potential vulnerabilities                         |
| Unknown Attack Surface           | Yes, to identify vulnerabilities in various areas                 |
| Continuous Testing               | Yes, to ensure new features don't introduce vulnerabilities       |
| Compliance Requirements          | Yes, to meet security and regulatory standards                    |
| Prior History of Vulnerabilities | Yes, to address past vulnerabilities and prevent recurrence       |
| Simple Input Handling            | No, manual testing or other techniques may suffice                |
| Static Analysis Tools            | No, static analysis may detect vulnerabilities without fuzzing    |
| Well-Established Libraries       | No, built-in protections may mitigate risk                        |
| Limited Resources                | Depends, prioritize other testing if resources are limited        |

---

## Ghidra Decompile

```c
void processEntry entry(undefined8 param_1, undefined8 param_2)
{
  undefined auStack_8 [8];
  FUN_00400900(FUN_0040075b, param_2, &stack0x00000008,
               FUN_00400ff0, FUN_00400fb0, param_1, auStack_8);
  do {
    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}
```

What Ghidra is telling us:

1. An 8-byte stack buffer `auStack_8` is declared.
2. `processEntry` takes `param_1` and `param_2`.
3. It calls `FUN_00400900` with a callback (`FUN_0040075b`), the original parameters, a pointer to the stack buffer, two other function references, and the buffer itself.
4. It then enters an infinite loop that does nothing.

The vulnerability would likely sit inside `FUN_00400900` if it copies input into `auStack_8` without bounds checking. The infinite loop makes debugging easier because the program does not exit. Next step is to analyze `FUN_00400900` and trace what happens to `auStack_8`.

![Ghidra view of the entry function.](/assets/img/blog/buffer-overflow-x86/image10.png)

---

## Artifacts in radare2

```
#aaaaaa
#afl
#iz
```

`afl` shows two readable functions, `entry` and `main`. `iz` lists strings, including:

```
0   0x00083870 0x00483870 98 99 .rodata ascii
    Welcome to rot13 as a Service!\nYour one stop shop for the best encryption the world has to offer.\n

159 0x000873d4 0x004873d4 24 25 .rodata ascii
    buffer overflow detected
```

```
#ie     (entry points)
#iM     (main address)
```

---

## Fuzzing in Python

![Fuzzing overview diagram.](/assets/img/blog/buffer-overflow-x86/image11.png)

The plan: connect to the application over a socket, send random or oversized data, watch the application's behavior in a debugger. A debugger lets you see the application's data and memory state when the input is too small or fast to observe otherwise.

![Initial Python connection sending HELP to the application.](/assets/img/blog/buffer-overflow-x86/image12.png)

![Banner and response printed from the Python script.](/assets/img/blog/buffer-overflow-x86/image13.png)

### Connection through a socket

![Binary loaded in immunity debugger ready to receive payloads.](/assets/img/blog/buffer-overflow-x86/image14.png)

```python
import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('192.168.147.138', 1337))
banner = s.recv(2048).decode()
print(banner)

msg = 'HELP'
s.send(msg.encode())

banner = s.recv(2048).decode()
print(banner)
s.close()
```

`socket.AF_INET` selects IPv4; `SOCK_STREAM` selects a TCP byte stream. `s.recv(2048)` reads up to 2048 bytes, then we send `HELP`, read the response, and close.

In Python 3 you can only send bytes, not strings, so payloads are encoded with `'raw_unicode_escape'` to keep the bytes intact.

### Iterating the payload

![Payload sent across the socket and observed in the debugger.](/assets/img/blog/buffer-overflow-x86/image15.png)

Send 50 `A`s first, then increase by 100 each iteration until the application crashes:

```python
#Ip: 192.168.147.138
#port: 1337
import socket
import time

count = 50

while True:
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('192.168.147.138', 1337))
    banner = s.recv(2048).decode()
    junk = 'A' * count
    payload = junk
    payload = payload.encode('raw_unicode_escape')
    s.send(payload)
    count += 100
    print("payload sent with {} bytes".format(count))
  except:
    print("application crashed at {} bytes".format(count))
    break

s.close()
```

When the connection breaks, the script prints the byte count that crashed the application, which is the starting point for figuring out where the overflow lands.

Breakpoints can also be set in the debugger with `RC > breakpoint > toggle`. Other fuzzers worth knowing: SULLEY and Boofuzz in Python, SPIKE in C, and Immunity Debugger for live analysis.
