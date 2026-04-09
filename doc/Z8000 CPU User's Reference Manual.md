# Z8000 CPU User's Reference Manual
**Zilog**
**Prentice-Hall, Inc., Englewood Cliffs, New Jersey 07632**

---

## Library of Congress Cataloging in Publication Data
**Main entry under title:**
Z8000 CPU user's reference manual.
1. Zilog Model Z8000 (Computer) 
I. Zilog, Inc.
II. Title: Z8000 C.P.U. user's reference manual.
QA76.8.Z55Z15 001.64's 81-21043
ISBN 0-13-983908-9 
AACR2
ISBN 0-13-983890-2 (pbk.)

Editorial/production supervision by Lori Opre
Manufacturing buyer: Gordon Osbourne

© 1982, 1981, and 1980 by Zilog, Inc.
All rights reserved.

---
# Chapter 1
# Z8000 Processor Overview

## 1.1 Introduction
This chapter provides a summary description of the advanced architecture of the Z8000 Microprocessor, with special attention given to those architectural features that set the Z8000 CPU apart from its predecessors. A complete overview of the architecture is provided in Chapter 2, with detailed descriptions of the various aspects of the processor provided in succeeding chapters.

## 1.2 General Organization
Zilog's Z8000 microprocessor has been designed to accommodate a wide range of applications, from the relatively simple to the large and complex. The Z8000 CPU is offered in three versions: the Z8001, 2, and 3. The Z8003 is discussed in the Z8003 CPU User's Manual. Each CPU comes with an entire family of support components: a memory management unit, a DMA controller, serial and parallel I/O controllers, and extended processing units—all compatible with Zilog's Z-Bus. Together with other Z8000 Family components, the advanced CPU architecture provides in an LSI microprocessor design the flexibility and sophisticated features usually associated with mini- or mainframe computers.

The major architectural features of the Z8000 CPU that enhance throughput and processing power are a general purpose register file, system and normal modes of operation, multiple addressing spaces, a powerful instruction set, numerous addressing modes, multiple stacks, sophisticated interrupt structure, a rich set of data types, separate I/O address spaces and, for the Z8001, a large address space and segmented memory addressing. Each of these benefits that result from these features are code density, compiler efficiency and support for typical operating system operations, and complex data structures. These topics are treated in Section 1.3.

The CPU has been designed so that a powerful memory management system can be used to improve the utilization of the main memory and provide protection capabilities for the system. This is discussed in Section 1.3.12. Although memory management is an optional capability—the Z8000 CPU is an extremely sophisticated processor without memory management—the CPU has explicit features to facilitate integrating an external memory management device into a Z8000 system configuration.

Finally, care has been taken to provide a very general mechanism for extending the basic instruction set through the use of external devices (called Extended Processing Units—EPUs). In general, an EPU is dedicated to performing complex and time-consuming tasks so as to unburden the CPU. Typical tasks for specialized EPUs include floating-point arithmetic, data base search and maintenance operations, network interfaces, and many others.

## 1.3 Architectural Features

### 1.3.1 General-Purpose Register File
The heart of the Z8000 CPU architecture is a file of sixteen 16-bit general-purpose registers. These general-purpose registers give the Z8000 its power and flexibility and add to its regular instruction structure.

General-purpose registers can be used as accumulators, memory pointers or index registers. Their major advantage is that the particular use to which they are put can vary during the course of a program as the needs of the program change. Thus, the general-purpose register file avoids the critical bottlenecks of an implied or dedicated register architecture, which must save and restore the contents of dedicated registers when more registers of a particular type are needed than are supplied by the processor.

The Z8000 CPU register file can be addressed in several ways: as 16 byte registers (occupying one half of the file) or as 16 word registers or, by using the register pairing mechanism, as eight long-word (32-bit) registers or as four quadruple-word (64-bit) registers. Because of this register flexibility, it is not necessary (for example) for a Z8000 user to dedicate a 32-bit register to hold a byte of data. Registers can be used efficiently in the Z8000.

### 1.3.2 Instruction Set
A powerful instruction set is one of the distinguishing characteristics of the Z8000. The instruction set is one measure of the flexibility and versatility of a computer. Having a given operation implemented in hardware saves memory and improves speed. In addition, completeness of the operations available on a particular data type is frequently more important than additional, esoteric instructions, which are unlikely to affect performance significantly. The Z8000 CPU provides a full complement of arithmetic, logical, branch, I/O, shift, rotate, and string instructions. In addition, special instructions have been included to facilitate multiprocessing, multiple processor configurations, and typical high level language and operating system functions. The general philosophy of the instruction set is two-operand register-memory operations, which include as a special subset register-register operations. However, to improve code density, a few memory-memory operations are used for string manipulation. The two-address format reflects the most frequently occurring operations (such as A <- A + B). Also, having one of the operands in a rapidly accessible general-purpose register facilitates the use of intermediate results generated during a calculation.

The majority of operations deal with byte, word, or long-word operands, thereby providing a high degree of regularity. Also included in the instruction set are compact, one-word instructions for the most frequently used operations, such as branching short distances in a program.

The instruction set contains some notable additions to the standard repertoire of earlier microprocessors. The Load and Exchange group of instructions has been expanded to support operating system functions and conversion of existing microprocessor programs. The usual arithmetic instructions can now deal with higher-precision operands, while hardware multiply and divide instructions have also been added. The Bit Manipulation instructions can use calculated values to specify the bit position within a byte or word as well as to specify the position statically in the instruction. The Rotate and Shift instructions are considerably more flexible than those in previous microprocessors. The String instructions are useful in translating between different character codes. Multiple-processor configurations are supported by special instructions.

### 1.3.3 Data Types
Many data types are supported by the Z8000 architecture. A data type is supported when it has a hardware representation and instructions which directly apply to it. New data types can always be simulated in terms of basic data types, but hardware support provides faster and more convenient operations. The basic data type is the byte, which is also the basic addressable element. The architecture also supports the following data types: words (16 bits), long words (32 bits), byte strings, and word strings. In addition, bits are fully supported and addressed by number within a byte or word. BCD digits are supported and represented as two 4-bit digits in a byte. Arrays are supported by the Indexed addressing mode (see 1.3.4 and Chapter 5). Stacks are supported by the instruction set and by an external device (the Memory Management Unit, MMU) available with the Z8001.

### 1.3.4 Addressing Modes
The addressing mode, which is the way an operand is specified in an instruction, determines how an address is generated. The Z8000 CPU offers eight addressing modes. Together with the large number of instructions and data types, they improve the processing power of the CPU. The addressing modes are Register, Immediate, Indirect Register, Direct Address, Index, Relative Address, Base Address, and Base Index. Several other addressing modes are implied by specific instructions, including autoincrement. The first five modes listed above are basic addressing modes that are used most frequently and apply to most instructions having more than one addressing mode. (In the Z8002, Base Address and Index modes are identical, and in the Z8001, Base Addressing capabilities can be simulated with all instructions, using Based Addressing or the Memory Management Unit and the Direct or Indexed Addressing mode.)

### 1.3.5 Multiple Memory Address Spaces
The Z8000 CPU facilitates the use of multiple address spaces. When the Z8000 CPU generates an address, it also outputs signals indicating the particular internal activity which led to the memory request: instruction fetch, operand reference, or stack reference. This information can be used in two ways: to increase the memory space available to the processor (for example, by putting programs in one space and data in another); or to protect portions of the memory and allow only certain types of accesses (for example, by allowing only instruction fetches from an area designated to contain proprietary software). The Memory Management Unit (MMU) has been designed to provide precisely these kinds of protection features by using the CPU-generated status information.

### 1.3.6 System/Normal Mode of Operation
The Z8000 CPU can run in either system mode or normal mode. In system mode, all of the instructions can be executed and all of the CPU registers can be accessed. This mode is intended for use by programs performing operating system functions. In normal mode, some instructions may not be executed (e.g., I/O instructions), and some CPU registers are not accessible (e.g., the control registers of the CPU). This dichotomy allows for the separation of operating system functions from application program functions. In this way, the operating system can be protected from possible mistakes made by the user. Programs are normally written to run in one of the two modes; a System Call instruction is used to switch from normal to system mode. This protection can be even further improved by using the multiple address spaces to separate system mode and normal mode. This makes it possible for the system software to run in its own independent address space, which could be made inaccessible to any program running in normal mode. In this way, the system could be protected from all programs run in normal mode. Typically, the system designer writes the operating system to run in system mode and the individual users write their programs to run in normal mode.

To further support the system/normal mode dichotomy, there are two copies of the stack pointer—one for a system mode stack and another for a normal mode stack. These two stacks facilitate the task switching involved when interrupts or traps occur. To insure that the normal stack is free of system information, the information saved on the occurrence of interrupts or traps is always pushed on to the system stack before the new program status is loaded.

### 1.3.7 Separate I/O Address Spaces
The Z8000 Architecture distinguishes between memory and I/O spaces and thus requires specific I/O instructions. This architectural separation allows better protection and has more potential for extension. The use of separate I/O spaces also conserves the limited Z8002 data memory space. There are in fact two separate I/O address spaces: Standard I/O and Special I/O. The main advantage of these two spaces is to provide for two types of peripheral support chips—Standard I/O peripherals and Special I/O peripherals—devices such as the Z8010 Memory Management Unit that do not respond to Standard I/O commands. A second advantage of these two spaces is that they allow 8-bit peripherals to attach to the low-order eight bits (Standard I/O) or to the high-order eight bits (Special I/O) of the processor Address/Data bus.

The increased speed requirements of future microprocessors are likely to be achieved by tailoring memory and I/O references to their respective specific needs. The Z8000 separate memory and I/O spaces allow for this.

### 1.3.8 Interrupt Structure
The Z8000 interrupt structure has been designed to satisfy two different types of requirements. The first is the need for a fast response to an interrupt, which is often found in real-time applications. The second is the need to efficiently handle many different interrupt sources.

The Z8000 has implemented a priority system for handling interrupts. Vectored interrupts have higher priority than non-vectored interrupts. This priority scheme allows the efficient control of many peripheral devices in a Z8000 system.

An interrupt causes information relating to the currently executing program (program status) to be saved on a special system stack with a code describing the reason for the switch. This allows recursive task switches to occur while leaving the normal stack undisturbed by system information. The program state to handle the interrupt (new program status) is loaded from a special area in memory, the program status area, designated by a pointer resident in the CPU.

The use of the stack and of a pointer to the program status area is a specific choice made to allow architectural compatibility if new interrupts or traps are added to the architecture.

### 1.3.9 Multi-Processing
The increase in microprocessor computing power that the Z8000 represents makes simple the design of distributed processing systems having many low-cost microprocessors running dedicated processes.

The Z8000 provides some basic mechanisms that allow the sharing of address spaces among different microprocessors. Large segmented address spaces and the support for external memory management make this possible. Also, a resource request bus is provided which, in conjunction with software, provides the exclusive use of shared critical resources. These mechanisms, and new peripherals such as the Z-FIO, have been designed to allow easy asynchronous communication between different CPUs.

### 1.3.10 Large Address Space for the Z8001
For many applications, a basic address space of 64K bytes is insufficient. A large address space increases the range of applications of a system by permitting large, complex programs and data sets to reside in memory rather than be partitioned and swapped into a small memory as needed. A large address space greatly simplifies program and data management. In addition, large address spaces and memories reduce the need for minimizing program size and permit the use of higher level languages. The segmented version of the Z8000 generates 23-bit addresses, for a basic address space of 8 megabytes (8M or 8,388,608 bytes).

### 1.3.11 Segmented Addressing of the Z8001
The segmented version of the Z8000 CPU divides its 23-bit addresses into a 7-bit segment number and a 16-bit segment offset. The segment number serves as a logical name of a segment; it is not altered by the effective address calculation (by indexing, for example). This corresponds to the way memory is typically used by a program—one portion of the memory is set aside to hold instructions, another for data. In a segmented address space, the instructions could reside in one segment (or several different modules in different segments), and each data set could reside in a separate segment. One advantage of segmentation is that it speeds up address calculation and relocation. Thus, segmentation allows the use of slower memories than linear addressing schemes allow. In addition, segments provide a convenient way of partitioning memory so that each partition is given particular access attributes (for example, read-only). The Z8000 approach to segmentation (simultaneous access to a large number of segments) is necessary if all the advantages of segmentation are to be realized. A system capable of directly accessing only, say, four segments would lack the needed flexibility and would be constrained by address space limitations.

### 1.3.12 Memory Management
Memory management consists primarily of dynamic relocation, protection, and sharing of memory. It offers the following advantages: providing a logical structure to the memory space that is independent of the actual physical location of data, protecting the user from inadvertent mistakes, preventing unauthorized access to memory resources or data, and protecting the operating system from disruption by the users.

The addresses manipulated by the programmer, used by instructions, and output by the segmented Z8000 CPU are called logical addresses. The external memory management system takes the logical addresses and transforms them into physical addresses required for accessing the memory. This address transformation process is called relocation, which makes user software independent of the physical memory. Thus, the user is freed from specifying where information is actually located in the physical memory.

The segmented Z8000 CPU supports memory management both with segmented addressing and with program-status information. A segmented addressing space allows individual segments to be treated differently.

Program status information generated by the CPU permits an external memory management device to monitor the intended use of each memory access. Thus, illegal types of access can be suppressed and memory segments protected from unintended or unwanted modes of use. For example, system tables could be protected from direct user access. This added protection capability becomes more important as microprocessors are applied to large, complex tasks.

## 1.4 Benefits of the Architecture
The features of the Z8000 Architecture combine to provide several significant benefits: improvements in code density, compiler efficiency, operating system support, and support for high level data structures.

### 1.4.1 Code Density
Code density affects both processor speed and memory utilization. Code compaction saves memory space—an especially important factor in smaller systems—and improves processor speed by reducing the number of instruction words that must be fetched and decoded. The Z8000 offers several advantages with respect to code density. The most frequently used instructions are encoded in single-word formats. Fewer instructions are needed to accomplish a given task and a consistent and regular architecture further reduces the number of instructions required.

Code density is achieved in part by the use of special "short" formats for certain instructions which are shown by statistical analysis to be most frequently used. A "short offset" mechanism has also been provided to allow a 2-word segmented address to be reduced to a single word; this format may be used by assemblers and compilers.

The largest reduction in program size and increase in speed results from the consistent and regular architecture and the powerful instruction set. The register file avoids the bottlenecks of dedicated registers, and the instruction set provides a full range of operations on the most frequently used data types.

### 1.4.2 Compiler Efficiency
It is often observed that compilers can find and use specialized or esoteric instructions. For a compiler to work effectively, it must have a regular and consistent architecture, many general-purpose registers, and a complete set of instructions with many addressing modes and data types. Access to parameters and local variables on the procedure stack is supported by the "Index With Short Offset" addressing mode, as well as the Base Address and Base Index addressing modes. In addition, address arithmetic is aided by the Increment and Decrement instructions. Testing of data, logical evaluation, initialization, and comparison of data are made possible by the instructions Test, Test Condition Codes, Load Immediate Into Memory, and Compare Immediate With Memory. Since compilers and assemblers frequently manipulate character strings, the instructions Translate, Translate And Test, Block Compare, and Compare String all result in dramatic speed improvements over software simulations of these important tasks. In addition, any register except R0 can be used as a stack pointer by the Push and Pop instructions.

### 1.4.3 Operating System Support
Interrupt and task-switching features are included to improve operating system implementations. The memory-management and compiler-support features are also quite important.

The interrupt structure has three levels: non-maskable, non-vectored, and vectored. When an interrupt occurs, the program status is saved on the system stack. To further facilitate the switch, a 16-bit identification code is also saved on the stack. The vectored interrupt provides up to 256 interrupt vectors that can point to particular interrupt handlers.

The system/normal mode of operation, the multiple address spaces, and the stack pointers for both modes all provide additional operating system support. In addition, two hardware stack pointers are used to assign separate stacks to system and normal operating modes, thereby further supporting the separation of system and normal operating environments discussed earlier.

### 1.4.4 Support for Many Types of Data Structures
A data structure is a logical organization of primitive elements (byte, word, etc.) whose format and access conventions are well-defined. Common data structures include arrays, lists, stacks, and strings. Since data structures are high-level constructs frequently used in programming, processor performance is significantly enhanced if the CPU provides mechanisms for efficiently manipulating them. The Z8000 offers such mechanisms.

In many applications, one of the most frequently encountered data structures is the array. Arrays are supported in the Z8000 by the Index and Base Index Addressing modes and by segmented addressing. The Base Index Addressing mode allows the use of pointers into an array (i.e., offsets from the array's starting address). Segmented addressing allows an array to be assigned to one segment, which can be referenced simply by segment number.

Lists occur more frequently than arrays in business applications and in general data processing. Lists are supported by Indirect Register and Base Address Addressing modes. The Base Index Addressing mode is also useful for more complex lists.

Stacks are used in all applications for nesting of routines, block structured languages, and interrupt handling. Stacks are supported by the Push and Pop instructions, and multiple stacks may be implemented based on the general-purpose registers of the Z8000. In addition, two hardware stack pointers are used to assign separate stacks to system and normal operating modes, thereby further supporting the separation of system and normal operating environments discussed earlier.

Byte strings are supported by the Translate and Translate And Test instructions. Decimal strings use the Decimal Adjust instruction to do decimal arithmetic on strings of BCD data, packed two characters per byte. The Rotate Digit instructions also manipulate 4-bit data.

### 1.4.5 Two CPU Versions: Z8001 and Z8002
The Z8000 CPU is offered in two versions: the Z8001 48-pin segmented CPU and the Z8002 40-pin nonsegmented CPU. The main difference between the two is addressing range. The Z8001 can directly address 8M bytes of memory; the Z8002 directly addresses 64K bytes. The Z8001 has a non-segmented mode of operation which permits it to execute programs written for the Z8002.

Not all applications require the large address space of the Z8001; for these applications the Z8002 is recommended. Moreover, many multiple-processor systems can be implemented with one Z8001 and several Z8002s, instead of exclusively using Z8001s. Since segmented Z8000s can execute code generated for nonsegmented CPUs, users can buy only the power they require without having to worry about software incompatibility between processors.

## 1.5 Extended Instruction Facility
The Z8000 architecture has a mechanism for extending the basic instruction set through the use of external devices. Special opcodes have been set aside to implement this feature. When the CPU encounters an instruction with these opcodes in its instruction stream, it will perform any indicated address calculation and data transfer; otherwise, it will treat the "extended instruction" as being executed by the external device. Fields have been set aside in these extended instructions which can be interpreted by external devices (Extended Processing Units—EPUs) as opcodes. Thus, by using appropriate EPUs, the instruction set of the Z8000 can be extended to include specialized instructions.

In general, an EPU is dedicated to performing complex and time-consuming tasks in order to unburden the CPU. Typical tasks suitable for specialized EPUs include floating-point arithmetic, data base search and maintenance operations, network interfaces, graphics support operations—a complete list would include most areas of computing.

## 1.6 Summary
The architectural sophistication of the Z8000 microprocessor is on a level comparable with that of the minicomputer. Features such as large address spaces, multiple memory spaces, segmented addresses, and support for multiple processors are beyond the capabilities of the traditional microprocessor. The benefits of this architecture—code density, compiler support, and operating system support—greatly enhance the power and versatility of the CPU. The CPU features that support an external memory management system also enhance the CPU's applicability to large system environments.

# Chapter 2 Architecture

## 2.1 Introduction
This chapter provides an overview of the Z8000 CPU architecture. The basic hardware, operating modes and instruction set are all described. Differences between the two versions of the Z8000 (the nonsegmented Z8002 and the segmented Z8001) are noted where appropriate. Most of the subjects covered here are also treated with greater detail in later chapters of the manual.

## 2.2 General Organization
Figure 2.1 contains a block diagram that shows the major elements of the Z8000 CPU, namely:

*   A 16-bit internal data bus, which is used to move addresses and data within the CPU.
*   A Z-Bus interface, which controls the interaction of the CPU with the outside world.
*   A set of 16 general-purpose registers, which is used to contain addresses and data.
*   Four special-purpose registers, which control the CPU operation.
*   An Arithmetic and Logic Unit, which is used for manipulating data and generating addresses.
*   An instruction execution control, which fetches and executes Z8000 instructions.
*   An exception-handling control, which processes interrupts and traps.
*   A refresh control, which generates memory refresh cycles.

Each of these elements is explained in the following sections. All of the elements are common to both the Z8001 CPU and the Z8002 CPU. The differences between the two versions of the Z8000 are derived from the number of bits in the addresses they generate. The Z8002 always generates a 16-bit linear address, while the Z8001 always generates a 23-bit segmented address (that is, an address composed of a 7-bit segment number and a 16-bit offset).

Figure 2.2 gives a system-level view of the Z8000. It is important to realize that the Z8000 CPU comes with a whole family of support components. The Z8000 Family has been designed to allow the easy implementation of powerful systems. The major elements of such a system might include:

*   The Z-Bus, a multiplexed address/data shared bus that links the components of the system.
*   A Z8000 CPU.
*   One or more Extended Processing Units (EPUs), which are dedicated to performing specialized, time-consuming tasks.
*   A memory sub-system, which in Z8001 systems can include one or more Memory Management Units (MMUs) that offer sophisticated memory allocation and protection features.
*   One or more Direct Memory Access (DMA) controllers for high-speed data transfers.
*   A large number of possible peripheral devices interfaced to the Z-Bus through Universal Peripheral Controllers (UPCs), Serial Communication Controllers (SCCs), Counter-Timer and Parallel I/O Controllers (CIOs) or other Z-Bus peripheral controllers.
*   One or more FIFO I/O Interface Units (FIOs) for elastic buffering between the CPU and another device, such as another CPU in a distributed processing system.

## 2.3 Hardware Interface
Figure 2.3 shows the Z8000 pins grouped according to function. The Z8001 is packaged in a 48-pin DIP and the Z8002 is packaged in a 40-pin DIP. The eight additional pins on the Z8001 are the seven segment-number lines and the segment trap. Except for those eight, all pins on the two CPU versions are identical.

The Z8000 is a Z-Bus CPU; thus, activity on the pins is governed by the Z-Bus protocols (see The Z-Bus Summary). These protocols specify two types of activities: transactions, which cover all data movement (such as memory references or I/O operations), and requests, which cover interrupts and requests for bus or resource control. The following is a brief overview of the Z8000 pin functions; complete descriptions are found in Chapter 9.

### 2.3.1 Address/Data Lines
These 16 lines alternately carry addresses and data. The addresses may be those of memory locations or I/O ports. The bus timing signal lines described below indicate what kind of information the Address/Data lines are carrying.

### 2.3.2 Segment Number (Z8001 only)
These seven lines encode the addresses of up to 128 relocatable memory segments. The segment signals become valid before the address offset signals, thus supporting address relocation by the memory management system.

### 2.3.3 Bus Timing
These three lines include Address Strobe (AS), Data Strobe (DS) and Memory Request (MREQ). They are used to signal the beginning of a bus transaction and to determine when the multiplexed Address/Data Bus holds addresses or data. The Memory Request signal can be used to time control signals to a memory system.

### 2.3.4 Status
These lines function to indicate the kind of transaction on the bus (ST0-ST3), whether it is a read or write (R/W, where High is Read and Low is Write), whether it is on byte or word data (B/W, High = byte, Low = word), and whether the CPU is operating in normal mode or system mode (N/S, High = normal, Low = system). The ST0-ST3 lines also encode additional characteristics of the bus transactions, as Table 2.1 shows. The availability of status information defining the type of bus transaction in advance of data transmission allows bidirectional drivers and other external hardware elements to be enabled before data is transferred.

#### Table 2.1 Status Line Codes
| ST3 | ST2 | ST1 | ST0 | Definition |
| :--- | :--- | :--- | :--- | :--- |
| 0 | 0 | 0 | 0 | Internal operation |
| 0 | 0 | 0 | 1 | Memory refresh |
| 0 | 0 | 1 | 0 | I/O reference |
| 0 | 0 | 1 | 1 | Special I/O reference |
| 0 | 1 | 0 | 0 | Segment trap acknowledge |
| 0 | 1 | 0 | 1 | Non-maskable Interrupt acknowledge |
| 0 | 1 | 1 | 0 | Non-vectored interrupt acknowledge |
| 0 | 1 | 1 | 1 | Vectored interrupt acknowledge |
| 1 | 0 | 0 | 0 | Data memory request |
| 1 | 0 | 0 | 1 | Stack memory request |
| 1 | 0 | 1 | 0 | Data memory request (EPU) |
| 1 | 0 | 1 | 1 | Stack memory request (EPU) |
| 1 | 1 | 0 | 0 | Instruction space access |
| 1 | 1 | 0 | 1 | Instruction fetch, first word |
| 1 | 1 | 1 | 0 | CPU-EPA Transfer |
| 1 | 1 | 1 | 1 | Test and Set Data Access (Z8003/4 only) |

### 2.3.5 CPU Control
These inputs allow external devices to delay the operation of the CPU. The WAIT line, when active (Low), causes the CPU to idle in the middle of a bus transaction, taking extra clock cycles until the WAIT line goes inactive; it is typically used by memory or I/O peripherals which operate more slowly than the CPU. The Stop (STOP) line halts internal CPU operation when the first word of an instruction (or the second word of an EPA instruction) has been fetched. This signal is useful for single-step instruction execution during debugging operations and for enabling Extended Processing Units to halt the CPU temporarily.

### 2.3.6 Bus Control
These lines provide the means for other devices, such as direct memory access (DMA) controllers, to gain exclusive use of the system bus, i.e., the signal lines that are common to several devices in a system. The external device requesting control of the bus inputs a bus request (BUSREQ); the CPU responds with a bus acknowledge (BUSACK) after three-stating, or electrically neutralizing, the Address/Data Bus, Bus Timing lines, Status lines, and Control lines. The Z-Bus allows a daisy chain to be used to enforce a priority among several external devices.

### 2.3.7 Interrupts
Three interrupt inputs are provided: non-maskable interrupts (NMI), vectored interrupts (VI) and non-vectored interrupts (NVI). These permit external devices to suspend the CPU's execution of its current program and begin executing an interrupt service routine.

### 2.3.8 Segment Trap Request (Z8001 only)
This input to the CPU is used by an external memory-management system to indicate that an illegal memory access has been attempted.

### 2.3.9 Multi-Micro Control
The Multi-Micro In (MI) and Multi-Micro Out (MO) lines are used in conjunction with instructions such as MSET and MREQ to coordinate multiple-CPU systems. They allow exclusive use by one CPU of a shared resource in a multiple-CPU system.

### 2.3.10 System Inputs
The four inputs shown at the bottom of Figure 2.3 include +5 V power, ground, a single-phase clock signal and a CPU reset. The reset function is described in Chapter 7.

## 2.4 Timing
Figure 2.4 shows the three basic timing periods of the Z8000: a clock cycle, a bus transaction, and a machine cycle. A clock cycle (sometimes called a T-state) is one cycle of the CPU clock, starting with a rising edge. A bus transaction covers a single data movement on the CPU bus and will last for three or more clock cycles, starting with a falling edge of AS and ending with a rising edge of DS. A machine cycle covers one basic CPU operation and always starts with a bus transaction. A machine cycle can extend beyond the end of a transaction by an unlimited number of clock cycles.

## 2.5 Address Spaces
The Z8000 supports two main address spaces corresponding to the two different kinds of locations that can be addressed:

*   **Memory Address Space.** This consists of the addresses of all locations in the main memory of the computer system.
*   **I/O Address Space.** This consists of the addresses of all I/O ports through which peripheral devices are accessed.

### 2.5.1 Memory Address Space
Memory address space can be further subdivided into Program Memory address space, Data Memory address space, and Stack Memory address space, each for both normal and system modes.

The particular space addressed is determined by the external circuitry from the code appearing at the CPU's output status pins (ST0-ST3) and the state of the Normal/System signal (N/S pin). Data memory reference, stack memory reference, and program memory reference each correspond to a different status code at the ST0-ST3 outputs, allowing three address spaces to be distinguished for each of two operating modes, giving six address spaces in all. Each of the six address spaces has a range as great as the addressing ability of the processor. For the nonsegmented Z8002, each address space can have up to 64K bytes of directly addressable memory. The segmented Z8001, on the other hand, provides up to 8M bytes of memory in each address space.

Segmentation is a means of partitioning memory into variable-sized segments so that a variety of useful functions may be implemented, including:

*   Protection mechanisms that prevent a user from referencing data belonging to others, attempting to modify read-only data or overflowing a stack.
*   Virtual memory, which permits a user to write functioning programs under the assumption that the system contains more memory than is actually available.
*   Dynamic relocating, which allows the placement of blocks of data in physical memory independently of user addresses, allowing better management of the memory resources and sharing of data and programs.

The signals provided on the segmented Z8001 CPU assist in implementing these features, although additional software and external circuitry (such as the Z8010 MMU) are generally required to take full advantage of them. Chapter 3 contains an extensive discussion of segmentation.

### 2.5.2 I/O Address Space
I/O addresses are represented as 16-bit words for both the Z8001 and Z8002.

There are two I/O address spaces, Standard I/O and Special I/O, which are both separate from the memory address space. Each I/O space is accessed through a separate set of I/O instructions, which can be executed only when the CPU is operating in system mode.

Standard I/O instructions transfer data between the CPU and peripherals and Special I/O instructions transfer data to or from external CPU support circuits such as the Z8010 MMU. Access to Standard or Special I/O space is distinguished by the status lines (ST0-ST3).

## 2.6 General-Purpose Registers
The Z8000 CPU contains 16 general-purpose registers, each 16 bits wide. Any general-purpose register can be used for any instruction operand (except for minor exceptions described at the beginning of Chapter 5).

Figure 2.5 shows these general-purpose registers. They allow data formats ranging from bytes to quadruple words. The word registers are specified in assembly-language statements as R0 through R15. Sixteen byte registers, RH0-RL7, which may be used as accumulators, overlap the first eight word registers. Register groupings for larger operands include eight double-word (32-bit) registers, RR0-RR14, and four quad-word registers, RQ0-RQ12, which are used by a few instructions such as Multiply, Divide, and Extend Sign.

As Figure 2.5 illustrates, the CPU has two hardware stack pointers, one dedicated to each of the two basic operating modes, system and normal. The segmented Z8001 uses a two-word stack pointer for each mode (R14'/R15' or R14/R15), whereas the nonsegmented Z8002 uses only one word for each mode (R15' or R15).

The system stack pointer is used for saving status information when an interrupt or trap occurs and for supporting calls in system mode. The normal stack pointer is used for subroutine calls in user programs. In normal-mode operation only the normal stack pointer is accessible. In system mode, the system stack pointer is directly accessed as a general-purpose register. The normal mode stack pointer can be accessed as a special control register.

## 2.7 Special-Purpose Registers
In addition to the general-purpose registers, there are special-purpose registers. These include the Program Status registers, the Program Status Area Pointer, and the Refresh Counter; they are illustrated for both CPU versions in Figure 2.6. Each register can be manipulated by software executing in system mode, and some are modified automatically by certain operations.

### 2.7.1 Program Status Registers
These registers include the Flag and Control Word (FCW) and the Program Counter (PC). They are used to keep track of the state of an executing program.

In the nonsegmented Z8002, the Program Status registers consist of two words: one each for the FCW and the PC. In the segmented Z8001, there are four words: one reserved word, one word for the FCW and two words for the segmented PC.

The low-order byte of the Flag and Control Word (FCW) contains the six status flags, from which the condition codes used for control of program looping and branching are derived. The six flags are:

*   **Carry (C)**, which generally indicates a carry out of the high-order bit position of a register being used as an accumulator.
*   **Zero (Z)**, which is generally used to indicate that the result of an operation is zero.
*   **Sign (S)**, which is generally used to indicate that the result of an operation is a negative number.
*   **Parity/Overflow (P/V)**, which is generally used to indicate either even parity (after logical operations on byte operands) or overflow (after arithmetic operations).
*   **Decimal-Adjust (D)**, which is used in BCD arithmetic to indicate the type of instruction that was executed (addition or subtraction).
*   **Half Carry (H)**, which is used to convert the binary result of a previous addition or subtraction of BCD numbers into the correct decimal result.

Section 6.3 provides more detail on these flags.

The control bits, which occupy the high-order byte of the FCW, are used to enable various interrupts or to control CPU operating modes. The control bits are:

*   **Non-Vectored Interrupt Enable (NVIE), Vectored Interrupt Enable (VIE).** These bits determine whether or not the CPU will accept non-vectored or vectored interrupts (see Section 2.13).
*   **System/Normal Mode (S/N).** When this bit is set to one, the CPU is operating in system mode; when cleared to zero, the CPU is in normal mode (see Section 2.8). The CPU output status line (N/S pin) is the complement of this bit.
*   **Extended Processor Architecture (EPA) Mode.** When this bit is set to one, it indicates that the system contains Extended Processing Units, and hence extended instructions encountered in the CPU instruction stream are executed (see Section 2.12). When this bit is cleared to zero, extended instructions are trapped for software emulation.
*   **Segmentation Mode (SEG).** This bit is implemented only in the Z8001; it is always cleared in the nonsegmented Z8002. When set to one, the CPU is operating in segmented mode, and when cleared to zero, the CPU is operating in nonsegmented mode (see Section 2.8).

### 2.7.2 Program Status Area Pointer (PSAP)
The Program Status Area Pointer points to an array of program status values (FCWs and PCs) in main memory called the Program Status Area. New Program Status register values are fetched from this area when an interrupt or trap occurs. As shown in Figure 2.6, the PSAP comprises either one word (nonsegmented Z8002) or two words (segmented Z8001); for either configuration, the lower byte of the pointer must be zero. Refer to Chapter 7 for more details about the Program Status Area and its layout.

### 2.7.3 Refresh Counter
The CPU contains a programmable counter that can be used to refresh dynamic memory automatically. The refresh counter register consists of a 9-bit row counter, a 6-bit rate counter and an enable bit (Figure 2.6). Refer to Chapter 8 for details of the refresh mechanism.

## 2.8 Instruction Execution
In the normal course of events, the Z8000 CPU will spend most of its time fetching instructions from memory and executing them. This process is called the running state of the CPU. The CPU also has two other states that it occasionally enters.

*   **Stop/Refresh State.** This is really one state, although it may be entered in two different ways: either automatically for a periodic memory refresh; or when the STOP line is activated. In this state, program execution is temporarily suspended and the CPU makes use of the Refresh Counter to generate refreshes. For more information, consult Chapter 8.
*   **Bus-Disconnect State.** This is the state the CPU enters when the DMA, or some other bus requester, takes over the bus. Program execution is suspended and the CPU disconnects itself from the bus.

While the CPU is in the running state, it can either be handling interrupts or executing instructions. If it is executing instructions, the Z8000 can be in the system or normal execution mode. In system mode, privileged instructions (such as those which perform I/O) can be executed; in normal mode they cannot. This dichotomy allows the creation of operating system software, which controls CPU resources and is protected from application program action.

In addition, the CPU will be in either segmented or nonsegmented mode. In segmented mode, which is available only on the Z8001, the program uses 23-bit segmented addresses for memory accesses; in nonsegmented mode, which is available on both CPUs, the program uses 16-bit nonsegmented addresses for memory accesses.

While executing instructions, the mode of the CPU is controlled by bits in the FCW (Section 2.7). While handling interrupts, the CPU is always in system mode and, for the Z8001, in segmented mode.

## 2.9 Instructions
The Z8000 instruction set contains over 400 different instructions which are formed by combining the 110 distinct instruction types (opcodes) with the various data types and addressing modes. The complete set is divided into the following groups:

*   **Load and Exchange** for register-to-register and register-to-memory operations, including stack management.
*   **Arithmetic** for arithmetic operations, including multiply and divide, on data in either registers or memory. Compare, increment, and decrement functions are included.
*   **Logical** for Boolean operations on data in registers or memory.
*   **Program Control** for program branching (conditional or unconditional), calls, and returns.
*   **Bit Manipulation** for setting, resetting and testing individual bits of bytes or words in registers or memory.
*   **Rotate and Shift** for bytes, words, or, for shifts only, long words within registers.
*   **Block Transfer and String Manipulation** for automatic memory-to-memory transfers of data blocks or strings, including compare and translate functions.
*   **Input/Output** for transfers of data between I/O ports and memory or registers.
*   **Extended** for operations involving Extended Processing Units.
*   **CPU Control** for accessing special registers, controlling the CPU operating state, synchronizing multiple-processor operation, enabling/disabling interrupts, mode selection, and memory refresh.

Chapter 6 contains details on the full instruction set.

### 2.9.1 Instruction Formats
Formats of the instructions are shown in Figure 2.7. The two most significant bits in the instruction word determine whether the compact instruction format (A) or the general instruction format (B) is used. Compact formats encode the four most frequently used instructions into single words, thereby saving on instruction-memory usage and increasing execution speed. As long as the two most significant bits are not logic ones, the general format applies. In the general format, the two most significant bits in conjunction with the source-register field are sufficient for specifying any of the five main addressing modes. Source and destination fields are four bits wide for addressing the 16 general-purpose registers.

## 2.10 Data Types
The Z8000 supports manipulation of eight data types. Five of these have fixed lengths; the other three have lengths that can vary dynamically. Each data type is supported by a number of instructions which operate upon it directly. These data types are:

*   Bit
*   Signed and unsigned byte, word, long word, or quadruple word binary integer
*   Byte or word-length logical value
*   Word (nonsegmented) or long word (segmented) address
*   Unsigned byte decimal integer
*   Dynamic-length string of byte data
*   Dynamic-length string of word data
*   Dynamic-length stack of word data

Bits can be manipulated in registers or memory. Binary and decimal integers and logical values can be manipulated in registers, although operands can be fetched directly from memory. Addresses are manipulated only in registers, and strings and stacks are manipulated only in memory.

## 2.11 Addressing Modes
The information included in Z8000 instructions consists of the function to be performed, the type and size of data elements to be manipulated, and the location of the data elements. Locations are designated using one of the following eight addressing modes:

*   **Register Mode.** The data element is located in one of the 16 general-purpose registers.
*   **Immediate Mode.** The data element is located in the instruction.
*   **Indirect Register Mode.** The data element can be found in the location whose address is in a register.
*   **Direct Address Mode.** The data element can be found in the location whose address is in the instruction.
*   **Index Mode.** The data element can be found in the location whose address is the sum of the contents of a 16-bit index value in a register and an address in the instruction.
*   **Relative Address Mode.** The data element can be found in the location whose address is the sum of the contents of the program counter and a 16-bit displacement in the instruction.
*   **Base Address Mode.** The data element can be found in the location whose address is the sum of a base address in a register and a displacement in the instruction.
*   **Base Index Mode.** The data element can be found in the location whose address is the sum of a base address in a register and a displacement in the instruction.

Chapter 5 defines and illustrates the eight addressing modes.

## 2.12 Extended Processing Architecture
An important feature of the Z8000 CPU architecture is the Extended Processing Architecture (EPA) facility. This facility provides a mechanism by which the basic instruction set of the CPU can be extended via external devices, called Extended Processing Units (EPUs). A special set of instructions, called extended instructions, is used to control this feature. When the CPU encounters one of these extended instructions in its instruction stream, it will either trap to a software trap handler to process the instruction or it will perform the data transfer portion of the instruction (leaving the data manipulation part of the instruction to the EPU). Whether the CPU traps or transfers data depends on the setting of the EPA bit in the FCW.

The underlying philosophy behind the EPA feature is a view of the CPU as an instruction processor—the CPU fetches instructions, fetches data associated with the instruction, performs the operations and stores the result. Extending the number of operations performed does not affect the instruction fetch and address calculation portion of the CPU activity. The extended instructions exploit this feature—the CPU fetches the instruction and performs any address calculation that may be needed. It also generates the timing signals for the memory access if data must be transferred between memory and the extended processor. But the actual data manipulation is handled by the EPU. The Extended Processing Architecture is explained more fully in Chapter 4.

### 2.13 Exceptions
Three events can alter the normal execution of a Z8000 program: hardware interrupts that occur when a peripheral device needs service, synchronous software traps that occur when an error condition arises, and system reset. Chapter 7 contains a detailed description of exceptions and how they are handled. Interrupt requests and segmentation trap requests are accepted after the completion of the instruction execution during which they were made. At the end of the instruction execution, a spurious instruction fetch transaction is usually performed before the interrupt acknowledge sequence begins, but the Program Counter is not affected by the spurious fetch.

#### 2.13.1 Reset
A system reset overrides all other operating conditions. It puts the CPU in a known state and then causes a new program status to be fetched from a reserved area of memory to reinitialize the Flag and Control Word (FCW) and the Program Counter (PC).

#### 2.13.2 Traps
Traps are synchronous events that are usually triggered by specific instructions and recur each time the instruction is executed with the same set of data and the same process or state. The four kinds of traps are:

*   **Extended instruction attempted in non-EPA mode.** The current instruction is an EPU instruction, but the system is not in EPA mode. This trap allows system software to either simulate instruction or abort the program.
*   **Privileged instruction attempted in normal mode.** The current instruction is privileged (I/O for example), but the CPU is in normal mode.
*   **System Call (SC) instruction.** This instruction provides a controlled access from normal-mode to system-mode operation.
*   **Segmentation violation (supplied by external circuit).** A segmentation violation, such as using an offset larger than the defined length of the segment, can be made to cause an external memory management system to signal a segmentation trap. This can occur only with the segmented Z8001.

#### 2.13.3 Interrupts
Interrupts are asynchronous events typically triggered by peripheral devices needing attention. The three kinds of interrupts associated with the three interrupt lines of the CPU are:

*   **Non-maskable interrupts (NMI).** These interrupts cannot be disabled and are usually reserved for critical external events that require immediate attention.
*   **Vectored interrupts (VI).** These interrupts cause eight bits of the vector output by the interrupting device to be used to select a particular interrupt service procedure to which the program automatically branches.
*   **Non-vectored interrupts (NVI).** These interrupts are maskable interrupts which are all handled by the same interrupt procedure.

#### 2.13.4 Trap and Interrupt Service Procedures
Interrupts and traps are handled similarly by the Z8000 CPU. The Z8000 CPU automatically acknowledges interrupts and processes traps in system mode. In the case of the segmented Z8001, the CPU uses the segmented mode regardless of its mode at the time of interrupt or trap. The program status information in effect just prior to the interrupt or trap is pushed onto the system stack. An additional word, which serves as an identifier for the interrupt or trap, also is pushed onto the system stack, where it can be accessed by the interrupt or trap handler. The Program Status registers are loaded with new status information obtained from the Program Status Area of memory. Then control is transferred to the service procedure, whose address is now located in the Program Counter. For details of interrupt and trap handling, refer to Chapter 7.

---

# Chapter 3
# Address Spaces

## 3.1 Introduction
Programs and data may be located in the main memory of the computer system or in peripheral devices. In either case, the location of the information must be specified by an address of some sort before that information can be accessed. A set of these addresses is called an address space.

The Z8000 supports two different types of addresses and thus two categories of address spaces:

*   **Memory addresses**, which specify locations in main memory.
*   **I/O addresses**, which specify the ports through which peripheral devices are accessed.

## 3.2 Types of Address Spaces
Within the two general types of address spaces (memory and I/O), it is possible to distinguish several subcategories. Figure 3.1 shows the address spaces that are available on both the Z8001 and the Z8002.

The difference between the Z8001 and the Z8002 lies not in the number and type of address spaces, but rather in the organization and maximum size of each space. For the Z8001, each of the six memory address spaces contains 8M byte addresses grouped into 128 segments, for a total memory addressing capability of 48M bytes. For the Z8002, each memory space is a homogeneous collection of 64K byte addresses. In both the Z8001 and the Z8002, the I/O address spaces contain 64K port addresses. When an address is used to access data, the address spaces may be distinguished by the state of the status lines (ST0-ST3) (which is determined by the way the address was generated) and by the value of the Normal/System line (N/S) (which is determined by the state of the S/N bit in the FCW).

*   **Instruction Space** (status = 1100 or 1101), normal mode (N/S = 1) or system mode (N/S = 0). These spaces typically address memory that contains user programs (normal) or system programs (system).
*   **Data Spaces** (status = 1000 or 1010), normal mode (N/S = 1) or system mode (N/S = 0). These spaces may be used to address the data that user or system programs operate on.
*   **Stack Spaces** (status = 1001 or 1011), normal mode (N/S = 1) or system mode (N/S = 0). These spaces can be used to address the system and normal program stacks.
*   **Standard I/O Space** (status = 0010). This space addresses all the I/O ports that are used for Z8000 peripherals.
*   **Special I/O Space** (status = 0011). This space addresses ports in CPU support chips (such as the Z8010 Memory Management Unit).

| Memory Address Spaces (System Mode) | Memory Address Spaces (Normal Mode) | I/O Address Spaces (System Mode) |
| :--- | :--- | :--- |
| Instructions | Instructions | Standard I/O |
| Data | Data | Special I/O |
| Stack | Stack | |

## 3.3 I/O Address Space
All I/O addresses are represented by 16-bit words. Each of the ports addressed is either eight or 16 bits wide. Transfer to or from 16-bit ports always involves word data and, for 8-bit ports, byte data.

The address of a 16-bit port may be even or odd for both address spaces. In Standard I/O space, byte ports must have an odd address; in Special I/O space, byte ports must have an even address.

## 3.4 Memory Address Spaces
Each memory address space in the Z8002, or each segment in each memory address space on the Z8001, can be viewed as addressing a string of 64K bytes numbered consecutively in ascending order. The 8-bit byte is the basic addressable element in Z8000 memory address spaces. However, there are three other addressable data elements:

*   Bits, in either bytes or words.
*   16-bit words.
*   32-bit long words.

### 3.4.1 Addressable Data Elements
The nature of the data element being addressed depends on the instruction being executed. As Chapter 6 explains in detail, different assembler mnemonics are used for addressing bytes, words, and long words. Moreover, only certain instructions can address bits.

A bit can be addressed by specifying a byte or word address and the number of the bit within the byte (0-7) or word (0-15). Bits are numbered right-to-left, from the least to the most significant. This is consistent with the convention that bit n corresponds to position 2^n in the conventional representation of binary numbers.

The address of a data type longer than one byte (word or long word) is the same as the address of the byte with the lowest memory address within the word or long word. This is the leftmost, highest-order, or most significant byte of the word or long word. Word or long word addresses are always even-numbered. Low bytes of words are stored at odd-numbered memory locations and high bytes at even-numbered locations. Byte addresses can be either even- or odd-numbered.

Certain memory locations are reserved for system-reset handling. These are described fully in Chapter 7. Except for these reserved locations, there are no memory addresses specifically designated for a particular purpose.

**Addressable Data Elements Layout:**

```text
Bits in a Byte:
7 6 5 4 3 2 1 0

Bits in a Word:
15 14 13 12 11 10 9 8 | 7 6 5 4 3 2 1 0

Byte:
[ Address n ]

Word:
[ Address n (MSB) ] [ Address n + 1 (LSB) ]

Long Word:
[ Address n (MSB) ] [ Address n + 1 ]
[ Address n + 2   ] [ Address n + 3 (LSB) ]
```

### 3.4.2 Segmented and Non-Segmented Addresses
The two versions of the Z8000 CPU generate two kinds of addresses with different lengths. The Z8002 generates a 16-bit address specifying one of 64K bytes. The Z8001 generates a 23-bit segmented address. A segmented address consists of a 7-bit segment number, which specifies one of 128 segments, and a 16-bit offset, which specifies one of up to 64K bytes in the segment. Each segment is an independent collection of bytes; thus, instructions and multiple byte data elements cannot cross segment boundaries.

Nonsegmented addresses are 16 bits long and thus can be stored in word registers (Rn) or in memory as word-length addressable elements. The 23-bit segmented addresses are embedded in a 32-bit long word and thus can be stored in a long word register (RRn) or a long word memory element. There is a short encoding of segmented addresses that appears in instructions and requires only 16 bits.
It is important to realize that even though the Z8001 can operate in nonsegmented mode (Chapter 4), it always generates segmented addresses. In non-segmented mode the segment number is supplied by the program counter segment number.

### 3.4.3 Segmentation and Memory Management
Addresses manipulated by the programmer, used by instructions, and output by the Z8001 are called "logical addresses." An external memory-management circuit can translate logical addresses into physical (actual) memory addresses and perform certain checks to insure data and programs are properly accessed.
The Z8010 Memory Management Unit (MMU) performs this function for the segmented addresses produced by the Z8001 CPU. A single MMU holds 64 descriptors. Each descriptor tells where in physical memory the segment lies, how long the segment is, and what kind of accesses can be made to the segment. The MMU uses these descriptors to translate logical segment numbers and offsets into 24-bit physical addresses. At the same time, the MMU checks for errors such as writing into a read-only segment or a system segment being accessed by a nonsystem program. MMUs are designed to be combined so that more than 64 descriptors can be supported at once.

Some of the benefits of the memory management features provided by the MMU are:

- Provision for flexible and efficient allocation of physical memory resources during the execution of programs.
- Hardware stack overflow protection.
- Support for multiple, independently executing programs that can share access to common code and data.
- Protection from unauthorized or unintentional access to data or programs.
- Detection of obviously incorrect use of memory by an executing program.
- Separation of users from system functions.

Segmentation in the Z8001 helps support memory management in two ways:

1. By allowing part of an address (the segment number) to be output by the CPU early in a memory cycle. This keeps access to the address descriptor in the MMU from adding to the basic access time of the memory.
2. By providing a standard, variable-sized unit of memory for the protection, sharing, and movement of data.

In addition, segmentation is a natural model for the support of modular programs and data in a multi-programming environment. It efficiently supports re-entrant programs by providing data relocation for different tasks using common code. More information about the MMU and memory management can be found in An Introduction to the Z8010 MMU Memory Management Unit and in the Z8010 MMU Manual and the Z8015 Paged MMU User's Manual.

---

# Chapter 4
# CPU Operation

## 4.1 Introduction
This chapter gives a fundamental description of the operating states of the Z8000 CPU and the process of instruction execution. The details of instruction execution are described in Chapters 5 and 6. Other detailed aspects of Z8000 operation are given in Chapter 7 (Exceptions) and Chapter 8 (Refresh). Chapter 9 describes CPU operations as they are manifest on the external pins of the CPU.

## 4.2 Operating States
The Z8000 CPU has three operating states: Running state, Stop/Refresh state, and Bus-Disconnect state. Running state is the usual state of the processor: the CPU is executing instructions or handling exceptions. Stop/Refresh state is entered when the STOP line is asserted or the refresh counter indicates that a periodic refresh should be done. In this state, memory refresh transactions are generated continually (see Chapter 8). Bus-Disconnect state is entered when the CPU acknowledges a bus request and gives up control of the system bus.

### 4.2.1 Running State
While the CPU is in Running state, it is either executing instructions (as described in Section 4.3) or handling exceptions (as described in Chapter 7). The CPU is normally in Running state, but will leave this state in response to one of three conditions:
*   The refresh mechanism indicates that a periodic refresh needs to be done, in which case the CPU temporarily enters Stop/Refresh state.
*   An external stop request pushes the CPU into Stopped state.
*   An external bus request pushes the CPU into Bus-Disconnect state.

### 4.2.2 Stop/Refresh State
While the CPU is in Stop/Refresh state, it generates a continuous stream of refresh cycles (as discussed in Chapter 8) and does not perform any other functions. This state provides for the generation of memory refreshes by the CPU and allows external devices to suspend CPU operation. This feature can be used to force single-step operation of the processor or to synchronize the CPU with an Extended Processing Unit (as described in Section 4.4).

The CPU enters Stop/Refresh state when the refresh mechanism needs to do a refresh or when the stop line is activated. It leaves Stop/Refresh state when neither of these conditions holds or when a bus request causes the CPU to enter Bus-Disconnect state.

### 4.2.3 Bus-Disconnect State
While the CPU is in Bus-Disconnect state, it does nothing. It enters Bus-Disconnect state from either Running state or Stop/Refresh state when a bus request has been received on BUSREQ and acknowledged on BUSACK (as described in Chapter 9). While in this state, it disconnects itself from the bus by 3-stating its output. It leaves Bus-Disconnect state when the external bus request has been released. Note that Bus-Disconnect state is highest in priority in that the presence of a bus request will force the CPU into this state, regardless of any conditions indicating that a different state should be entered.

### 4.2.4 Effect of Reset
Activation of the CPU's RESET line puts the CPU in a nonoperational state within five clock cycles, regardless of its previous state or the states of its other inputs. The CPU will remain in this state until RESET is deactivated. When this occurs, the program enters one of the three operating states described above, depending on the state of BUSREQ and STOP inputs. Reset is more fully described in Chapters 7 and 9.

## 4.3 Instruction Execution
While the CPU is in Running state and executing instructions, it is controlled by the Program Status registers. The Program Counter gives the address from which instructions are fetched, the flags control branching (as described in Chapter 6), and the control bits determine the mode in which the CPU operates and the interrupts that are masked (see Chapter 7).

Instruction execution consists of the repeated application of two steps:
*   Fetch one or more words comprising a single instruction from the program memory address space at the address specified by the Program Counter (PC).
*   Perform the operation specified by the instruction and update the Program Counter and flags in the Program Status registers.

The operation performed by an instruction and the way the flags are updated depends on the particular instruction being executed and is described in Chapter 6. For most instructions, the PC value is updated to point to the word immediately following the last word of the instruction. The effect of this is that instructions are fetched sequentially from memory. Exceptions to this are Branch, Call, Interrupt Return, Load Program Status, System Call, Halt, Decrement and Jump if Non-Zero, and Return instructions, which cause the PC to be set to a value generated by the instruction. This causes a transfer of control with execution continuing at the new address in PC.

The Z8000 CPU is able to overlap the fetching of one instruction with the operation of the previous instruction. This facility, called Instruction Look-Ahead, is illustrated in Figure 4.3. After executing an instruction and in some cases (explained in Chapters 6 and 7) during an instruction's execution, the CPU checks to see if there are any traps or interrupts pending and not masked. If so, it temporarily suspends instruction execution and begins a standard exception-handling sequence.

### 4.3.1 Running-State Modes
While the CPU is executing instructions, its mode will be controlled by three control bits in the FCW: the System/Normal Mode bit (S/N), the Segmentation Mode bit (SEG), and the EPA Mode bit.

### 4.3.2 Segmented and Nonsegmented Modes
The segmentation mode of the CPU (segmented or nonsegmented) determines the size and format of addresses that are directly manipulated by programs. In segmented mode (SEG = 1), programs manipulate 23-bit segmented addresses; in nonsegmented mode (SEG = 0), programs generate 16-bit nonsegmented addresses. There are also the following differences in the address portions of instructions, which are due to the difference in address size:
*   Indirect and Base Registers are 32-bit registers in segmented mode and 16-bit registers in nonsegmented mode.
*   Addresses embedded in instructions are always 16-bits in nonsegmented mode. They consist of a 7-bit segment number and either an 8-bit or 16-bit offset in segmented mode.

Segmented mode is available only on the Z8001 CPU; on the Z8002, the segment bit is always forced to zero, indicating nonsegmented mode. Because the Z8001 supports segmented and nonsegmented modes, it is possible to run programs written for the Z8002 on the Z8001 without alteration. The Z8001 CPU always generates segmented addresses, even when operating in nonsegmented mode. In nonsegmented mode, the segment number is the value of the segment number field of the Program Counter.

### 4.3.3 Normal and System Modes
The operation mode of the CPU (system mode or normal mode) determines which instructions can be executed and which Stack Pointer register is used. In system mode (S/N = 1), all instructions can be executed. While in normal mode, certain privileged instructions that alter sensitive parts of the machine state (such as I/O operations or changes to control registers) cannot be executed.

The second distinction between system and normal mode is access to the system or normal Stack Pointer. As shown in Table 4.1, there are two Stack Pointer registers (Register 15 in the Z8002 and Registers 14 and 15 in the Z8001): one for normal mode and one for system mode.

#### Table 4.1 Registers Accessed by References to R14 and R15
| Register Referenced by Instruction | System Mode (Segmented) | System Mode (Nonsegmented) | Normal Mode (Segmented) | Normal Mode (Nonsegmented) |
| :--- | :--- | :--- | :--- | :--- |
| **R14** | System R14 | Normal R14 | Normal R14 | Normal R14 |
| **R15** | System R15 | System R15 | Normal R15 | Normal R15 |
| **RR14** | System R14/R15 | Normal R14 / System R15 | Normal R14/R15 | Normal R14/R15 |

Note: Z8002 always runs in nonsegmented mode.

In normal mode, the system stack pointer is not accessible; in system mode the normal stack pointer is accessed by using a special Load Control Register instruction (described in Chapter 6).

## 4.4 Extended Instructions
The Z8000 CPU supports seven types of extended instructions, which can be executed cooperatively by the CPU and an external Extended Processing Unit. The execution of these instructions is controlled by the EPA control bit in the FCW.

When the EPA bit is zero, it indicates that there is no Extended Processing Unit connected to the CPU and causes the CPU to trap (as explained in Chapter 7) when it encounters an extended instruction. This allows the operation of the extended instruction to be simulated by software running on the CPU.

If the EPA bit is set, it indicates that an Extended Processing Unit is connected to the CPU. The CPU will fetch the extended instruction and perform any address calculation required by that instruction. If the instruction specifies the transfer of data, the CPU will generate the timing signals for this transfer. While the EPU is executing the instruction, the CPU can be fetching and executing further instructions.

---

# Chapter 5
# Addressing Modes

## 5.1 Introduction
This chapter describes the eight addressing modes used by instructions to access data in memory or CPU registers. Separate sets of examples for the nonsegmented and segmented modes of operation are given at the end of the chapter.

An instruction is a consecutive list of one or more words aligned at even-numbered byte addresses in memory. Most instructions have operands in addition to an operation code (opcode). These operands may reside in CPU registers or memory locations. The modes by which references are made to operands are called "addressing modes."

| Addressing Mode | Abbreviation | Operand Addressing |
| :--- | :--- | :--- |
| **Register** | R | Operand is in a register. |
| **Immediate** | IM | Operand is in the instruction. |
| **Indirect Register** | IR | Register contains the address of the operand. |
| **Direct Address** | DA | Instruction contains the address of the operand. |
| **Index** | X | Address is Instruction address + register. |
| **Relative Address** | RA | Address is PC + displacement in instruction. |
| **Base Address** | BA | Address is Base register + displacement in instruction. |
| **Base Index** | BX | Address is Base register + Index register. |

*Note: Do not use R0 or RR0 as indirect, index, or base registers.*

## 5.2 Use of CPU Registers
The 16 general-purpose CPU registers can, with the exceptions noted below, be used in any of the following ways:
*   As accumulators, where the data to be manipulated resides within the register.
*   As pointers, where the value in the register is the memory address of the operand.
*   As index or base registers, where the contents of the register and the word(s) following the instruction are combined to produce the address of the operand.

There are two exceptions to the above uses:
1.  Register R0 (or RR0 in segmented mode) cannot be used as an indirect register, base register, index register, or software stack pointer.
2.  Register R15' (or RR14' in the Z8001) is used in acknowledging interrupts and therefore can never be used as an accumulator in system-mode operation.

## 5.3 Addressing Mode Descriptions
The following pages contain descriptions of the addressing modes of the Z8000. Each description:
*   Explains how the operand address is calculated.
*   Indicates which address space (Register, I/O, Data Memory, etc.) the operand is located in.
*   Shows the assembly language format.
*   Works through an example.

## 5.4 Descriptions and Examples (Z8002 and Z8001 Nonsegmented Mode)
In this section, the addressing modes of both the Z8002 and the nonsegmented mode Z8001 and Z8003 are described.

### 5.4.1 Register (R)
In the Register Addressing mode the instruction processes data taken from a specified general-purpose register. Storing data in a register allows shorter instructions and faster execution than occur with instructions that access memory.

The operand is always in the register address space. The register length (byte, word, register pair, or register quadruple) is specified by the instruction opcode.

**Assembler language format:**
RHn, RLn   Byte register
Rn         Word register
RRn        Double-word register
RQn        Quadruple-word register

**Example of R mode:**
LD R2, R3    !load the contents of!
             !R3 into R2!

**Before Execution**
R2 [ A6B8 ]
R3 [ 9A20 ]

**After Execution**
R2 [ 9A20 ]
R3 [ 9A20 ]

---

### 5.4.2 Immediate (IM)
The Immediate Addressing mode is the only mode that does not indicate a register or memory address as the source operand. The data processed by the instruction is in the instruction.

Because an immediate operand is part of the instruction, it is always located in the program memory address space. Immediate mode is often used to initialize registers. The Z8000 is optimized for this function, providing several short immediate instructions to reduce the length of programs.

**Assembler language format (see also Chapter 6):**
#data

**Example of IM mode:**
LDB RH2, #%55    !load hex 55 into RH2!

**Before Execution**
R2 [ 6789 ]

**After Execution**
R2 [ 5589 ]

---

### 5.4.3 Indirect Register (IR)
In the Indirect Register Addressing mode, the data processed is not the value in the specified register. Instead, the register holds the address of the data.

A single word register is used to hold the address. Any general-purpose word register can be used except R0.

Depending on the instruction, the operand specified by IR mode will be located in either Standard I/O address space (I/O instructions), Special I/O address space (Special I/O instructions), or data or stack memory address spaces. For non-I/O references, the operand will be in stack memory space if the stack pointer (R15) is used as the indirect register; otherwise, the operand will be in data memory space.

The Indirect Register mode may save space and reduce execution time when consecutive locations are referenced. This mode can also be used to simulate more complex addressing modes, since addresses can be computed before the data is accessed.

**Assembler language format (see also Chapter 6):**
@Rn

**Example of IR mode:**
LD R2, @R5    !load R2 with the!
              !data addressed by the!
              !contents of R5!

**Before Execution**          **Data Memory**
R2 [ 030F ]
R3 [ 0005 ]                   170A [ A023 ]
R4 [ 2000 ]                   170C [ 0B0E ]
R5 [ 170C ]                   170E [ 10D0 ]

**After Execution**
R2 [ 0B0E ]
R3 [ 0005 ]
R4 [ 2000 ]
R5 [ 170C ]

---

### 5.4.4 Direct Address (DA)
In the Direct Addressing mode, the data processed is found at the address specified in the instruction.

Depending upon the instruction, the operand specified by DA mode will be either in Standard I/O space (I/O instructions), in Special I/O space (Special I/O instructions), or in data memory space.

This mode is also used by Jump and Call instructions to specify the address of the next instruction to be executed in program memory. (Actually, the address serves as an immediate value that is loaded into the Program Counter.)

**Assembler language format (see also Chapter 6):**
address    either memory, I/O, or Special I/O

**Example of DA mode:**
LDB RH2, %5E23    !load RH2 with the!
                  !data in address!
                  !5E23!

**Before Execution**
R2 [ 167891 ]  (Note: Original OCR text shows 167891, possibly meaning 1678 / 91)
Address 5E23 contains: 06

**After Execution**
R2 [ 06891 ]

### 5.4.5 Index (X)
In the Index Addressing mode, the data processed is found at an address that is the sum of the contents of a register and an address specified in the instruction.

The instruction contains a 16-bit address. Any word register can be used as the index register except R0.

Operands specified by X mode are always in the data memory address space.

**Assembler language format (see also Chapter 6):**
address(Rn)

**Example of X mode:**
LD R4, %231A(R3)    !load into R4 the con-!
                    !tents of the memory!
                    !location whose!
                    !address is 231A +!
                    !the value in R3!

**Before Execution**          **Data Memory**
R3 [ 01FE ]                   2516 [ F3C2 ]
R4 [ 203A ]                   2518 [ 3D0E ]
                              251A [ 7ADA ]

**Address Calculation**
  231A
+ 01FE
  2518

**After Execution**
R3 [ 01FE ]
R4 [ 3D0E ]

---

### 5.4.6 Relative Address (RA)
In the Relative Addressing mode, the data processed is found at an address relative to the current instruction. The instruction specifies a two's complement displacement which is combined with the contents of the program counter to form the target address. The program counter value used is the address of the instruction following the current instruction.

Relative Addressing is used by certain program control instructions (Jump, Call, etc.) to specify the target address. (Actually, the calculated address is loaded into the program counter.) It is also used by the Load Relative (LDR) instructions to specify an operand in the program memory address space.

The displacement is a signed 8-bit or 16-bit value.

**Assembler language format (see also Chapter 6):**
address

**Example of RA mode:** (Note that the symbol "$" is used for the value of the current program counter.)
LDR R2, $+%6    !load into R2 the con-!
                !tents of the memory!
                !location whose!
                !address is the current!
                !program counter!
                !+ hex 6!

Because the program counter will be advanced to point to the next instruction when the address calculation is performed, the constant that occurs in the instruction will actually be +2.

**Before Execution**          **Program Memory**
R2 [ A0F0 ]                   0202 [ 3102 ] } Instruction
PC [ 0202 ]                   0204 [ 0002 ]
                              0206 [ E801 ]
                              0208 [ FFFE ]

**Address Calculation**
  0206
+    2
  0208

**After Execution**
R2 [ FFFE ]
PC [ 0206 ]

---

### 5.4.7 Base Address (BA)
The Base Addressing mode is similar to Index mode in that a base and offset are combined to produce the effective address. In Base Addressing, however, a register contains the base address, and the displacement is expressed as a 16-bit value in the instruction. The two are added and the resulting address points to the data to be processed. This addressing mode may be used only with the Load instructions. Base Addressing mode, as a complement to Index mode, allows random access to tables or other data structures where the displacement of an element within the structure is known, but the base of the particular structure must be computed by the program.

Any word register can be used for the base address except R0.

An operand specified by BA mode will be in stack memory space if the base register is the stack pointer (R15) and in data memory space otherwise.

**Assembler language format (see also Chapter 6):**
Rn(#disp)

**Example of BA mode:**
LDL R5(#%18), RR2    !load the long word!
                     !in RR2 into the!
                     !memory location!
                     !whose address is the!
                     !value in R5 + hex!
                     !18!

**Before Execution**          **Data Memory**
RR2: R2 [ 0A00 ]
     R3 [ 1500 ]              20C0 [ OABE ]
R4      [ 3100 ]              20C2 [ F50D ]
R5      [ 20AA ]              20C4 [ BADE ]
                              20C6 [ BOD1 ]

**Address Calculation**
  20AA
+   18
  20C2

**After Execution**           **Data Memory**
RR2: R2 [ 0A00 ]
     R3 [ 1500 ]              20C0 [ OABE ]
R4      [ 3100 ]              20C2 [ 0A00 ]
R5      [ 20AA ]              20C4 [ 1500 ]
                              20C6 [ BOD1 ]

---

### 5.4.8 Base Index (BX)
The Base Index addressing mode is an extension of the Base Addressing mode and may be used only with the Load instructions. In this case, both the base address and index (displacement) are held in registers. This mode allows access to memory locations whose physical addresses are computed at runtime and are not fully known at assembly time.

Any word register can be used for either the base address or the index except R0.

An operand specified by BX mode will be in stack memory space if the base register is the stack pointer (R15) and in data memory otherwise.

**Assembler language format (see also Chapter 6):**
Rn(Rm)

**Example of BX mode:**
LD R2, R5(R3)    !load into R2 the!
                 !value whose address!
                 !is the value in!
                 !R5 + the value in R3!

**Before Execution**          **Data Memory**
R2 [ 1F3A ]
R3 [ FFFE ]                   14FE [ 0101 ]
R4 [ 0300 ]                   1500 [ BODE ]
R5 [ 1502 ]                   1502 [ F732 ]

**Address Calculation**
  1502
+ FFFE
  1500

**After Execution**
R2 [ BODE ]
R3 [ FFFE ]
R4 [ 0300 ]
R5 [ 1502 ]

## 5.5 Descriptions and Examples (Segmented Z8001)
In this section, "<<nn>>" will often be used to refer to segment number nn.

### 5.5.1 Register (R)
In the Register Addressing mode, the instruction processes data taken from a specified general purpose register. Storing data in a register allows shorter instructions and faster execution than occur with instructions that access memory.

The operand is always in the register address space. The register length (byte, word, register pair, or register quadruple) is specified by the instruction opcode.

**Assembler language formats (see also Chapter 6):**
RHn, RLn   Byte register
Rn         Word register
RRn        Double-word register
RQn        Quadruple-word register

**Example of R mode:**
LDL RR2, RR4    !load the contents!
                !of RR4 into RR2!

**Before Execution**
RR2: R2 [ A6B8 ]
     R3 [ 9A20 ]
RR4: R4 [ 38A6 ]
     R5 [ 745E ]

**After Execution**
RR2: R2 [ 38A6 ]
     R3 [ 745E ]
RR4: R4 [ 38A6 ]
     R5 [ 745E ]

---

### 5.5.2 Immediate (IM)
The Immediate Addressing mode is the only mode that does not indicate a register or memory address as the location of the source operand. The data processed by the instruction is in the instruction.

Because an immediate operand is part of the instruction, it is always located in the program memory address space. Immediate mode is often used to initialize registers. The Z8000 is optimized for this function, providing several short immediate instructions to reduce the length of programs.

**Assembler language format (see also Chapter 6):**
#data

**Example of IM mode:**
LDB RH2, #%55    !load hex 55 into RH2!

**Before Execution**
R2 [ 167891 ]

**After Execution**
R2 [ 155891 ]

---

### 5.5.3 Indirect Register (IR)
In the Indirect Register Addressing mode, the data processed is not the value in the specified register. Instead, the register holds the address of the data.

Depending upon the instruction, the operand specified by IR mode will be located in either I/O address space (I/O instructions), Special I/O address space (Special I/O instructions), or data or stack memory address spaces. For non-I/O references, the operand will be in stack memory space if the stack pointer (RR14) is used as the indirect register, otherwise the operand will be in data memory space.

A 16-bit register is used to hold an I/O or Special I/O address; a register pair is used to hold a memory address. Any general-purpose register or register pair may be used except R0 or RR0.

The Indirect Register mode may save space and reduce execution time when consecutive locations are referenced. This mode can also be used to simulate more complex addressing modes, since addresses can be computed before the data is accessed.

**Assembler language formats (see also Chapter 6):**
@Rn     Contains I/O or Special I/O address.
@RRn    Contains memory address.

**Example of memory access using IR mode:**
LD R2, @RR4    !load into R2 the!
               !value in the memory!
               !location addressed!
               !by the contents of!
               !RR4!

**Before Execution**          **Data Memory**
RR2: R2 [ 030F ]
     R3 [ 0005 ]              <<20>> 170A [ A023 ]
RR4: R4 [ 2000 ]              <<20>> 170C [ 0B0E ]
     R5 [ 170C ]              <<20>> 170E [ 10D3 ]

**After Execution**
RR2: R2 [ 0B0E ]
     R3 [ 0005 ]
RR4: R4 [ 2000 ]
     R5 [ 170C ]

**Example of I/O using IR mode:**
OUTB @R1, RL0

**Before Execution**
R0 [ 0A23 ]    Execution sends the
R1 [ 0011 ]    data "23" to the I/O
               device addressed by "0011."

---

### 5.5.4 Direct Address (DA)
In the Direct Addressing mode, the data processed is found at the address specified in the instruction.

Depending upon the instruction, the operand specified by the Direct Address (DA) mode will be either in Standard I/O address space (Standard I/O instructions), Special I/O address space (Special I/O instructions), or in data memory space. I/O addresses are one word long; memory addresses can be either one or two words long, depending on whether the long or short format is used.

This mode is also used by Jump and Call instructions to specify the address of the next instruction to be executed. (Actually, the address serves as an immediate value that is loaded into the Program Counter.)

**Assembler language format (see also Chapter 6):**
address    either memory, I/O, or Special I/O where double angle brackets "<<" and ">>" enclose the segment number, and vertical lines "|" and "|" enclose short-form memory addresses.

**Example of DA mode:**
LDB RH2, <<15>> %23    !load RH2 with the!
                       !value in memory!
                       !segment 15,!
                       !displacement!
                       !23 (hex)!

**Before Execution**          **Data Memory**
R2 [ 167891 ]
                              <<15>> 0022 [ 0101 ]
                              <<15>> 0023 [ 06 ]
                              <<15>> 0024 [ 0304 ]

**After Execution**
R2 [ 106891 ]

---

### 5.5.5 Index (X)
In the Index Addressing mode, the instruction processes data located at an indexed address in memory. The indexed address is computed by adding the "index" contained in a word register, to an address specified in the instruction.

The offset of the operand address is computed by adding the 16-bit index value to the 8 or 16-bit offset portion of the address in the instruction. The segment number of the operand address comes directly from the instruction. (Any overflow is ignored—it neither sets the Overflow flag nor increments the segment number.) Indexed addressing allows random access to tables or other complex data structures where the address of the base of the table is known, but the particular element index must be computed by the program.

Any word register can be used as the index register except R0. The address in the instruction can be one or two words, depending on whether a long or short offset is used in the address.

Operands specified by X mode are always in the data memory address space.

**Assembler language format:**
address(Rn)

**Example of X mode:**
LD R4, <<5>> %231A(R3)    !load into R4 the!
                          !contents of the!
                          !memory location!
                          !whose address is!
                          !segment 5,!
                          !displacement!
                          !231A + the!
                          !value in R3!

**Before Execution**          **Data Memory**
R3 [ 01FE ]
R4 [ 203A ]                   <<5>> 2516 [ F3C2 ]
                              <<5>> 2518 [ 3D0E ]
                              <<5>> 251A [ 7ADA ]

**Address Calculation**
<<5>> 231A
+      01FE
<<5>> 2518

**After Execution**
R3 [ 01FE ]
R4 [ 3D0E ]

---

### 5.5.6 Relative Address (RA)
In the Relative Addressing mode, the data processed is found at an address relative to the current instruction. The instruction specifies a two's complement displacement which is added to the offset of the Program Counter to form the target address. The Program Counter setting used is the address of the instruction following the currently executing instruction. (The assembler will take this into account in calculating the constant that is assembled into the instruction.)

An operand specified by RA mode is always in the program memory address space.

As with the Direct Addressing mode, the Relative Addressing mode is also used by certain program control instructions to specify the address of the next instruction to be executed. For JR, the result of the addition of the Program Counter offset value and the displacement is loaded into the Program Counter; for DJNZ or CALR instructions, the displacement is then subtracted from the PC offset. Relative addressing allows short references forward or backward from the current Program Counter value and is used only for such instructions as Jumps and Calls and special loads (LDR). Note that because the segment number is unchanged relative addresses are located in the same segment as the instruction.

**Assembler language format (see also Chapter 6):**
address

**Example of RA mode:**
LDR R2, $+6    !load into R2 the con-!
               !tents of the memory!
               !location whose!
               !address is the!
               !current program!
               !counter + 6!

Because the program counter will be advanced to point to the next instruction when the address calculation is performed, the constant that occurs in the instruction will actually be +2.

**Before Execution**          **Program Memory**
R2 [ IA0F0 I ]
PC [ <<13>> 0202 ]            <<13>> 0202 [ 3102 ] }
                              <<13>> 0204 [ 0002 ] } Instruction
                              <<13>> 0206 [ E801 ]
                              <<13>> 0208 [ FFFE ]

**Address Calculation**
<<13>> 0206
+          2
<<13>> 0208

**After Execution**
R2 [ FFFE ]
PC [ <<13>> 0206 ]

---

### 5.5.7 Base Address (BA)
The Base Addressing mode is similar to Index mode in that a base and displacement are combined to produce the effective address. In Base Addressing, a register pair contains the 23-bit segmented base address and the displacement is expressed as a 16-bit value in the instruction. The displacement is added to the offset of the base address, and the resulting address points to the data to be processed. (The segment number is not changed.) This addressing mode may be used only with the Load instructions. Base Addressing mode, as a complement to Index mode, allows random access to records or other data structures where the displacement of an element within the structure is known, but the base of the particular structure must be computed by the program.

Any double-word register can be used for the base address except RR0. The Base Address mode allows access to locations whose segment numbers are not known at assembly time.

An operand specified by BA mode will be in stack memory space if the base register is the stack pointer (RR14) and in data memory space otherwise.

If the segment number is known when the program is assembled (or loaded, for example, if the loader can resolve symbolic segment numbers), the Index Addressing mode may be used to simulate the Based Addressing mode. For example, if R2 is known to hold segment number 15, then the operand specified using the based address RR2 (#%93) can also be referenced by the indexed address <<15>> %93(R3). The advantage of this simulation is that Index mode is supported for most operations, whereas based is restricted to LOAD and LOAD ADDRESS. Thus, using Indexed addressing is faster and leads to compact code.

**Assembler language format (see also Chapter 6):**
RRn(#disp)    Add the immediate value to the contents of RRn; the result is the address of the operand.

**Example of BA mode:**
LDL RR4(#%18), RR2    !load the long word!
                      !in RR2 into the!
                      !memory location!
                      !whose address is!
                      !the value of RR4!
                      !+ hex 18!

**Before Execution**          **Data Memory**
RR2: R2 [ OAOO ]
     R3 [ 1500 ]              <<31>> 20C0 [ OABE ]
RR4: R4 [ IFOO ]              <<31>> 20C2 [ F50D ]
     R5 [ 20AA ]              <<31>> 20C4 [ BADE ]
                              <<31>> 20C6 [ BOD1 ]

**Address Calculation**
<<31>> 20AA
+          18
<<31>> 20C2

**After Execution**           **Data Memory**
RR2: R2 [ OAOO ]
     R3 [ 1500 ]              <<31>> 20C0 [ OABE ]
RR4: R4 [ IFOO ]              <<31>> 20C2 [ OAOO ]
     R5 [ 20AA ]              <<31>> 20C4 [ 1500 ]
                              <<31>> 20C6 [ BOD1 ]

---

### 5.5.8 Base Index (BX)
The Base Index addressing mode is an extension of the Base Addressing mode and may be used only with the LOAD and LOAD ADDRESS instructions. In this case, both the base address and index are held in registers. The index value is added to the offset of the base address to produce the offset of the operand address. The segment number of the operand address is the same as the base address. This mode allows access to memory locations whose physical addresses are computed at runtime and are not fully known at assembly time.

Any register pair can be used for the base address except RR0. Any word register except R0 can be used for the index. Note that the Short Offset format for base addresses is illegal in registers.

An operand specified by BX mode will be in stack memory space if the base register is the stack pointer (RR14) and in data memory otherwise.

**Assembler language format (see also Chapter 6):**
RRn(Rn)

**Example of BX mode:**
LD R2, RR4(R3)    !load into R2 the value!
                  !whose address is the!
                  !contents of RR4 +!
                  !the contents of R3!

**Before Execution**          **Data Memory**
RR2: R2 [ 3535 ]
     R3 [ FFFE ]              <<13>> 14FE [ 0101 ]
RR4: R4 [ ODOO ]              <<13>> 1500 [ BODE ]
     R5 [ 1502 ]              <<13>> 1502 [ F732 ]

**Address Calculation**
<<13>> 1502
+        FFFE
<<13>> 1500

**After Execution**           **Data Memory**
RR2: R2 [ BODE ]
     R3 [ FFFE ]              <<13>> 14FE [ 0101 ]
RR4: R4 [ ODOO ]              <<13>> 1500 [ BODE ]
     R5 [ 1502 ]              <<13>> 1502 [ F732 ]

# Chapter 6
# Instruction Set

## 6.1 Introduction
This chapter describes the instruction set of the Z8000. An overview of the instruction set is presented first, in which the instructions are divided into ten functional groups. The instructions in each group are listed, followed by a summary description of the instructions. Significant characteristics shared by the instructions in the group, such as the available addressing modes, flags affected, or interruptibility, are described. Unusual instructions or features that are not typical of predecessor microprocessors are pointed out.

Following the functional summary of the instruction set, flags and condition codes are discussed in relation to the instruction set. This is followed by a section discussing interruptibility of instructions and a description of traps. The last part of this chapter consists of a detailed description of each Z8000 instruction, listed in alphabetical order.

## 6.2 Functional Summary
This section presents an overview of the Z8000 instructions. For this purpose, the instructions may be divided into ten functional groups:
* Load and Exchange
* Arithmetic
* Logical
* Program Control
* Bit Manipulation
* Rotate and Shift
* Block Transfer and String Manipulation
* Input/Output
* CPU Control
* Extended Instructions

### 6.2.1 Load and Exchange Instructions
The Load and Exchange group includes a variety of instructions that provide for movement of data between registers, memory, and the program itself (i.e., immediate data). These instructions are supported with the widest range of addressing modes, including the Base (BA) and the Base Index (BX) mode which are available here only. None of these instructions affect any of the CPU flags.

| Instruction | Operand(s) | Name of Instruction |
| :--- | :--- | :--- |
| CLR | dst | Clear |
| CLRB | | |
| EX | dst, src | Exchange |
| EXB | | |
| LD | dst, src | Load |
| LDB | | |
| LDL | | |
| LDA | dst, src | Load Address |
| LDAR | dst, src | Load Address Relative |
| LDK | dst, src | Load Constant |
| LDM | dst, src, num | Load Multiple |
| LDR | dst, src | Load Relative |
| LDRB | | |
| LDRL | | |
| POP | dst, src | Pop |
| POPL | | |
| PUSH | dst, src | Push |
| PUSHL | | |

### 6.2.2 Arithmetic Instructions
The Arithmetic group consists of instructions for performing integer arithmetic. The basic instructions use standard two's complement binary format and operations. Support is also provided for implementation of BCD arithmetic.

Most of the instructions in this group perform an operation between a register operand and a second operand designated by any of the five basic addressing modes, and load the result into the register.

| Instruction | Operand(s) | Name of Instruction |
| :--- | :--- | :--- |
| ADC | dst, src | Add with Carry |
| ADCB | | |
| ADD | dst, src | Add |
| ADDB | | |
| ADDL | | |
| CP | dst, src | Compare |
| CPB | | |
| CPL | | |
| DAB | dst | Decimal Adjust |
| DEC | dst, src | Decrement |
| DECB | | |
| DIV | dst, src | Divide |
| DIVL | | |
| EXTS | dst | Extend Sign |
| EXTSB | | |
| EXTSL | | |
| INC | dst, src | Increment |
| INCB | | |
| MULT | dst, src | Multiply |
| MULTL | | |
| NEG | dst | Negate |
| NEGB | | |
| SBC | dst, src | Subtract with Carry |
| SBCB | | |
| SUB | dst, src | Subtract |
| SUBB | | |
| SUBL | | |

### 6.2.3 Logical Instructions
The instructions in this group perform logical operations on each of the bits of the operands. The operands may be bytes or words.

| Instruction | Operand(s) | Name of Instruction |
| :--- | :--- | :--- |
| AND | dst, src | And |
| ANDB | | |
| COM | dst | Complement |
| COMB | | |
| OR | dst, src | Or |
| ORB | | |
| TEST | dst | Test |
| TESTB | | |
| TESTL | | |
| XOR | dst, src | Exclusive Or |
| XORB | | |

### 6.2.4 Program Control Instructions
This group consists of the instructions that affect the Program Counter (PC) and thereby control program flow.

| Instruction | Operand(s) | Name of Instruction |
| :--- | :--- | :--- |
| CALL | dst | Call Procedure |
| CALR | dst | Call Procedure Relative |
| DJNZ | r, dst | Decrement and Jump if Not Zero |
| DBJNZ | | |
| IRET | | Interrupt Return |
| JP | cc, dst | Jump |
| JR | cc, dst | Jump Relative |
| RET | cc | Return from Procedure |
| SC | src | System Call |

### 6.2.5 Bit Manipulation Instructions
The instructions in this group are useful for manipulating individual bits in registers or memory.

| Instruction | Operand(s) | Name of Instruction |
| :--- | :--- | :--- |
| BIT | dst, src | Bit Test |
| BITB | | |
| RES | dst, src | Reset Bit |
| RESB | | |
| SET | dst, src | Set Bit |
| SETB | | |
| TSET | dst | Test and Set |
| TSETB | | |
| TCC | cc, dst | Test Condition Code |
| TCCB | | |

### 6.2.6 Rotate and Shift Instructions
These instructions rotate or shift the contents of a register.

| Instruction | Operand(s) | Name of Instruction |
| :--- | :--- | :--- |
| RL | dst, src | Rotate Left |
| RLB | | |
| RLC | dst, src | Rotate Left through Carry |
| RLCB | | |
| RLDB | dst, src | Rotate Left Digit |
| RR | dst, src | Rotate Right |
| RRB | | |
| RRC | dst, src | Rotate Right through Carry |
| RRCB | | |
| RRDB | dst, src | Rotate Right Digit |
| SDA | dst, src | Shift Dynamic Arithmetic |
| SDAB | | |
| SDAL | | |
| SDL | dst, src | Shift Dynamic Logical |
| SDLB | | |
| SDLL | | |
| SLA | dst, src | Shift Left Arithmetic |
| SLAB | | |
| SLAL | | |
| SLL | dst, src | Shift Left Logical |
| SLLB | | |
| SLLL | | |
| SRA | dst, src | Shift Right Arithmetic |
| SRAB | | |
| SRAL | | |
| SRL | dst, src | Shift Right Logical |
| SRLB | | |
| SRLL | | |

### 6.2.7 Block Transfer and String Manipulation Instructions
This group provides string comparison, string translation and block transfer functions.

| Instruction | Operand(s) | Name of Instruction |
| :--- | :--- | :--- |
| CPD / CPDB | dst, src, r, cc | Compare and Decrement |
| CPDR / CPDRB | | Compare, Decrement and Repeat |
| CPI / CPIB | | Compare and Increment |
| CPIR / CPIRB | | Compare, Increment and Repeat |
| CPSD / CPSDB | | Compare String and Decrement |
| CPSDR / CPSDRB | | Compare String, Decrement and Repeat |
| CPSI / CPSIB | | Compare String and Increment |
| CPSIR / CPSIRB | | Compare String, Increment and Repeat |
| LOD / LODB | dst, src, r | Load and Decrement |
| LODR / LODRB | | Load, Decrement and Repeat |
| LDI / LDIB | | Load and Increment |
| LDIR / LDIRB | | Load, Increment and Repeat |
| TRDB | dst, src, r | Translate and Decrement |
| TRDRB | | Translate, Decrement and Repeat |
| TRIB | | Translate and Increment |
| TRIRB | | Translate, Increment and Repeat |
| TRTDB | src1, src2, r | Translate, Test and Decrement |
| TRTDRB | | Translate, Test, Decrement and Repeat |
| TRTIB | | Translate, Test and Increment |
| TRTIRB | | Translate, Test, Increment and Repeat |

### 6.2.8 Input/Output Instructions
This group consists of instructions for transferring a byte, word or block of data between peripheral devices and the CPU registers or memory.

| Instruction | Operand(s) | Name of Instruction |
| :--- | :--- | :--- |
| IN / INB | dst, src | Input |
| IND / INDB | dst, src, r | Input and Decrement |
| INDR / INDRB | | Input, Decrement and Repeat |
| INI / INIB | | Input and Increment |
| INIR / INIRB | | Input, Increment and Repeat |
| OTDR / OTDRB | | Output, Decrement and Repeat |
| OTIR / OTIRB | | Output, Increment and Repeat |
| OUT / OUTB | dst, src | Output |
| OUTD / OUTDB | | Output and Decrement |
| OUTI / OUTIB | | Output and Increment |
| SIN / SINB | dst, src | Special Input |
| SIND / SINDB | | Special Input and Decrement |
| SINDR / SINDRB | | Special Input, Decrement and Repeat |
| SINI / SINIB | | Special Input and Increment |
| SINIR / SINIRB | | Special Input, Increment and Repeat |
| SOTDR / SOTDRB | | Special Output, Decrement and Repeat |
| SOTIR / SOTIRB | | Special Output, Increment and Repeat |
| SOUT / SOUTB | | Special Output |
| SOUTD / SOUTDB | | Special Output and Decrement |
| SOUTI / SOUTIB | | Special Output and Increment |

### 6.2.9 CPU Control Instructions
These instructions relate to CPU control and status registers.

| Instruction | Operand(s) | Name of Instruction |
| :--- | :--- | :--- |
| COMFLG | flag | Complement Flag |
| DI | int | Disable Interrupt |
| EI | int | Enable Interrupt |
| HALT | | Halt |
| LDCTL | dst, src | Load Control Register |
| LDCTLB | | |
| LDPS | src | Load Program Status |
| MBIT | | Multi-Micro Bit Test |
| MREQ | dst | Multi-Micro Request |
| MRES | | Multi-Micro Reset |
| MSET | | Multi-Micro Set |
| NOP | | No Operation |
| RESFLG | flag | Reset Flag |
| SETFLG | flag | Set Flag |

### 6.2.10 Extended Instructions
Special opcodes dedicated for the implementation of extended instructions using EPUs.

---

## 6.3 Processor Flags
The processor flags are a part of the program status. They provide a link between sequentially executed instructions.

*   **Carry (C):** Generally indicates a carry out of or a borrow into the high-order bit position.
*   **Zero (Z):** Set when the result is zero.
*   **Sign (S):** Set when the most significant bit of a result register contains a one.
*   **Parity/Overflow (P/V):** Indicates arithmetic overflow for arithmetic instructions (V), or even parity for logical instructions on byte operands (P).
*   **Decimal-Adjust (D):** Used for BCD arithmetic to record if an add or subtract was executed.
*   **Half-Carry (H):** Used for BCD arithmetic to indicate a carry or borrow out of bit 3.

---

## 6.4 Condition Codes
The condition code forms a part of all conditional instructions.

| Code | Meaning | Flag Setting | Binary |
| :--- | :--- | :--- | :--- |
| F | Always false | | 0000 |
| (blank) | Always true | | 1000 |
| Z | Zero | Z = 1 | 0110 |
| NZ | Not zero | Z = 0 | 1110 |
| C | Carry | C = 1 | 0111 |
| NC | No carry | C = 0 | 1111 |
| PL | Plus | S = 0 | 1101 |
| MI | Minus | S = 1 | 0101 |
| NE | Not equal | Z = 0 | 1110 |
| EQ | Equal | Z = 1 | 0110 |
| OV | Overflow | V = 1 | 0100 |
| NOV | No overflow | V = 0 | 1100 |
| PE | Parity even | P = 1 | 0100 |
| PO | Parity odd | P = 0 | 1100 |
| GE | Greater than or equal | (S XOR V) = 0 | 1001 |
| LT | Less than | (S XOR V) = 1 | 0001 |
| GT | Greater than | (Z OR (S XOR V)) = 0 | 1010 |
| LE | Less than or equal | (Z OR (S XOR V)) = 1 | 0010 |
| UGE | Unsigned greater or equal | C = 0 | 1111 |
| ULT | Unsigned less than | C = 1 | 0111 |
| UGT | Unsigned greater than | ((C = 0) AND (Z = 0)) | 1011 |
| ULE | Unsigned less than or equal | (C OR Z) = 1 | 0011 |

---

## 6.5 Instruction Interrupts and Traps
The Z8000 CPUs implement four kinds of traps:
* Extended Instruction
* Privileged Instruction
* Addressing Violation (Segment Trap in 28001)
* System Call

---

## 6.6 Notation and Binary Encoding
The following notation is used for register operands:
* **Rd, Rs:** a word register (R0-R15)
* **Rbd, Rbs:** a byte register (RH0-RL7)
* **RRd, RRs:** a double-word register (RR0-RR14)
* **RQd:** a quad-word register (RQ0-RQ12)

**Binary Encoding for Register Fields:**
| Register | Binary | Register | Binary |
| :--- | :--- | :--- | :--- |
| R0 / RH0 / RR0 / RQ0 | 0000 | R8 / RL0 / RR8 / RQ8 | 1000 |
| R1 / RH1 | 0001 | R9 / RL1 | 1001 |
| R2 / RH2 / RR2 | 0010 | R10 / RL2 / RR10 | 1010 |
| R3 / RH3 | 0011 | R11 / RL3 | 1011 |
| R4 / RH4 / RR4 / RQ4 | 0100 | R12 / RL4 / RR12 / RQ12 | 1100 |
| R5 / RH5 | 0101 | R13 / RL5 | 1101 |
| R6 / RH6 / RR6 | 0110 | R14 / RL6 / RR14 | 1110 |
| R7 / RH7 | 0111 | R15 / RL7 | 1111 |


## 6.7 Z8000 Instruction Descriptions and Formats

### ADC / ADCB
**Add With Carry**

**ADC dst, src**
**ADCB**

**dst: R**
**src: R**

**Operation:**
dst <- dst + src + C

The source operand, along with the setting of the carry flag, is added to the destination operand and the sum is stored in the destination. The contents of the source are not affected. Two's complement addition is performed. In multiple precision arithmetic, this instruction permits the carry from the addition of low-order operands to be carried into the addition of high-order operands.

**Flags:**
*   **C:** Set if there is a carry from the most significant bit of the result; cleared otherwise.
*   **Z:** Set if the result is zero; cleared otherwise.
*   **S:** Set if the result is negative; cleared otherwise.
*   **V:** Set if arithmetic overflow occurs, that is, if both operands were of the same sign and the result is of the opposite sign; cleared otherwise.
*   **D:** ADC-unaffected; ADCB-cleared.
*   **H:** ADC-unaffected; ADCB-set if there is a carry from the most significant bit of the low-order four bits of the result; cleared otherwise.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format (Nonsegmented) | Cycles | Format (Segmented) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | ADC Rd, Rs | 10001001 Rs Rd | 5 | 10001001 Rs Rd | 5 |
| R | ADCB Rbd, Rbs | 10001000 Rbs Rbd | 5 | 10001000 Rbs Rbd | 5 |

**Example:**
Long addition can be done with the following instruction sequence, assuming R0, R1 contain one operand and R2, R3 contain the other operand:
```assembly
ADD  R1, R3    !add low-order words!
ADC  R0, R2    !add carry and high-order words!
```
If R0 contains %0000, R1 contains %FFFF, R2 contains %4320 and R3 contains %0001, then the above two instructions leave the value %4321 in R0 and %0000 in R1.

---

### ADD / ADDB / ADDL
**Add**

**ADD dst, src**
**ADDB**
**ADDL**

**dst: R**
**src: R, IM, IR, DA, X**

**Operation:**
dst <- dst + src

The source operand is added to the destination operand and the sum is stored in the destination. The contents of the source are not affected. Two's complement addition is performed.

**Flags:**
*   **C:** Set if there is a carry from the most significant bit of the result; cleared otherwise.
*   **Z:** Set if the result is zero; cleared otherwise.
*   **S:** Set if the result is negative; cleared otherwise.
*   **V:** Set if arithmetic overflow occurs; cleared otherwise.
*   **D:** ADD, ADDL-unaffected; ADDB-cleared.
*   **H:** ADD, ADDL-unaffected; ADDB-set if there is a carry from bit 3; cleared otherwise.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | ADD Rd, Rs | 10000001 Rs Rd | 4 | 10000001 Rs Rd | 4 |
| R | ADDB Rbd, Rbs | 10000000 Rbs Rbd | 4 | 10000000 Rbs Rbd | 4 |
| R | ADDL RRd, RRs | 10101101 RRs RRd | 8 | 10101101 RRs RRd | 8 |
| IM | ADD Rd, #data | 00100001 0000 Rd | 7 | 00100001 0000 Rd | 7 |
| IR | ADD Rd, @Rs | 00000001 Rs 0000 | 7 | 10000001 RRs 0000 | 7 |
| DA | ADD Rd, addr | 10110000 1w 0000 Rd | 9 | 01100000 1w 0000 Rd | 10/12 |
| X | ADD Rd, addr(Rs) | 10110000 1w Rs Rd | 10 | 01100000 1w Rs Rd | 10/13 |

**Example:**
```assembly
ADD R2, AUGEND    !augend A located at %1254!
```
Before execution: R2 contains %0001, memory %1254 contains %0644.
After execution: R2 contains %0645.

---

### AND / ANDB
**Logical AND**

**AND dst, src**
**ANDB**

**dst: R**
**src: R, IM, IR, DA, X**

**Operation:**
dst <- dst AND src

A logical AND operation is performed between the corresponding bits of the source and destination operands, and the result is stored in the destination. A one bit is stored wherever the corresponding bits in the two operands are both ones; otherwise a zero bit is stored. The source contents are not affected.

**Flags:**
*   **C:** Unaffected.
*   **Z:** Set if the result is zero; cleared otherwise.
*   **S:** Set if the most significant bit of the result is set; cleared otherwise.
*   **P:** AND-unaffected; ANDB-set if parity of the result is even; cleared otherwise.
*   **D:** Unaffected.
*   **H:** Unaffected.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | AND Rd, Rs | 10000111 Rs Rd | 4 | 10000111 Rs Rd | 4 |
| IM | AND Rd, #data | 00100011 0000 Rd | 7 | 00100011 0000 Rd | 7 |
| IR | AND Rd, @Rs | 00000111 Rs 0000 | 7 | 10000111 RRs 0000 | 7 |
| DA | AND Rd, addr | 10110011 1w 0000 Rd | 9 | 01100011 1w 0000 Rd | 10/12 |
| X | AND Rd, addr(Rs) | 10110011 1w Rs Rd | 10 | 01100011 1w Rs Rd | 10/13 |

**Example:**
```assembly
ANDB RL3, #%CE
```
Before execution: RL3 contains %E7 (11100111), Carry=0, Zero=0, Sign=0, P/V=0.
After execution: RL3 contains %C6 (11000110), Carry=0, Zero=0, Sign=1, P/V=1.

### BIT / BITB
**Bit Test**

**BIT dst, src**
**BITB**

**dst: R, IR, DA, X**
**src: IM**
**or**
**dst: R**
**src: R**

**Operation:**
Z <- NOT dst (src)

The specified bit within the destination operand is tested, and the Z flag is set to one if the specified bit is zero; otherwise the Z flag is cleared to zero. The contents of the destination are not affected. The bit number (the source) can be specified statically as an immediate value, or dynamically as a word register whose contents are the bit number. In the dynamic case, the destination operand must be a register, and the source operand must be R0 through R7 for BITB, or R0 through R15 for BIT. The bit number is a value from 0 to 7 for BITB, or 0 to 15 for BIT, with 0 indicating the least significant bit. Note that only the lower four bits of the source operand are used to specify the bit number for BIT, while only the lower three bits of the source operand are used for BITB.

**Flags:**
*   **C:** Unaffected.
*   **Z:** Set if specified bit is zero; cleared otherwise.
*   **S:** Unaffected.
*   **V:** Unaffected.
*   **D:** Unaffected.
*   **H:** Unaffected.

**Instruction Formats and Execution Times (Bit Test Static):**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | BIT Rd, #b | 10001111 0b Rd | 4 | 10001111 0b Rd | 4 |
| IR | BIT @Rd, #b | 10011001 0b Rd | 8 | 10011001 0b RRd | 8 |
| DA | BIT address, #b | 10111001 1w 0000 b | 10 | 01111001 1w 0000 b | 11/13 |
| X | BIT addr(Rd), #b | 10111001 1w Rd b | 11 | 01111001 1w Rd b | 11/14 |

**Instruction Formats and Execution Times (Bit Test Dynamic):**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | BIT Rd, Rs | 10011001 1w 0000 Rs | 10 | 10011001 1w 0000 Rs | 10 |

**Example:**
If register RH2 contains %B2 (10110010), the instruction
```assembly
BITB RH2, #0
```
will leave the Z flag set to 1.

---

### CALL
**Call Procedure**

**CALL dst**

**dst: IR, DA, X**

**Operation:**
**Nonsegmented:**
SP <- SP - 2
@SP <- PC
PC <- dst

**Segmented:**
SP <- SP - 4
@SP <- PC
PC <- dst

The current contents of the program counter (PC) are pushed onto the top of the processor stack. The stack pointer used is R15 in nonsegmented mode, or RR14 in segmented mode. (The program counter value used is the address of the first instruction following the CALL instruction.) The specified destination address is then loaded into the PC and points to the first instruction of the called procedure. At the end of the procedure a RET instruction can be used to return to original program. RET pops the top of the processor stack back into the PC.

**Flags:**
No flags affected.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | CALL @Rd | 10011111 Rd 0000 | 10 | 10011111 RRd 0000 | 15 |
| DA | CALL address | 10110111 1100 0000 | 12 | 01101111 1100 0000 | 18/20 |
| X | CALL addr(Rd) | 10110111 11 Rd 0000 | 13 | 01101111 11 Rd 0000 | 18/21 |

**Example:**
In nonsegmented mode, if the contents of the program counter are %1000 and the contents of the stack pointer (R15) are %3002, the instruction
```assembly
CALL %2520
```
causes the stack pointer to be decremented to %3000, the value %1004 (the address following the CALL instruction) to be loaded into the word at location %3000, and the program counter to be loaded with the value %2520.

---

### CALR
**Call Procedure Relative**

**CALR dst**

**dst: RA**

**Operation:**
**Nonsegmented:**
SP <- SP - 2
@SP <- PC
PC <- PC + (2 x displacement)

**Segmented:**
SP <- SP - 4
@SP <- PC
PC <- PC + (2 x displacement)

The current contents of the program counter (PC) are pushed onto the top of the processor stack. The stack pointer used is R15 in nonsegmented mode, or RR14 in segmented mode. The destination address is the sum of twice the displacement in the instruction and the current value of the PC. The displacement is a 12-bit signed value in the range -2048 to +2047. Thus, the destination address must be in the range -4094 to +4096 bytes from the start of the CALR instruction.

**Flags:**
No flags affected.

| Addressing Mode | Assembler Syntax | Format | Cycles (Nonseg) | Cycles (Seg) |
| :--- | :--- | :--- | :--- | :--- |
| RA | CALR address | 1101 displacement | 10 | 15 |

---

### CLR / CLRB
**Clear**

**CLR dst**
**CLRB**

**dst: R, IR, DA, X**

**Operation:**
dst <- 0

The destination is cleared to zero.

**Flags:**
No flags affected.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | CLR Rd | 11010011 0w Rd 1000 | 7 | 11010011 0w Rd 1000 | 7 |
| IR | CLR @Rd | 0000110w Rd 1000 | 8 | 1000110w RRd 1000 | 8 |
| DA | CLR address | 10110011 0w 0000 1000 | 11 | 01100110 w 0000 1000 | 12/14 |
| X | CLR addr(Rd) | 10110011 0w Rd 1000 | 12 | 01100110 w Rd 1000 | 12/15 |

---

### COM / COMB
**Complement**

**COM dst**
**COMB**

**dst: R, IR, DA, X**

**Operation:**
dst <- NOT dst

The contents of the destination are complemented (one's complement).

**Flags:**
*   **C:** Unaffected.
*   **Z:** Set if result is zero.
*   **S:** Set if result is negative.
*   **P:** COMB-set if parity even.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | COM Rd | 10001101 0w Rd 0000 | 7 | 10001101 0w Rd 0000 | 7 |
| IR | COM @Rd | 0000110w Rd 0000 | 12 | 1000110w RRd 0000 | 12 |

---

### COMFLG
**Complement Flag**

**COMFLG flag**

**flag: C, Z, S, P, V**

**Operation:**
FLAGS (4:7) <- FLAGS (4:7) XOR instruction (4:7)

Any combination of the C, Z, S, P or V flags is complemented. The flags to be complemented are encoded in a field in the instruction. If the bit in the field is one, the corresponding flag is complemented. Note that the P and V flags are represented by the same bit.

**Flags:**
*   **C, Z, S, P/V:** Complemented if specified; unaffected otherwise.

| Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- |
| COMFLG flags | 10001101 01 flags 1101 | 7 |

### CP / CPB / CPL
**Compare**

**CP dst, src**
**CPB**
**CPL**

**dst: R**
**src: R, IM, IR, DA, X**
**or**
**dst: IR, DA, X**
**src: IM**

**Operation:**
dst - src

The source operand is compared to (subtracted from) the destination operand, and the appropriate flags set accordingly, which may then be used for arithmetic and logical conditional jumps. Both operands are unaffected, with the only action being the setting of the flags. Subtraction is performed by adding the two's complement of the source operand to the destination operand. There are two variants of this instruction: Compare Register compares the contents of a register against an operand specified by any of the five basic addressing modes; Compare Immediate performs a comparison between an operand in memory and an immediate value.

**Flags:**
*   **C:** Cleared if there is a carry from the most significant bit of the result; set otherwise, indicating a "borrow".
*   **Z:** Set if the result is zero; cleared otherwise.
*   **S:** Set if the result is negative; cleared otherwise.
*   **V:** Set if arithmetic overflow occurs, that is, if both operands were of opposite signs and the sign of the result is the same as the sign of the source; cleared otherwise.
*   **D:** Unaffected.
*   **H:** Unaffected.

**Instruction Formats and Execution Times (Compare Register):**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | CP Rd, Rs | 10001011 Rs Rd | 4 | 10001011 Rs Rd | 4 |
| R | CPB Rbd, Rbs | 10001010 Rbs Rbd | 4 | 10001010 Rbs Rbd | 4 |
| R | CPL RRd, RRs | 10101011 RRs RRd | 8 | 10101011 RRs RRd | 8 |
| IM | CP Rd, #data | 00101011 0000 Rd | 7 | 00101011 0000 Rd | 7 |
| IR | CP Rd, @Rs | 00001011 Rs 0000 | 7 | 10001011 RRs 0000 | 7 |
| DA | CP Rd, address | 10110101 1w 0000 Rd | 9 | 01100101 1w 0000 Rd | 10/12 |
| X | CP Rd, addr(Rs) | 10110101 1w Rs Rd | 10 | 01100101 1w Rs Rd | 10/13 |

**Instruction Formats and Execution Times (Compare Immediate):**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | CP @Rd, #data | 00100110 1w Rd 0001 | 11 | 00100110 1w RRd 0001 | 11 |
| DA | CP address, #data| 01100110 1w 0000 0001 | 14 | 01100110 1w 0000 0001 | 15/17 |
| X | CP addr(Rd), #data| 01100110 1w Rd 0001 | 15 | 01100110 1w Rd 0001 | 15/18 |

**Example:**
If register R5 contains %0400, the byte at location %0400 contains 2, and the source operand is the immediate value 3, the statement
```assembly
CPB @R5, #3
```
will leave the C flag set, indicating a borrow, the S flag set, and the Z and V flags cleared.

---

### CPD / CPDB
**Compare and Decrement**

**CPD dst, src, r, cc**
**CPDB**

**dst: R**
**src: IR**

**Operation:**
dst - src
AUTODECREMENT src (by 1 if byte, by 2 if word)
r <- r - 1

This instruction is used to search a string of data for an element meeting the specified condition. The contents of the location addressed by the source register are compared to (subtracted from) the destination operand, and the Z flag is set if the condition code specified by "cc" would be set by the comparison; otherwise the Z flag is cleared. Both operands are unaffected. The source register is then decremented by one if CPDB, or by two if CPD. The word register specified by "r" (used as a counter) is then decremented by one. The source, destination, and count registers must be separate and non-overlapping registers.

**Flags:**
*   **C, S, H:** Undefined.
*   **Z:** Set if the condition code generated by the comparison matches cc; cleared otherwise.
*   **V:** Set if the result of decrementing r is zero; cleared otherwise.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | CPD Rd, @Rs, r, cc | 11011101 1w Rs 1001 | 20 | 11011101 1w RRs 1001 | 20 |

**Example:**
If register RH0 contains %FF, register R1 contains %4001, the byte at location %4001 contains %00, and register R3 contains 5, the instruction
```assembly
CPDB RH0, @R1, R3, EQ
```
will leave the Z flag cleared since the condition code would not have been "equal." Register R1 will contain the value %4000 and R3 will contain 4.

---

### CPDR / CPDRB
**Compare, Decrement and Repeat**

**CPDR dst, src, r, cc**
**CPDRB**

**dst: R**
**src: IR**

**Operation:**
dst - src
AUTODECREMENT src (by 1 if byte, by 2 if word)
r <- r - 1
repeat until cc is true or r = 0

The entire operation is repeated until either the condition is met or the result of decrementing r is zero. This instruction can search a string from 1 to 65536 bytes or 32768 words long. The source, destination, and count registers must be separate and non-overlapping registers. This instruction can be interrupted after each execution of the basic operation.

**Flags:**
*   **Z:** Set if condition code generated matches cc; cleared otherwise.
*   **V:** Set if the result of decrementing r is zero; cleared otherwise.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | CPDR Rd, @Rs, r, cc | 11011101 1w Rs 1101 | 11+9n | 11011101 1w RRs 1101 | 11+9n |

---

### CPI / CPIB
**Compare and Increment**

**CPI dst, src, r, cc**
**CPIB**

**dst: R**
**src: IR**

**Operation:**
dst - src
AUTOINCREMENT src (by 1 if byte, by 2 if word)
r <- r - 1

Similar to CPD, but the source register is incremented after the comparison.

**Flags:**
*   **Z:** Set if condition matches cc.
*   **V:** Set if r becomes zero.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | CPI Rd, @Rs, r, cc | 11011101 1w Rs 1000 | 20 | 11011101 1w RRs 1000 | 20 |

---

### CPIR / CPIRB
**Compare, Increment and Repeat**

**CPIR dst, src, r, cc**
**CPIRB**

**dst: R**
**src: IR**

**Operation:**
dst - src
AUTOINCREMENT src (by 1 if byte, by 2 if word)
r <- r - 1
repeat until cc is true or r = 0

**Example:**
The following sequence of instructions (nonsegmented) can be used to search a string for an ASCII return character (%0D):
```assembly
LDA   R1, STRSTART
LD    R3, #STRLEN
LDB   RL0, #%0D
CPIRB RL0, @R1, R3, EQ
JR    Z, FOUND
```

### CPSD / CPSDB
**Compare String and Decrement**

**CPSD dst, src, r, cc**
**CPSDB**

**dst: IR**
**src: IR**

**Operation:**
dst - src
AUTODECREMENT dst and src (by 1 if byte; by 2 if word)
r <- r - 1

This instruction can be used to compare two strings of data until the specified condition is true. The contents of the location addressed by the source register are compared to (subtracted from) the contents of the location addressed by the destination register. The Z flag is set if the condition code specified by "cc" would be set by the comparison; otherwise the Z flag is cleared. Both operands are unaffected. The source and destination registers are then decremented by one if CPSDB, or by two if CPSD. The word register specified by "r" (used as a counter) is then decremented by one. The source, destination, and count registers must be separate and non-overlapping registers.

**Flags:**
*   **C:** Cleared if there is a carry from the MSB of the result; set otherwise, indicating a "borrow".
*   **Z:** Set if the condition matches cc; cleared otherwise.
*   **S:** Set if the result of the comparison is negative.
*   **V:** Set if the result of decrementing r is zero; cleared otherwise.
*   **D, H:** Unaffected.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | CPSDB @Rd, @Rs, r, cc | 11011101 1w Rs 1010 | 25 | 11011101 1w RRs 1010 | 25 |

**Example:**
If register R2 contains %2000, byte at %2000 is %FF, R3 contains %3000, byte at %3000 is %00, and R4 contains 1:
```assembly
CPSDB @R2, @R3, R4, UGE
```
will leave Z=1 (unsigned greater or equal) and V=1 (counter R4 is now 0). R2 will contain %1FFF, R3 will contain %2FFF.

---

### CPSDR / CPSDRB
**Compare String, Decrement and Repeat**

**CPSDR dst, src, r, cc**
**CPSDRB**

**dst: IR**
**src: IR**

**Operation:**
dst - src
AUTODECREMENT dst and src (by 1 if byte; by 2 if word)
r <- r - 1
repeat until cc is true or r = 0

The entire operation is repeated until either the condition is met or the result of decrementing r is zero. This instruction can compare strings from 1 to 65536 bytes or 32768 words long. The source, destination, and count registers must be separate and non-overlapping registers.

**Flags:**
*   **C:** Cleared if there is a carry; set otherwise.
*   **Z:** Set if condition matches cc.
*   **V:** Set if r becomes zero.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | CPSDRB @Rd, @Rs, r, cc | 11011101 1w Rs 1110 | 11+14n | 11011101 1w RRs 1110 | 11+14n |

---

### CPSI / CPSIB
**Compare String and Increment**

**CPSI dst, src, r, cc**
**CPSIB**

**dst: IR**
**src: IR**

**Operation:**
dst - src
AUTOINCREMENT dst and src (by 1 if byte; by 2 if word)
r <- r - 1

Similar to CPSD, but pointers are incremented.

**Flags:**
*   **Z:** Set if condition matches cc.
*   **V:** Set if r becomes zero.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | CPSIB @Rd, @Rs, r, cc | 11011101 1w Rs 1000 | 25 | 11011101 1w RRs 1000 | 25 |

---

### CPSIR / CPSIRB
**Compare String, Increment and Repeat**

**CPSIR dst, src, r, cc**
**CPSIRB**

**dst: IR**
**src: IR**

**Operation:**
dst - src
AUTOINCREMENT dst and src (by 1 if byte; by 2 if word)
r <- r - 1
repeat until cc is true or r = 0

---

### DAB
**Decimal Adjust**

**DAB dst**

**dst: R**

**Operation:**
dst <- DA dst

The destination byte is adjusted to form two 4-bit BCD digits following a binary addition or subtraction operation on two BCD encoded bytes.

**BCD Adjustment Table:**

| Instruction | Carry Before DAB | Bits 4-7 Value (Hex) | H Flag Before DAB | Bits 0-3 Value (Hex) | Number Added To Byte | Carry After DAB |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ADDB / ADCB** | 0 | 0-9 | 0 | 0-9 | 00 | 0 |
| | 0 | 0-8 | 0 | A-F | 06 | 0 |
| | 0 | 0-9 | 1 | 0-3 | 06 | 0 |
| | 0 | A-F | 0 | 0-9 | 60 | 1 |
| | 0 | 9-F | 0 | A-F | 66 | 1 |
| | 0 | A-F | 1 | 0-3 | 66 | 1 |
| | 1 | 0-2 | 0 | 0-9 | 60 | 1 |
| | 1 | 0-2 | 0 | A-F | 66 | 1 |
| **SUBB / SBCB** | 0 | 0-9 | 0 | 0-9 | 00 | 0 |
| | 0 | 0-8 | 1 | 6-F | FA | 0 |
| | 1 | 7-F | 0 | 0-9 | A0 | 1 |
| | 1 | 6-F | 1 | 6-F | 9A | 1 |

**Flags:**
*   **C:** Set or cleared according to the table above.
*   **Z:** Set if result is zero.
*   **S:** Set if MSB of result is set.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| R | DAB Rbd | 11000001 Rbd 0000 | 5 |

---

### DEC / DECB
**Decrement**

**DEC dst, src**
**DECB**

**dst: R, IR, DA, X**
**src: IM**

**Operation:**
dst <- dst - src (where src = 1 to 16)

The source operand (a value from 1 to 16) is subtracted from the destination operand and the result is stored in the destination. The source operand may be omitted and defaults to 1. The value of the source field in the instruction is one less than the actual value (0 to 15 corresponds to 1 to 16).

**Flags:**
*   **C:** Unaffected.
*   **Z:** Set if result is zero.
*   **S:** Set if result is negative.
*   **V:** Set if arithmetic overflow occurs.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | DEC Rd, #n | 10001011 n-1 Rd | 4 | 10001011 n-1 Rd | 4 |
| IR | DEC @Rd, #n | 1001011w Rd n-1 | 11 | 1101011w RRd n-1 | 11 |
| DA | DEC address, #n | 10111010 1w 0000 n-1| 13 | 01110101 1w 0000 n-1 | 14/16 |
| X | DEC addr(Rd), #n | 10111010 1w Rd n-1 | 14 | 01110101 1w Rd n-1 | 14/17 |

**Example:**
If register R10 contains %002A, the statement
```assembly
DEC R10
```
will leave the value %0029 in R10.

### DI
**Disable Interrupt**
**Privileged Instruction**

**DI int**

**int: VI, NVI**

**Operation:**
If instruction (0) = 0 then NVI <- 0
If instruction (1) = 0 then VI <- 0

Any combination of the Vectored Interrupt (VI) or Non-Vectored Interrupt (NVI) control bits in the Flags and Control Word (FCW) are cleared to zero if the corresponding bit in the instruction is zero, thus disabling the appropriate type of interrupt. If the corresponding bit in the instruction is one, the control bit will not be affected. All other bits in the FCW are not affected. There may be one or two operands in the assembly language statement, in either order.

**Flags:**
No flags affected.

**Instruction Formats and Execution Times:**

| Assembler Syntax | Format (Nonsegmented) | Cycles | Format (Segmented) | Cycles |
| :--- | :--- | :--- | :--- | :--- |
| DI int | 10111110 01000000 | 7 | 10111110 01000000 | 7 |

**Example:**
If the NVI and VI control bits are set (1) in the FCW, the instruction:
```assembly
DI VI
```
will leave the NVI control bit in the FCW set (1) and will leave the VI control bit in the FCW cleared (0).

---

### DIV / DIVL
**Divide**

**DIV dst, src**
**DIVL**

**dst: R**
**src: R, IM, IR, DA, X**

**Operation:**
**Word: (dst is register pair, src is word):**
dst (0:31) is divided by src (0:15)
(dst (0:31) = quotient x src (0:15) + remainder)
dst (0:15) <- quotient
dst (16:31) <- remainder

**Long: (dst register quadruple, src is long word or register pair):**
dst (0:63) is divided by src (0:31)
(dst (0:63) = quotient x src (0:31) + remainder)
dst (0:31) <- quotient
dst (32:63) <- remainder

The destination operand (dividend) is divided by the source operand (divisor), the quotient is stored in the low-order half of the destination and the remainder is stored in the high-order half of the destination. Both operands are treated as signed, two's complement integers and division is performed so that the remainder is of the same sign as the dividend. For DIV, the destination is a register pair; for DIVL, the destination is a register quadruple.

There are four possible outcomes of the Divide instruction:
**CASE 1:** If the quotient is within range (-2^15 to 2^15 - 1 for DIV), then quotient and remainder are stored, V and C flags are cleared.
**CASE 2:** If the divisor is zero, the destination remains unchanged, V and Z flags are set, C and S flags are cleared.
**CASE 3:** If the quotient is outside range (-2^16 to 2^16 - 1 for DIV), destination is undefined, V flag is set, C and Z flags are cleared.
**CASE 4:** If the quotient is inside Case 3 range but outside Case 1, all but the sign bit of the quotient and all of the remainder are left in the destination, V and C are set.

**Flags:**
*   **C:** Set if V is set and the quotient lies in Case 4 range; cleared otherwise.
*   **Z:** Set if the quotient or divisor is zero; cleared otherwise.
*   **S:** Set if the quotient is negative; cleared otherwise (Undefined if V set and C clear).
*   **V:** Set if divisor is zero or if quotient lies outside Case 1 range; cleared otherwise.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | DIV RRd, Rs | 10110111 Rs RRd | 107 | 10110111 Rs RRd | 107 |
| R | DIVL RQd, RRs | 10110101 RRs RQd | 744 | 10110101 RRs RQd | 744 |
| IM | DIV RRd, #data | 00101101 1100 RRd | 107 | 00101101 1100 RRd | 107 |
| IR | DIV RRd, @Rs | 00001101 Rs 0000 | 107 | 10110111 RRs 0000 | 107 |
| DA | DIV RRd, addr | 11011011 1100 RRd | 108 | 01011011 1100 RRd | 109/111 |
| X | DIV RRd, addr(Rs)| 11011011 11 Rs RRd | 109 | 01011011 11 Rs RRd | 109/112 |

Note: The execution time is lower (approx -94 cycles for word) for divide by zero or overflow.

**Example:**
If register RR0 (R0 and R1) contains %00000022 (decimal 34) and register R3 contains 6, the statement
```assembly
DIV RR0, R3
```
will leave the value %00040005 in RR0 (R1 contains quotient 5, R0 contains remainder 4).

---

### DJNZ / DBJNZ
**Decrement and Jump if Not Zero**

**DJNZ R, dst**
**DBJNZ**

**dst: RA**

**Operation:**
R <- R - 1
If R != 0 then PC <- PC - (2 x displacement)

The register being used as a counter is decremented. If the contents of the register are not zero after decrementing, the destination address is calculated and then loaded into the program counter (PC). The displacement is a 7-bit positive value (0 to 127). The destination address must be in the range -252 to 2 bytes from the start of the instruction.

**Flags:**
No flags affected.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| RA | DJNZ R, address | 11111 r 1w disp | 11 |

**Example:**
```assembly
      LDB   RH0, #100    !initialize counter!
      LDA   R1, SRCBUF
LOOP:
      LDB   RL0, @R1
      RESB  RL0, #7      !mask off sign!
      LDB   @R2, RL0
      INC   R1
      INC   R2
      DBJNZ RH0, LOOP    !repeat until zero!
```

---

### EI
**Enable Interrupts**
**Privileged Instruction**

**EI int**

**int: VI, NVI**

**Operation:**
If instruction (0) = 0 then NVI <- 1
If instruction (1) = 0 then VI <- 1

**Flags:**
No flags affected.

| Assembler Syntax | Format (Nonsegmented) | Cycles | Format (Segmented) | Cycles |
| :--- | :--- | :--- | :--- | :--- |
| EI int | 01111100 00000000 | 7 | 01111100 00000000 | 7 |

---

### EX / EXB
**Exchange**

**EX dst, src**
**EXB**

**dst: R**
**src: R, IR, DA, X**

**Operation:**
tmp <- src
src <- dst
dst <- tmp

The contents of the source operand are exchanged with the contents of the destination operand.

**Flags:**
No flags affected.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | EX Rd, Rs | 10001101 Rs Rd | 6 | 11011101 0w Rs Rd | 6 |
| IR | EX Rd, @Rs | 0000110w Rs 0000 | 12 | 1000110w RRd 0000 | 12 |
| DA | EX Rd, address | 10111011 0w 0000 Rd | 15 | 01110110 1w 0000 Rd | 16/18 |
| X | EX Rd, addr(Rs) | 10111011 0w Rs Rd | 16 | 01110110 1w Rs Rd | 16/19 |

### EXTS / EXTSB / EXTSL
**Extend Sign**

**EXTSB dst**
**EXTS**
**EXTSL**

**dst: R**

**Operation:**
**Byte:** if dst (7) = 0 then dst (8:15) <- 000...000 else dst (8:15) <- 111...111
**Word:** if dst (15) = 0 then dst (16:31) <- 000...000 else dst (16:31) <- 111...111
**Long:** if dst (31) = 0 then dst (32:63) <- 000...000 else dst (32:63) <- 111...111

The sign bit of the low-order half of the destination operand is copied into all bit positions of the high-order half of the destination. For EXTSB, the destination is a word; for EXTS, the destination is a register pair; for EXTSL, the destination is a register quadruple. This instruction is useful in multiple precision arithmetic or for conversion of small signed operands to larger signed operands (as, for example, before a divide).

**Flags:**
No flags affected.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | EXTSB Rd | 10001111 1000 Rd | 11 | 10001111 1000 Rd | 11 |
| R | EXTS RRd | 10001111 1001 RRd | 11 | 10001111 1001 RRd | 11 |
| R | EXTSL RQd | 10001111 1010 RQd | 11 | 10001111 1010 RQd | 11 |

**Example:**
If register pair RR2 (composed of word registers R2 and R3) contains %12345678, the statement
```assembly
EXTS RR2
```
will leave the value %00005678 in RR2 (because the sign bit of R3 was 0).

---

### HALT
**Halt**
**Privileged Instruction**

**HALT**

**Operation:**
The CPU operation is suspended until an interrupt or reset request is received. This instruction is used to synchronize the Z8000 with external events, preserving its state until an interrupt or reset request is honored. After an interrupt is serviced, the instruction following HALT is executed. While halted, memory refresh cycles will still occur, and BUSREQ will be honored.

**Flags:**
No flags affected.

| Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- |
| HALT | 10111110 10000000 | 8+3n | 10111110 10000000 | 8+3n |

---

### IN / INB / SIN / SINB
**Input / (Special) Input**
**Privileged Instruction**

**IN dst, src**
**INB**
**SIN dst, src**
**SINB**

**dst: R**
**src: IR, DA**

**Operation:**
dst <- src

The contents of the source operand, an Input or Special Input port, are loaded into the destination register. IN and INB are used for Standard I/O operation; SIN and SINB are used for Special I/O operation.

**Flags:**
No flags affected.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| IR | IN Rd, @Rs | 00111110 1w Rs Rd | 10 |
| DA | IN Rd, port | 00111101 1w Rd S port | 12 |

Note: For SIN, S=1; otherwise S=0.

**Example:**
If register R6 contains the I/O port address %0123 and the port %0123 contains %FF, the statement
```assembly
INB RH2, @R6
```
will leave the value %FF in register RH2.

---

### INC / INCB
**Increment**

**INC dst, src**
**INCB**

**dst: R, IR, DA, X**
**src: IM**

**Operation:**
dst <- dst + src (src = 1 to 16)

The source operand (a value from 1 to 16) is added to the destination operand and the sum is stored in the destination. Two's complement addition is performed. The source operand may be omitted from the assembly language statement and defaults to 1. The value of the source field in the instruction is one less than the actual value (0 to 15 corresponds to 1 to 16).

**Flags:**
*   **C:** Unaffected.
*   **Z:** Set if result is zero.
*   **S:** Set if result is negative.
*   **V:** Set if arithmetic overflow occurs.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | INC Rd, #n | 10001001 n-1 Rd | 4 | 10001001 n-1 Rd | 4 |
| IR | INC @Rd, #n | 1001000w Rd n-1 | 11 | 1101000w RRd n-1 | 11 |
| DA | INC address, #n | 10111010 0w 0000 n-1 | 13 | 01110100 1w 0000 n-1 | 14/16 |
| X | INC addr(Rd), #n | 10111010 0w Rd n-1 | 14 | 01110100 1w Rd n-1 | 14/17 |

---

### IND / INDB / SIND / SINDB
**Input and Decrement / (Special) Input and Decrement**
**Privileged Instruction**

**IND dst, src, r**
**INDB**
**SIND**
**SINDB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src
AUTODECREMENT dst (by 1 byte, by 2 if word)
r <- r - 1

This instruction is used for block input of strings of data. IND and INDB are used for Standard I/O operation; SIND and SINDB are used for Special I/O operation. The contents of the I/O port addressed by the source word register are loaded into the memory location addressed by the destination register. The destination register is then decremented. The word register specified by "r" (used as a counter) is then decremented by one. The address of the I/O port in the source register is unchanged.

**Flags:**
*   **V:** Set if the result of decrementing r is zero; cleared otherwise.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| IR | IND @Rd, @Rs, r | 11011101 1w Rs 1000 / r Rd S 1000 | 21 |

Note: For SIND, S=1, otherwise S=0.

**Example:**
In segmented mode, if RR4 contains %02004000, R6 contains %0228 (port), and R0 contains %0016:
```assembly
IND @RR4, @R6, R0
```
will leave port value in memory at %4000, RR4 becomes %02003FFE, R0 becomes %0015.


### INDR / INDRB / SINDR / SINDRB
**(Special) Input, Decrement and Repeat**
**Privileged Instruction**

**INDR dst, src, r**
**INDRB**
**SINDR**
**SINDRB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src
AUTODECREMENT dst (by 1 if byte, by 2 if word)
r <- r - 1
repeat until r = 0

This instruction is used for block input of strings of data. INDR and INDRB are used for Standard I/O operation; SINDR and SINDRB are used for special I/O operation. The contents of the I/O port addressed by the source word register are loaded into the memory location addressed by the destination register. I/O port addresses are 16 bits. The destination register is then decremented by one if a byte instruction, or by two if a word instruction, thus moving the pointer to the previous element of the string in memory. The word register specified by "r" (used as a counter) is then decremented by one. The address of the I/O port in the source register is unchanged. The entire operation is repeated until the result of decrementing r is zero. This instruction can input from 1 to 65536 bytes or 32768 words (the value for r must not be greater than 32768 for INDR or SINDR).

This instruction can be interrupted after each execution of the basic operation. The program counter value of the start of this instruction is saved before the interrupt request is accepted, so that the instruction can be properly resumed. Seven more cycles should be added to this instruction's execution time for each interrupt request that is accepted. The source, destination, and count registers must be separate and non-overlapping registers.

**Flags:**
*   **C, Z, S, H:** Unaffected or Undefined (see functional summary).
*   **V:** Set.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| IR | INDR @Rd, @Rs, r | 11011101 1w Rs 1101 / r Rd S 0000 | 11+10n |

Note: For SINDR, S=1, otherwise S=0.

**Example:**
If register R1 contains %202A, register R2 contains the Special I/O address %0AFC, and register R3 contains 8, the instruction
```assembly
SINDRB @R1, @R2, R3
```
will input 8 bytes from the Special I/O port 0AFC and leave them in descending order from %202A to %2023. Register R1 will contain %2022, and R3 will contain 0. R2 will not be affected. The V flag will be set.

---

### INI / INIB / SINI / SINIB
**(Special) Input and Increment**
**Privileged Instruction**

**INI dst, src, r**
**INIB**
**SINI**
**SINIB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src
AUTOINCREMENT dst (by 1 if byte, by 2 if word)
r <- r - 1

This instruction is used for block input of strings of data. INI, INIB are used for Standard I/O operation; SINI, SINIB are used for Special I/O operation. The contents of the I/O port addressed by the source word register are loaded into the memory location addressed by the destination register. I/O port addresses are 16 bits. The destination register is then incremented by one if a byte instruction, or by two if a word instruction, thus moving the pointer to the next element of the string in memory. The word register specified by "r" (used as a counter) is then decremented by one. The address of the I/O port in the source register is unchanged. The source, destination, and count registers should be separate and non-overlapping registers.

**Flags:**
*   **V:** Set if the result of decrementing r is zero; cleared otherwise.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| IR | INI @Rd, @Rs, r | 11011101 1w Rs 1000 / r Rd S 1000 | 21 |

**Example:**
In nonsegmented mode, if register R4 contains %4000, register R6 contains the I/O port address %0229, the port %0229 contains %B9, and register R0 contains %0016:
```assembly
INIB @R4, @R6, R0
```
will leave the value %B9 in location %4000, the value %4001 in R4, and the value %0015 in R0.

---

### INIR / INIRB / SINIR / SINIRB
**(Special) Input, Increment and Repeat**
**Privileged Instruction**

**INIR dst, src, r**
**INIRB**
**SINIR**
**SINIRB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src
AUTOINCREMENT dst (by 1 if byte, by 2 if word)
r <- r - 1
repeat until r = 0

This instruction is used for block input of strings of data. INIR and INIRB are used for Standard I/O operation; SINIR and SINIRB are used for Special I/O operation. The contents of the I/O port addressed by the source word register are loaded into the memory location addressed by the destination register. I/O port addresses are 16 bits. The destination register is then incremented by one if a byte instruction, or by two if a word instruction, thus moving the pointer to the next element in the string. The word register specified by "r" (used as a counter) is then decremented by one. The address of the I/O port in the source register is unchanged. The entire operation is repeated until the result of decrementing r is zero.

**Flags:**
*   **V:** Set.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| IR | INIR @Rd, @Rs, r | 11011101 1w Rs 1100 / r Rd S 0000 | 11+10n |

---

### IRET
**Interrupt Return**
**Privileged Instruction**

**IRET**

**Operation:**
**Nonsegmented:**
SP <- SP + 2 (Pop "identifier")
PS <- @SP
SP <- SP + 4

**Segmented:**
SP <- SP + 2 (Pop "identifier")
PS <- @SP
SP <- SP + 6

This instruction is used to return to a previously executed procedure at the end of a procedure entered by an interrupt or trap (including a System Call instruction). First, the "identifier" word associated with the interrupt or trap is popped from the system stack and discarded. Then the contents of the location addressed by the system stack pointer are popped into the program status (PS), loading the Flags and Control Word (FCW) and the program counter (PC). The new value of the FCW is not effective until the next instruction, so that the status pins will not be affected by the new control bits until after the IRET instruction execution is completed. The system stack pointer (R15 if nonsegmented, or RR14 if segmented) is used to access memory. When using a 28001 or 28003, the operation of IRET in nonsegmented mode is undefined. A 28001/3 must be in segmented mode when an IRET instruction is performed.

**Flags:**
Loaded from system stack.

| Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- |
| IRET | 01111011 10000000 | 13 | 01111011 10000000 | 16 |

---

### JP
**Jump**

**JP cc, dst**

**dst: IR, DA, X**

**Operation:**
If cc is satisfied, then PC <- dst

A conditional jump transfers program control to the destination address if the condition specified by "cc" is satisfied by the flags in the FCW. If the condition is satisfied, the program counter (PC) is loaded with the designated address; otherwise, the instruction following the JP instruction is executed.

**Flags:**
No flags affected.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles (T/NT) | Format (Seg SS/SL) | Cycles (T/NT) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | JP cc, @Rd | 10011110 cc Rd 0000 | 10/7 | 10011110 cc RRd 0000 | 15/7 |
| DA | JP cc, address | 10110111 10 cc 0000 | 7/7 | 01101111 10 cc 0000 | 8/8 (SS), 10/10 (SL)|
| X | JP cc, addr(Rd)| 10110111 10 cc Rd | 8/8 | 01101111 10 cc Rd | 8/8 (SS), 11/11 (SL)|

Note: T/NT = Jump Taken / Jump Not Taken cycles.

**Example:**
If the carry flag is set, the statement
```assembly
JP C, %1520
```
replaces the contents of the program counter with %1520, thus transferring control to that location.

### JR
**Jump Relative**

**JR cc, dst**

**dst: RA**

**Operation:**
if cc is satisfied then PC <- PC + (2 x displacement)

A conditional jump transfers program control to the destination address if the condition specified by "cc" is satisfied by the flags in the FCW. If the condition is satisfied, the program counter (PC) is loaded with the designated address; otherwise, the instruction following the JR instruction is executed. The destination address is calculated by doubling the displacement in the instruction, then adding this value to the updated value of the PC. The updated PC value is taken to be the address of the instruction following the JR instruction, while the displacement is an 8-bit signed value in the range -128 to +127. Thus, the destination address must be in the range -254 to +256 bytes from the start of the JR instruction. In the segmented mode, the PC segment number is not affected.

The assembler automatically calculates the displacement by subtracting the PC value of the following instruction from the address given by the programmer.

**Flags:**
No flags affected.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| RA | JR cc, address | 1110 cc displacement | 6 |

**Example:**
If the result of the last arithmetic operation executed is negative, the next four instructions (which occupy a total of twelve bytes) are to be skipped. This can be accomplished with the instruction
```assembly
JR MI, $ + 14
```
If the S flag is not set, execution continues with the instruction following the JR. A byte-saving form of a jump to the label LAB is
```assembly
JR LAB
```
where LAB must be within the allowed range. The condition code is "blank" in this case, and indicates that the jump is always taken.

---

### LD / LDB / LDL
**Load**

**LD dst, src**
**LDB**
**LDL**

**dst: R**
**src: R, IR, DA, X, BA, BX**
**or**
**dst: IR, DA, X, BA, BX**
**src: R**
**or**
**dst: R, IR, DA, X**
**src: IM**

**Operation:**
dst <- src

The contents of the source are loaded into the destination. The contents of the source are not affected. There are three versions of the Load instruction: Load into a register, load into memory and load an immediate value.

**Flags:**
No flags affected.

**Instruction Formats and Execution Times (Load Register):**

| Source Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | LD Rd, Rs | 11011000 0w Rs Rd | 3 | 11011000 0w Rs Rd | 3 |
| R | LDB Rbd, Rbs | 11011000 0w Rs Rd | 3 | 11011000 0w Rs Rd | 3 |
| R | LDL RRd, RRs | 10010100 01 RRs RRd| 5 | 00010100 01 RRs RRd | 5 |
| IR | LD Rd, @Rs | 00001000 1w Rs Rd | 7 | 10001000 1w RRs Rd | 7 |
| IR | LDL RRd, @Rs | 00010100 11 Rs RRd | 11 | 10010100 11 RRs RRd | 11 |
| DA | LD Rd, address | 10110000 0w 0000 Rd| 9 | 01100000 0w 0000 Rd | 10/12 |
| DA | LDL RRd, address| 10110101 00 0000 RRd| 12 | 01101010 01 0000 RRd | 13/15 |
| X | LD Rd, addr(Rs) | 10110000 0w Rs Rd | 10 | 01100000 0w Rs Rd | 10/13 |
| X | LDL RRd, addr(Rs)| 10110101 00 Rs RRd | 13 | 01101010 01 Rs RRd | 13/16 |
| BA | LD Rd, Rs(#disp) | 00111000 1w Rs Rd | 14 | 00111000 1w RRs Rd | 14 |
| BA | LDL RRd, Rs(#disp)| 10011101 01 Rs RRd | 17 | 00111010 11 RRs RRd | 17 |
| BX | LD Rd, Rs(Rx) | 11111000 0w Rs Rd / 0000 Rx 0000 | 14 | 11111000 0w RRs Rd / 0000 Rx 0000 | 14 |
| BX | LDL RRd, Rs(Rx) | 10111101 01 Rs RRd / 0000 Rx 0000 | 17 | 01111010 11 RRs RRd / 0000 Rx 0000 | 17 |

Note: RRd and RRs denote register pairs for long word (LDL). Rbd and Rbs denote byte registers (LDB).

### LD / LDB / LDL (Continued)
**Load Memory (Store)**

**Instruction Formats and Execution Times (Load Memory):**

| Destination Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | LD @Rd, Rs | 00001001 1w Rd Rs | 8 | 10001001 1w RRd Rs | 8 |
| IR | LDL @Rd, RRs | 01011101 Rd RRs | 11 | 01111101 RRd RRs | 11 |
| DA | LD address, Rs | 10111011 1w 0000 Rs| 11 | 01110111 1w 0000 Rs | 12/14 |
| DA | LDL address, RRs| 10110111 01 0000 RRs| 14 | 01110111 01 0000 RRs | 15/17 |
| X | LD addr(Rd), Rs | 10111011 1w Rd Rs | 12 | 01110111 1w Rd Rs | 12/15 |
| X | LDL addr(Rd), RRs| 10110111 01 Rd RRs | 15 | 01110111 01 Rd RRs | 15/18 |
| BA | LD Rd(#disp), Rs | 00111001 1w Rd Rs | 14 | 00111001 1w RRd Rs | 14 |
| BA | LDL Rd(#disp), RRs| 00110111 11 Rd RRs | 17 | 00110111 11 RRd RRs | 17 |
| BX | LD Rd(Rx), Rs | 10111100 11 Rd Rs / 0000 Rx 0000 | 14 | 01111100 11 RRd Rs / 0000 Rx 0000 | 14 |
| BX | LDL Rd(Rx), RRs | 10111011 11 Rd RRs / 0000 Rx 0000 | 17 | 01111011 11 RRd RRs / 0000 Rx 0000 | 17 |

---

**Load Immediate Value**

**Instruction Formats and Execution Times (Load Immediate):**

| Destination Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | LD Rd, #data | 00110000 11 0000 Rd | 7 | 00110000 11 0000 Rd | 7 |
| R | LDB Rbd, #data (Note 2)| 00110000 01 0000 Rbd| 7 | 00110000 01 0000 Rbd | 7 |
| R | LDB Rbd, #data (Short)| 1100 Rbd data | 5 | 1100 Rbd data | 5 |
| R | LDL RRd, #data | 00101010 01 0000 RRd| 11 | 00101010 01 0000 RRd | 11 |
| IR | LD @Rd, #data | 00100110 11 Rd 0101 | 11 | 00100110 11 RRd 0101 | 11 |
| IR | LDB @Rd, #data | 00100110 01 Rd 0101 | 11 | 00100110 01 RRd 0101 | 11 |
| DA | LD address, #data| 01100110 11 0000 0101| 14 | 01100110 11 0000 0101| 15/17 |
| DA | LDB address, #data| 01100110 01 0000 0101| 14 | 01100110 01 0000 0101| 15/17 |
| X | LD addr(Rd), #data| 01100110 11 Rd 0101 | 15 | 01100110 11 Rd 0101 | 15/18 |
| X | LDB addr(Rd), #data| 01100110 01 Rd 0101 | 15 | 01100110 01 Rd 0101 | 15/18 |

**Note 1:** Word register in nonsegmented mode, register pair in segmented mode.
**Note 2:** Although two formats exist for "LDB R, IM", the assembler always uses the short format. In this case, the "src field" in the instruction format encoding contains the source operand.

**Example:**
Several examples of the use of the Load instruction are treated in detail in Chapter 4 under addressing modes.

---

### LDA
**Load Address**

**LDA dst, src**

**dst: R**
**src: DA, X, BA, BX**

**Operation:**
dst <- address (src)

The address of the source operand is computed and loaded into the destination. The contents of the source are not affected. The address computation follows the rules for address arithmetic. The destination is a word register in nonsegmented mode, and a register pair in segmented mode. In segmented mode, the address loaded into the destination has an undefined value in all reserved bits (bits 16-23 and bit 31). However, this address may be used by subsequent instructions in the indirect, base, or base-index addressing modes without any modification to the reserved bits.

**Flags:**
No flags affected.

**Instruction Formats and Execution Times:**

| Source Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| DA | LDA Rd, address | 10111101 10 0000 Rd | 12 | 01111101 10 0000 RRd | 13/15 |
| X | LDA Rd, addr(Rs)| 10111101 10 Rs Rd | 13 | 01111101 10 Rs RRd | 13/16 |
| BA | LDA Rd, Rs(#disp)| 00110100 00 Rs Rd | 15 | 00110100 00 RRs RRd | 15 |
| BX | LDA Rd, Rs(Rx) | 01110100 00 Rs Rd / 0000 Rx 0000 | 15 | 01110100 00 RRs RRd / 0000 Rx 0000 | 15 |

**Examples:**
```assembly
LDA R4, STRUCT    !in nonsegmented mode, register R4 is loaded!
                  !with the nonsegmented address of STRUCT!

LDA RR2, <<3>> 8(R4) !in segmented mode, if index register R4!
                     !contains %20, RR2 is loaded with the!
                     !segmented address (segment 3, offset %28)!

LDA RR2, RR4(#8)  !in segmented mode, if base register RR4!
                  !contains %01000020, RR2 is loaded with!
                  !address <<1>> %28!
```

### LDAR
**Load Address Relative**

**LDAR dst, src**

**dst: R**
**src: RA**

**Operation:**
dst <- address (src)

The address of the source operand is computed and loaded into the destination. The contents of the source are not affected. The destination is a word register in nonsegmented mode, and a register pair in segmented mode. In segmented mode, the address loaded into the destination has all reserved bits (bits 16-23 and bit 31) cleared to zero.

The relative address is calculated by adding the displacement in the instruction to the updated value of the program counter (PC) to derive the address. The updated PC value is taken to be the address of the instruction following the LDAR instruction, while the displacement is a 16-bit signed value in the range -32768 to +32767. The addition is performed following the rules of address arithmetic, with no modifications to the segment number in segmented mode. Thus in segmented mode, the source operand must be in the same segment as the LDAR instruction.

The assembler automatically calculates the displacement by subtracting the PC value of the following instruction from the address given by the programmer.

**Flags:**
No flags affected.

| Source Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RA | LDAR Rd, address | 10011010 0000 Rd | 15 | 00110100 0000 RRd | 15 |

**Examples:**
```assembly
LDAR R2, TABLE     !in nonsegmented mode, register R2 is loaded!
                   !with the address of TABLE!

LDAR RR4, TABLE    !in segmented mode, register pair RR4 is!
                   !loaded with the segmented address of TABLE,!
                   !which must be in the same segment as the program!
```

---

### LDCTL
**Load Control**
**Privileged Instruction**

**LDCTL dst, src**

**dst: CTLR**
**src: R**
**or**
**dst: R**
**src: CTLR**

**Operation:**
dst <- src

This instruction loads the contents of a general purpose register into a control register, or loads the contents of a control register into a general-purpose register. The control register may be one of the following CPU registers:

*   **FCW:** Flag and Control Word
*   **REFRESH:** Refresh Control
*   **PSAPSEG:** Program Status Area Pointer - segment number
*   **PSAPOFF:** Program Status Area Pointer - offset
*   **NSPSEG:** Normal Stack Pointer - segment number
*   **NSPOFF:** Normal Stack Pointer - offset

**Load Into Control Register**
*   **LDCTL FCW, Rs:** FCW (2:7) <- Rs (2:7), FCW (11:15) <- Rs (11:15)
*   **LDCTL REFRESH, Rs:** REFRESH (1:15) <- Rs (1:15)
*   **LDCTL NSPSEG, Rs:** NSPSEG (0:15) <- Rs (0:15) (Segmented mode only)
*   **LDCTL NSPOFF, Rs / NSP, Rs:** NSPOFF (0:15) <- Rs (0:15)
*   **LDCTL PSAPSEG, Rs:** PSAPSEG (8:14) <- Rs (8:14) (Segmented mode only)
*   **LDCTL PSAPOFF, Rs / PSAP, Rs:** PSAPOFF (8:15) <- Rs (8:15)

**Load From Control Register**
*   **LDCTL Rd, FCW:** Rd (2:7) <- FCW (2:7), Rd (11:15) <- FCW (11:15) (Z8001), Rd (11:14) <- FCW (11:14) (Z8002)
*   **LDCTL Rd, REFRESH:** Rd (0:8) <- REFRESH (0:8)
*   **LDCTL Rd, PSAPSEG:** Rd (8:14) <- PSAPSEG (8:14) (Segmented mode only)
*   **LDCTL Rd, PSAPOFF / Rd, PSAP:** Rd (8:15) <- PSAPOFF (8:15)
*   **LDCTL Rd, NSPSEG:** Rd (0:15) <- NSPSEG (0:15) (Segmented mode only)
*   **LDCTL Rd, NSPOFF / Rd, NSP:** Rd (0:15) <- NSPOFF (0:15)

**Flags:**
No flags affected, except when the destination is the Flag and Control Word (LDCTL FCW, Rs), in which case all the flags are loaded from the source register.

**Instruction Formats and Execution Times:**

| Direction | Assembler Syntax | Format (Nonseg) | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- |
| To Control | LDCTL FCW, Rs | 01111101 Rs 1000 | 01111101 Rs 1000 | 7 |
| To Control | LDCTL REFRESH, Rs| 01111101 Rs 1001 | 01111101 Rs 1001 | 7 |
| To Control | LDCTL PSAP, Rs | 01111101 Rs 1010 | 01111101 Rs 1010 | 7 |
| From Control| LDCTL Rd, FCW | 01111101 Rd 0000 | 01111101 Rd 0000 | 7 |
| From Control| LDCTL Rd, REFRESH| 01111101 Rd 0001 | 01111101 Rd 0001 | 7 |
| From Control| LDCTL Rd, PSAP | 01111101 Rd 0010 | 01111101 Rd 0010 | 7 |

---

### LDCTLB
**Load Control Byte**

**LDCTLB dst, src**

**dst: FLAGS**
**src: R**
**or**
**dst: R**
**src: FLAGS**

**Operation:**
dst <- src

This instruction is used to load the FLAGS register or to transfer its contents into a general-purpose register. Note that this is not a privileged instruction.

**Load Into FLAGS Register (LDCTLB FLAGS, Rbs):**
FLAGS (2:7) <- src (2:7)

**Load From FLAGS Register (LDCTLB Rbd, FLAGS):**
dst (2:7) <- FLAGS (2:7), dst (0:1) <- 0

**Flags:**
When the FLAGS register is the destination, all the flags are loaded from the source. When the FLAGS register is the source, none of the flags are affected.

| Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| LDCTLB FLAGS, Rbs | 10001100 Rbs 0000 | 7 | 10001100 Rbs 0000 | 7 |
| LDCTLB Rbd, FLAGS | 10001100 Rbd 0100 | 7 | 10001100 Rbd 0100 | 7 |

---

### LDD / LDDB
**Load and Decrement**

**LDD dst, src, r**
**LDDB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src
AUTODECREMENT dst and src (by 1 if byte, by 2 if word)
r <- r - 1

This instruction is used for block transfers of strings of data. The contents of the location addressed by the source register are loaded into the location addressed by the destination register. The source and destination registers are then decremented. The word register specified by "r" (used as a counter) is then decremented by one. The source, destination, and counter registers must be separate and non-overlapping registers.

**Flags:**
*   **V:** Set if the result of decrementing r is zero; cleared otherwise.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | LDD @Rd, @Rs, r | 11011101 1w Rs 1001 / 0000 r Rd 1000 | 20 | 11011101 1w RRs 1001 / 0000 r RRd 1000 | 20 |

**Example:**
In nonsegmented mode, if R1 contains %202A, R2 contains %404A, memory at %404A is %FFFF, and R3 is 5:
```assembly
LDD @R1, @R2, R3
```
will leave %FFFF at location %202A, R1 becomes %2028, R2 becomes %4048, R3 becomes 4.

---

### LDDR / LDDRB
**Load, Decrement and Repeat**

**LDDR dst, src, r**
**LDDRB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src
AUTODECREMENT dst and src (by 1 if byte, by 2 if word)
r <- r - 1
repeat until r = 0

This instruction is used for block transfers of strings of data. The entire operation is repeated until the result of decrementing r is zero. The effect of decrementing the pointers during the transfer is important if the source and destination strings overlap with the source string starting at a lower memory address. Placing the pointers at the highest address of the strings and decrementing the pointers ensures that the source string will be copied without destroying the overlapping area.

**Flags:**
*   **V:** Set.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | LDDR @Rd, @Rs, r | 11011101 1w Rs 1001 / 0000 r Rd 0000 | 11+9n | 11011101 1w RRs 1001 / 0000 r RRd 0000 | 11+9n |

### LDI / LDIB
**Load and Increment**

**LDI dst, src, r**
**LDIB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src
AUTOINCREMENT dst and src (by 1 if byte, by 2 if word)
r <- r - 1

This instruction is used for block transfers of strings of data. The contents of the location addressed by the source register are loaded into the location addressed by the destination register. The source and destination registers are then incremented. The word register specified by "r" (used as a counter) is then decremented by one. The source, destination, and counter registers must be separate and non-overlapping registers.

**Flags:**
*   **V:** Set if the result of decrementing r is zero, cleared otherwise.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | LDI @Rd, @Rs, r | 11011101 1w Rs 1001 / 0000 r Rd 1001 | 20 | 11011101 1w RRs 1001 / 0000 r RRd 1001 | 20 |

**Example:**
This instruction can be used in a "loop" of instructions which transfers a string of data from one location to another, but an intermediate operation on each data element is required. The following sequence (nonsegmented) transfers a string of 80 bytes, but tests for a special value (%0D, an ASCII return character) which terminates the loop if found.
```assembly
      LD    R3, #80      !initialize counter!
      LDA   R1, DSTBUF   !load start addresses!
      LDA   R2, SRCBUF
LOOP:
      CPB   @R2, #%0D    !check for return character!
      JR    EQ, DONE     !exit loop if found!
      LDIB  @R1, @R2, R3 !transfer next byte!
      JR    NOV, LOOP    !repeat until counter = 0!
DONE:
```

---

### LDIR / LDIRB
**Load, Increment and Repeat**

**LDIR dst, src, r**
**LDIRB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src
AUTOINCREMENT dst and src (by 1 if byte, by 2 if word)
r <- r - 1
repeat until r = 0

This instruction is used for block transfers of strings of data. The entire operation is repeated until the result of decrementing r is zero. The effect of incrementing the pointers during the transfer is important if the source and destination strings overlap with the source string starting at a higher memory address. Placing the pointers at the lowest address of the strings and incrementing the pointers ensures that the source string will be copied without destroying the overlapping area.

**Flags:**
*   **V:** Set.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | LDIR @Rd, @Rs, r | 11011101 1w Rs 1001 / 0000 r Rd 0001 | 11+9n | 11011101 1w RRs 1001 / 0000 r RRd 0001 | 11+9n |

**Example:**
The following sequence of instructions (nonsegmented) can be used to copy a buffer of 512 words (1024 bytes).
```assembly
LDA   R1, DSTBUF
LDA   R2, SRCBUF
LD    R3, #512
LDIR  @R1, @R2, R3
```

---

### LDK
**Load Constant**

**LDK dst, src**

**dst: R**
**src: IM**

**Operation:**
dst <- src (src = 0 to 15)

The source operand (a constant value specified in the src field) is loaded into the destination register. The source operand is a value from 0 to 15. It is loaded into the four low-order bits of the destination register, while the high-order 12 bits are cleared to zero.

**Flags:**
No flags affected.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | LDK Rd, #data | 11111011 Rd data | 5 | 11111011 Rd data | 5 |

---

### LDM
**Load Multiple**

**LDM dst, src, n**

**dst: R**
**src: IR, DA, X**
**or**
**dst: IR, DA, X**
**src: R**

**Operation:**
dst <- src (n words)

The contents of n source words are loaded into the destination. The contents of the source are not affected. The value of n lies between 1 and 16, inclusive. This instruction moves information between memory and registers; registers are accessed in increasing order starting with the specified register; R0 follows R15.

**Flags:**
No flags affected.

**Instruction Formats and Execution Times (Registers From Memory):**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | LDM Rd, @Rs, #n | 00101110 0 Rs 0001 / 0000 Rd 0000 n-1| 11+3n | 00101110 0 RRs 0001 / 0000 Rd 0000 n-1 | 11+3n |
| DA | LDM Rd, addr, #n | 01101110 0 0000 0001 / 0000 Rd 0000 n-1| 14+3n | 01101110 0 0000 0001 / 0000 Rd 0000 n-1 | 15/17+3n |
| X | LDM Rd, addr(Rs), #n| 01101110 0 Rs 0001 / 0000 Rd 0000 n-1| 15+3n | 01101110 0 Rs 0001 / 0000 Rd 0000 n-1 | 15/18+3n |

**Instruction Formats and Execution Times (Memory From Registers):**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | LDM @Rd, Rs, #n | 00101110 0 Rd 1001 / 0000 Rs 0010 n-1| 11+3n | 00101110 0 RRd 1001 / 0000 Rs 0010 n-1 | 11+3n |
| DA | LDM addr, Rs, #n | 01101110 0 0000 1001 / 0000 Rs 0010 n-1| 14+3n | 01101110 0 0000 1001 / 0000 Rs 0010 n-1 | 15/17+3n |
| X | LDM addr(Rd), Rs, #n| 01101110 0 Rd 1001 / 0000 Rs 0010 n-1| 15+3n | 01101110 0 Rd 1001 / 0000 Rs 0010 n-1 | 15/18+3n |

---

### LDPS
**Load Program Status**
**Privileged Instruction**

**LDPS src**

**src: IR, DA, X**

**Operation:**
PS <- src

The contents of the source operand are loaded into the Program Status (PS), loading the Flags and Control Word (FCW) and the program counter (PC). The next instruction executed is that addressed by the new contents of the PC. This instruction is used to set the Program Status of a program and is particularly useful for setting the System/Normal mode of a program to Normal mode.

**Program Status Block Format (Source Operand):**

**NONSEGMENTED (4 bytes):**
```text
LOW ADDRESS  | FCW (2 bytes)     |
HIGH ADDRESS | PC (2 bytes)      |
```

**SEGMENTED (8 bytes):**
```text
LOW ADDRESS  | FCW (2 bytes)     |
             | RESERVED (2 bytes)|
             | PC SEGMENT (2 b.) |
HIGH ADDRESS | PC OFFSET (2 b.)  |
```

**Flags:**
All flags are loaded from the source operand.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IR | LDPS @Rs | 00001111 0011 Rs 0000| 12 | 10001111 0011 RRs 0000 | 16 |
| DA | LDPS address | 10111110 01 0000 0000| 16 | 01111100 11 0000 0000 | 20/22 |
| X | LDPS addr(Rs) | 10111110 01 Rs 0000 | 17 | 01111100 11 Rs 0000 | 20/23 |

### LDR / LDRB / LDRL
**Load Relative**

**LDR dst, src**
**LDRB**
**LDRL**

**dst: R**
**src: RA**
**or**
**dst: RA**
**src: R**

**Operation:**
dst <- src

The contents of the source operand are loaded into the destination. The contents of the source are not affected. The relative address is calculated by adding the displacement in the instruction to the updated value of the program counter (PC) to derive the operand's address. In segmented mode, the segmented number of the computed address is the same as the segment number of the PC. The updated PC value is taken to be the address of the instruction following the LDR, LDRB, or LDRL instruction, while the displacement is a 16-bit signed value in the range -32768 to +32767.

Status pin information during the access to memory for the data operand will be Program Reference (1100) instead of Data Memory request (1000). The assembler automatically calculates the displacement by subtracting the PC value of the following instruction from the address given by the programmer.

**Flags:**
No flags affected.

**Instruction Formats and Execution Times (Load Relative Register):**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RA | LDR Rd, address | 10011000 0w 0000 Rd | 14 | 10011000 0w 0000 Rd | 14 |
| RA | LDRB Rbd, address| 10011000 0w 0000 Rbd| 14 | 10011000 0w 0000 Rbd | 14 |
| RA | LDRL RRd, address| 10011010 10000 RRd | 17 | 10011010 10000 RRd | 17 |

**Instruction Formats and Execution Times (Load Relative Memory):**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RA | LDR address, Rs | 10011001 0w 0000 Rs | 14 | 10011001 0w 0000 Rs | 14 |
| RA | LDRB address, Rbs| 10011001 0w 0000 Rbs | 14 | 10011001 0w 0000 Rbs | 14 |
| RA | LDRL address, RRs| 10011011 10000 RRs | 17 | 10011011 10000 RRs | 17 |

---

### MBIT
**Multi-Micro Bit Test**
**Privileged Instruction**

**MBIT**

**Operation:**
S <- 1 if MI high (inactive); 0 otherwise

This instruction is used to synchronize multiple processors' exclusive access to shared hardware resources. The multi-micro input pin (MI) is tested, and the S flag is cleared if the pin is low (active); otherwise, the S flag is set, indicating that the pin is high (inactive). After the MBIT instruction is executed, the S flag can be used to determine whether a requested resource is available or not.

**Flags:**
*   **S:** Set if MI is high; cleared otherwise.
*   **Z:** Undefined.

| Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- |
| MBIT | 01111011 00001010 | 7 | 01111011 00001010 | 7 |

---

### MREQ
**Multi-Micro Request**
**Privileged Instruction**

**MREQ dst**

**dst: R**

**Operation:**
Z <- 0
if MI low (active) then S <- 0, MO forced high (inactive)
else MO forced low (active)
     repeat dst <- dst - 1 until dst = 0
     if MI low (active) then S <- 1
     else S <- 0, MO forced high (inactive)
     Z <- 1

This instruction is used to synchronize multiple processors' exclusive access to shared hardware resources. A request for a resource is signalled through the multi-micro input and output pins (MI and MO), with the S and Z flags indicating the availability of the resource. To allow for propagation of the signal to other processors, a finite delay is accomplished by repeatedly decrementing the contents of the destination register until zero. The original value must be greater than 2.

**Resource Request State Table:**
| S flag | Z flag | MO Pin | Indicates |
| :--- | :--- | :--- | :--- |
| 0 | 0 | high | Request not signalled (resource busy) |
| 0 | 1 | high | Request not granted (contention) |
| 1 | 1 | low | Request granted (resource available) |

**Flags:**
*   **Z:** Set if request was signalled; cleared otherwise.
*   **S:** Set if request was signalled and granted; cleared otherwise.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| R | MREQ Rd | 10111110 1101 Rd | 12+7n |

Note: n = number of times destination is decremented.

---

### MRES / MSET
**Multi-Micro Reset / Multi-Micro Set**
**Privileged Instruction**

**MRES**
**MSET**

**Operation:**
**MRES:** MO is forced high (inactive).
**MSET:** MO is forced low (active).

**Flags:**
No flags affected.

| Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- |
| MRES | 01111011 10001001 | 5 |
| MSET | 01111011 10001000 | 5 |

---

### MULT / MULTL
**Multiply**

**MULT dst, src**
**MULTL**

**dst: R**
**src: R, IM, IR, DA, X**

**Operation:**
**Word:** dst (0:31) <- dst (0:15) x src (0:15)
**Long:** dst (0:63) <- dst (0:31) x src (0:31)

The low-order half of the destination operand (multiplicand) is multiplied by the source operand (multiplier) and the product is stored in the destination. Both operands are treated as signed, two's complement integers. For MULT, the destination is a register pair; for MULTL, the destination is a register quadruple. For proper execution, the dst field must be even for MULT and a multiple of 4 for MULTL.

**Flags:**
*   **C:** Set if product cannot be represented in the same precision as the multiplicand.
*   **Z:** Set if result is zero.
*   **S:** Set if result is negative.
*   **V:** Cleared.

**Execution Times (Note 2):**

| Source Mode | Word (Nonseg) | Word (Seg SS) | Word (Seg SL) | Long (All Modes) |
| :--- | :--- | :--- | :--- | :--- |
| R, IM, IR | 70 | 70 | 70 | 282 + 7*n |
| DA | 71 | 72 | 74 | 283 + 7*n |
| X | 72 | 72 | 75 | 284 + 7*n |

Note 1: n = number of bits equal to one in the absolute value of the multiplicand.
Note 2: If multiplier is zero, word execution is 18-23 cycles, long is 30-35 cycles.

**Instruction Formats:**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Format (Seg) |
| :--- | :--- | :--- | :--- |
| R | MULT RRd, Rs | 10111001 Rs RRd | 10111001 Rs RRd |
| R | MULTL RQd, RRs | 10111000 RRs RQd | 10111000 RRs RQd |
| IM | MULT RRd, #data| 00101100 1100 RRd | 00101100 1100 RRd |
| IR | MULT RRd, @Rs | 00001100 1 Rs 0000 | 10111001 RRs 0000 |

### NEG / NEGB
**Negate**

**NEG dst**
**NEGB**

**dst: R, IR, DA, X**

**Operation:**
dst <- - dst

The contents of the destination are negated, that is, replaced by its two's complement value. Note that %8000 for NEG and %80 for NEGB are replaced by themselves since in two's complement representation the negative number with greatest magnitude has no positive counterpart; for these two cases, the V flag is set.

**Flags:**
*   **C:** Cleared if the result is zero; set otherwise, which indicates a "borrow".
*   **Z:** Set if the result is zero; cleared otherwise.
*   **S:** Set if the result is negative; cleared otherwise.
*   **V:** Set if the result is %8000 for NEG, or %80 for NEGB; cleared otherwise.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | NEG Rd | 10001101 0w Rd 0010 | 7 | 10001101 0w Rd 0010 | 7 |
| IR | NEG @Rd | 0000110w Rd 0010 | 12 | 1000110w RRd 0010 | 12 |
| DA | NEG address | 10110011 0w 0000 0010| 15 | 01100110 1w 0000 0010 | 16/18 |
| X | NEG addr(Rd) | 10110011 0w Rd 0010 | 16 | 01100110 1w Rd 0010 | 16/19 |

**Example:**
If register R8 contains %051F, the statement
```assembly
NEG R8
```
will leave the value %FAEI in R8.

---

### NOP
**No Operation**

**NOP**

**Operation:**
No operation is performed.

**Flags:**
No flags affected.

| Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- |
| NOP | 10001101 00000111 | 7 |

---

### OR / ORB
**Logical OR**

**OR dst, src**
**ORB**

**dst: R**
**src: R, IM, IR, DA, X**

**Operation:**
dst <- dst OR src

A logical OR operation is performed between the source and destination operands and the result is stored in the destination.

**Flags:**
*   **Z:** Set if result is zero.
*   **S:** Set if MSB is set.
*   **P:** ORB-set if parity even.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | OR Rd, Rs | 10000101 Rs Rd | 4 | 10000101 Rs Rd | 4 |
| IM | OR Rd, #data | 00100010 0000 Rd | 7 | 00100010 0000 Rd | 7 |
| IR | OR Rd, @Rs | 00000101 Rs 0000 | 7 | 10000101 RRs 0000 | 7 |
| DA | OR Rd, address | 10110001 0w 0000 Rd | 9 | 01100010 1w 0000 Rd | 10/12 |
| X | OR Rd, addr(Rs) | 10110001 0w Rs Rd | 10 | 01100010 1w Rs Rd | 10/13 |

---

### OTDR / OTDRB / SOTDR / SOTDRB
**(Special) Output, Decrement and Repeat**
**Privileged Instruction**

**OTDR dst, src, r**
**OTDRB**
**SOTDR**
**SOTDRB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src
AUTODECREMENT src (by 1 if byte, by 2 if word)
r <- r - 1
repeat until r = 0

This instruction is used for block output of strings of data. The contents of the memory location addressed by the source register are loaded into the I/O port addressed by the destination word register. The source register is then decremented.

**Flags:**
*   **V:** Set.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| IR | OTDR @Rd, @Rs, r | 10011101 1w Rs 1101 / r Rd S 0000 | 11+10n |

Note: For SOTDR, S=1; otherwise S=0.

---

### OTIR / OTIRB / SOTIR / SOTIRB
**(Special) Output, Increment and Repeat**
**Privileged Instruction**

**OTIR dst, src, r**
**OTIRB**
**SOTIR**
**SOTIRB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src
AUTOINCREMENT src (by 1 if byte, by 2 if word)
r <- r - 1
repeat until r = 0

---

### OUT / OUTB / SOUT / SOUTB
**Output / (Special) Output**
**Privileged Instruction**

**OUT dst, src**
**OUTB**
**SOUT dst, src**
**SOUTB**

**dst: IR, DA**
**src: R**

**Operation:**
dst <- src

The contents of the source register are loaded into the destination port.

**Flags:**
No flags affected.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| IR | OUT @Rd, Rs | 10011111 1w Rd Rs | 10 |
| DA | SOUT port, Rs | 10011101 1w Rs S port | 12 |

---

### OUTD / OUTDB / SOUTD / SOUTDB
**(Special) Output and Decrement**
**Privileged Instruction**

**OUTD dst, src, r**
**OUTDB**
**SOUTD**
**SOUTDB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src
AUTODECREMENT src (by 1 if byte, by 2 if word)
r <- r - 1

**Flags:**
*   **V:** Set if result of decrementing r is zero.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| IR | OUTD @Rd, @Rs, r | 10011101 1w Rs 1101 / r Rd S 1000 | 21 |

---

### OUTI / OUTIB / SOUTI / SOUTIB
**(Special) Output and Increment**
**Privileged Instruction**

**OUTI dst, src, r**
**OUTIB**
**SOUTI**
**SOUTIB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src
AUTOINCREMENT src (by 1 if byte, by 2 if word)
r <- r - 1

**Flags:**
*   **V:** Set if result of decrementing r is zero.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| IR | OUTI @Rd, @Rs, r | 10011101 1w Rs 1000 / r Rd S 1000 | 21 |

### POP / POPL
**Pop**

**POP dst, src**
**POPL**

**dst: R, IR, DA, X**
**src: IR**

**Operation:**
dst <- src
AUTOINCREMENT src (by 2 if word, by 4 if long)

The contents of the location addressed by the source register (a stack pointer) are loaded into the destination. The source register is then incremented by a value which equals the size in bytes of the destination operand, thus removing the top element of the stack by changing the stack pointer. Any register except R0 (or RR0 in segmented mode) can be used as a stack pointer. The same register cannot be used in both the source and destination addressing fields.

**Flags:**
No flags affected.

**Instruction Formats and Execution Times:**

| Destination Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | POP Rd, @Rs | 10010111 Rs Rd | 8 | 10010111 RRs RRd | 8 |
| R (Long) | POPL RRd, @Rs | 01010101 Rs RRd | 12 | 01010101 RRs RRd | 12 |
| IR | POP @Rd, @Rs | 10010111 Rd Rs | 12 | 01010111 RRs RRd | 12 |
| DA | POP address, @Rs | 10110101 11 Rs 0000 | 16 | 01101011 1 RRs 0000 | 16/18 |
| X | POP addr(Rd), @Rs| 10110101 11 Rs Rd | 16 | 01101011 1 RRs Rd | 16/19 |

**Example:**
In nonsegmented mode, if register R12 (a stack pointer) contains %1000, the word at location %1000 contains %0055, and register R3 contains %0022, the instruction
```assembly
POP R3, @R12
```
will leave the value %0055 in R3 and the value %1002 in R12.

---

### PUSH / PUSHL
**Push**

**PUSH dst, src**
**PUSHL**

**dst: IR**
**src: R, IM, IR, DA, X**

**Operation:**
AUTODECREMENT dst (by 2 if word, by 4 if long)
dst <- src

The contents of the destination register (a stack pointer) are decremented by a value which equals the size in bytes of the source operand. Then the source operand is loaded into the location addressed by the updated destination register, thus adding a new element to the top of the stack. Any register except R0 (or RR0 in segmented mode) can be used as a stack pointer.

**Flags:**
No flags affected.

**Instruction Formats and Execution Times:**

| Source Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | PUSH @Rd, Rs | 10010111 Rd Rs | 9 | 10010111 RRd RRs | 9 |
| R (Long) | PUSHL @Rd, RRs | 01010001 Rd RRs | 12 | 01010001 RRd RRs | 12 |
| IM | PUSH @Rd, #data | 00100110 1 Rd 10011 | 12 | 00100110 1 RRd 10011 | 12 |
| IR | PUSH @Rd, @Rs | 01010111 Rd Rs | 13 | 01010111 RRd RRs | 13 |
| DA | PUSH @Rd, address | 10110100 11 Rd 0000 | 14 | 01101001 1 RRd 0000 | 14/16 |
| X | PUSH @Rd, addr(Rs)| 10110100 11 Rd Rs | 14 | 01101001 1 RRd Rs | 14/17 |

---

### RES / RESB
**Reset Bit**

**RES dst, src**
**RESB**

**dst: R, IR, DA, X**
**src: IM (Static) or R (Dynamic)**

**Operation:**
dst(src) <- 0

This instruction clears the specified bit within the destination operand without affecting any other bits in the destination. The bit number is a value from 0 to 7 for RESB, or 0 to 15 for RES, with 0 indicating the least significant bit.

**Flags:**
No flags affected.

**Instruction Formats (Static - Immediate Bit Number):**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | RES Rd, #b | 10000111 0b Rd | 4 | 10000111 0b Rd | 4 |
| IR | RES @Rd, #b | 10011000 0b Rd | 11 | 1101000w RRd 0b | 11 |
| DA | RES address, #b | 10111000 1w 0000 b | 13 | 01110001 1w 0000 b | 14/16 |

**Instruction Formats (Dynamic - Register Bit Number):**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | RES Rd, Rs | 10011000 1w 0000 Rs | 10 | 10011000 1w 0000 Rs | 10 |

---

### RESFLG
**Reset Flag**

**RESFLG flag**

**flag: C, Z, S, P, V**

**Operation:**
FLAGS (4:7) <- FLAGS (4:7) AND NOT instruction (4:7)

Any combination of the C, Z, S, P or V flags are cleared to zero if the corresponding bits in the instruction are one.

**Flags:**
*   **C, Z, S, P/V:** Cleared if specified; unaffected otherwise.

| Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- |
| RESFLG flags | 10001101 00 flags 0011 | 7 |

---

### RET
**Return from Procedure**

**RET cc**

**Operation:**
**Nonsegmented:**
if cc is true then
  PC <- @SP
  SP <- SP + 2

**Segmented:**
if cc is true then
  PC <- @SP
  SP <- SP + 4

This instruction is used to return to a previously executed procedure at the end of a procedure entered by a CALL or CALR instruction. If the condition specified by "cc" is satisfied, then the contents of the location addressed by the processor stack pointer are popped into the program counter (PC).

**Flags:**
No flags affected.

| Assembler Syntax | Format | Cycles (Nonseg T/NT) | Cycles (Seg T/NT) |
| :--- | :--- | :--- | :--- |
| RET cc | 10011110 cc 0000 0000 | 10/7 | 13/7 |

Note: T/NT = Return Taken / Return Not Taken cycles.

### RL / RLB
**Rotate Left**

**RL dst, src**
**RLB**

**dst: R**
**src: IM (1 or 2)**

**Operation:**
Do src times: (src = 1 or 2)
  tmp <- dst
  C <- tmp (msb)
  dst(0) <- tmp (msb)
  dst (n + 1) <- tmp (n) (for n = 0 to msb - 1)

The contents of the destination operand are rotated left one bit position if the source operand is 1, or two bit positions if the source operand is 2. The most significant bit (msb) of the destination operand is moved to the bit 0 position and also replaces the C flag. The source operand may be omitted from the assembly language statement and thus defaults to the value 1.

**Flags:**
*   **C:** Set if the last bit rotated from the most significant bit position was 1; cleared otherwise.
*   **Z:** Set if the result is zero; cleared otherwise.
*   **S:** Set if the most significant bit of the result is set; cleared otherwise.
*   **V:** Set if arithmetic overflow occurs, that is, if the sign of the destination changed during rotation; cleared otherwise.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles (1/2 bits) | Format (Seg) | Cycles (1/2 bits) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | RL Rd, #n | 10001101 0w Rd 0001 | 6/7 | 11011101 0w Rd 0001 | 6/7 |

Note: s = 0 for rotation by 1 bit; s = 1 for rotation by 2 bits.

---

### RLC / RLCB
**Rotate Left through Carry**

**RLC dst, src**
**RLCB**

**dst: R**
**src: IM (1 or 2)**

**Operation:**
Do src times: (src = 1 or 2)
  tmp <- C
  C <- dst (msb)
  dst (n + 1) <- dst (n) (for n = msb - 1 to 0)
  dst (0) <- tmp

The contents of the destination operand with the C flag are rotated left one bit position if the source operand is 1, or two bit positions if the source operand is 2. The most significant bit (msb) of the destination operand replaces the C flag and the previous value of the C flag is moved to the bit 0 position of the destination during each rotation.

**Flags:**
*   **C:** Set if the last bit rotated from the msb was 1.
*   **Z:** Set if result is zero.
*   **S:** Set if MSB is set.
*   **V:** Set if sign changed during rotation.

| Addressing Mode | Assembler Syntax | Format | Cycles (1/2 bits) |
| :--- | :--- | :--- | :--- |
| R | RLC Rd, #n | 110011w s Rd 0000 | 6/7 |

**Example:**
If the Carry flag is clear (= 0) and register R0 contains %800F (1000000000001111), the statement
```assembly
RLC R0, #2
```
will leave the value %003D (0000000000111101) in R0 and clear the Carry flag.

---

### RLDB
**Rotate Left Digit**

**RLDB link, src**

**src: R**
**link: R**

**Operation:**
tmp (0:3) <- link (0:3)
link (0:3) <- src (4:7)
src (4:7) <- src (0:3)
src (0:3) <- tmp (0:3)

The low digit of the link byte register is logically concatenated to the source byte register. The resulting three-digit quantity is rotated to the left by one BCD digit (four bits). The upper digit of the link is unaffected. The same byte register must not be used as both the source and the link.

**Flags:**
*   **Z:** Set if the link is zero after the operation; cleared otherwise.
*   **S:** Undefined.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| R | RLDB Rb1, Rbs | 11111100 Rbs Rb1 | 9 |

---

### RR / RRB
**Rotate Right**

**RR dst, src**
**RRB**

**dst: R**
**src: IM (1 or 2)**

**Operation:**
Do src times: (src = 1 or 2)
  tmp <- dst
  C <- tmp (0)
  dst (msb) <- tmp (0)
  dst (n - 1) <- tmp (n) (for n = 1 to msb)

**Flags:**
*   **C:** Set if the last bit rotated from the least significant position was 1.
*   **Z, S, V:** Set according to result.

| Addressing Mode | Assembler Syntax | Format | Cycles (1/2 bits) |
| :--- | :--- | :--- | :--- |
| R | RR Rd, #n | 1101110w s Rd 0011 | 6/7 |

---

### RRC / RRCB
**Rotate Right through Carry**

**RRC dst, src**
**RRCB**

**dst: R**
**src: IM (1 or 2)**

**Operation:**
Do src times: (src = 1 or 2)
  tmp <- C
  C <- dst (0)
  dst (n) <- dst (n + 1) (for n = 0 to msb - 1)
  dst (msb) <- tmp

**Flags:**
*   **C:** Set if the last bit rotated from the least significant bit position was 1.

---

### RRDB
**Rotate Right Digit**

**RRDB link, src**

**src: R**
**link: R**

**Operation:**
tmp (0:3) <- link (0:3)
link (0:3) <- src (0:3)
src (0:3) <- src (4:7)
src (4:7) <- tmp (0:3)

The low digit of the link byte register is logically concatenated to the source byte register. The resulting three-digit quantity is rotated to the right by one BCD digit (four bits). The upper digit of the link is unaffected.

**Flags:**
*   **Z:** Set if the link is zero after the operation; cleared otherwise.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| R | RRDB Rb1, Rbs | 11111100 Rbs Rb1 | 9 |

### SBC / SBCB
**Subtract with Carry**

**SBC dst, src**
**SBCB**

**dst: R**
**src: R**

**Operation:**
dst <- dst - src - C

The source operand, along with the setting of the carry flag, is subtracted from the destination operand and the result is stored in the destination. The contents of the source are not affected. Subtraction is performed by adding the two's complement of the source operand to the destination operand. In multiple precision arithmetic, this instruction permits the carry ("borrow") from the subtraction of low-order operands to be subtracted from the subtraction of high-order operands.

**Flags:**
*   **C:** Cleared if there is a carry from the most significant bit of the result; set otherwise, indicating a "borrow".
*   **Z:** Set if the result is zero; cleared otherwise.
*   **S:** Set if the result is negative; cleared otherwise.
*   **V:** Set if arithmetic overflow occurs, that is, if the operands were of opposite signs and the sign of the result is the same as the sign of the source; cleared otherwise.
*   **D:** SBC-unaffected; SBCB-set.
*   **H:** SBC-unaffected; SBCB-cleared if there is a carry from the most significant bit of the low-order four bits of the result; set otherwise, indicating a "borrow".

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | SBC Rd, Rs | 10001011 Rs Rd | 5 | 10001011 Rs Rd | 5 |
| R | SBCB Rbd, Rbs | 10001010 Rbs Rbd | 5 | 10001010 Rbs Rbd | 5 |

**Example:**
Long subtraction may be done with the following instruction sequence, assuming R0, R1 contain one operand and R2, R3 contain the other operand:
```assembly
SUB R1, R3    !subtract low-order words!
SBC R0, R2    !subtract carry and high-order words!
```

---

### SC
**System Call**

**SC src**

**src: IM**

**Operation:**
**Nonsegmented:**
SP <- SP - 4
@SP <- PS
SP <- SP - 2
@SP <- instruction
PS <- System Call PS

**Segmented:**
SP <- SP - 6
@SP <- PS
SP <- SP - 2
@SP <- instruction
PS <- System Call PS

This instruction is used for controlled access to operating system software in a manner similar to a trap or interrupt. The current program status (PS) is pushed on the system processor stack, and then the instruction itself, which includes the source operand (an 8-bit value) is pushed. The PS includes the Flag and Control Word (FCW), and the updated program counter (PC). (The updated program counter value used is the address of the first instruction following the SC instruction.) The system stack pointer is always used (R15 in nonsegmented CPUs, or RR14 in segmented CPUs).

**Saved Program Status Format on System Stack:**

**NONSEGMENTED:**
```text
(SP AFTER TRAP) -> [ IDENTIFIER ] (SC Instruction)
                   [ FCW        ]
                   [ PC         ]
(SP BEFORE TRAP) ->
```

**SEGMENTED:**
```text
(SP AFTER TRAP) -> [ IDENTIFIER ] (SC Instruction)
                   [ FCW        ]
                   [ PC SEGMENT ]
                   [ PC OFFSET  ]
(SP BEFORE TRAP) ->
```

**Flags:**
Flags loaded from Program Status Area.

| Source Mode | Assembler Syntax | Format | Cycles (Nonseg) | Cycles (Seg) |
| :--- | :--- | :--- | :--- | :--- |
| IM | SC #src | 01111111 src | 33 | 39 |

---

### SDA / SDAB / SDAL
**Shift Dynamic Arithmetic**

**SDA dst, src**
**SDAB**
**SDAL**

**dst: R**
**src: R**

**Operation:**
**Right (src negative):**
Do -src times:
  C <- dst (0)
  dst (n) <- dst (n + 1) (for n = 0 to msb - 1)
  dst (msb) <- dst (msb)
**Left (src positive):**
Do src times:
  C <- dst (msb)
  dst (n + 1) <- dst (n) (for n = msb - 1 to 0)
  dst (0) <- 0

The destination operand is shifted arithmetically left or right by the number of bit positions specified by the contents of the source operand (a word register). Shift count ranges: -8 to +8 (SDAB), -16 to +16 (SDA), -32 to +32 (SDAL). Positive values = left shift, Negative values = right shift.

**Flags:**
*   **C:** Set if the last bit shifted was 1.
*   **Z, S, V:** Set according to result.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| R | SDA Rd, Rs | 00110001 1w 0000 Rs / 0000 Rd 0000 0000 | 15+3n |

---

### SDL / SDLB / SDLL
**Shift Dynamic Logical**

**SDL dst, src**
**SDLB**
**SDLL**

**dst: R**
**src: R**

**Operation:**
**Right (src negative):** MSB is filled with 0.
**Left (src positive):** LSB is filled with 0.

Similar to SDA, but no sign replication.

**Flags:**
*   **C:** Set if the last bit shifted was 1.
*   **V:** Undefined.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| R | SDL Rd, Rs | 00110000 1w 0000 Rs / 0000 Rd 0000 0000 | 15+3n |

---

### SET / SETB
**Set Bit**

**SET dst, src**
**SETB**

**dst: R, IR, DA, X**
**src: IM (Static) or R (Dynamic)**

**Operation:**
dst(src) <- 1

Sets the specified bit within the destination operand.

**Flags:**
No flags affected.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R (Static) | SET Rd, #b | 10001111 1b Rd | 4 | 10001111 1b Rd | 4 |
| R (Dynamic) | SET Rd, Rs | 10010010 1w 0000 Rs| 10 | 10010010 1w 0000 Rs | 10 |

---

### SETFLG
**Set Flag**

**SETFLG flag**

**flag: C, Z, S, P, V**

**Operation:**
FLAGS (4:7) <- FLAGS (4:7) OR instruction (4:7)

Any combination of the C, Z, S, P or V flags are set to one if the corresponding bits in the instruction are one.

**Flags:**
*   **C, Z, S, P/V:** Set if specified; unaffected otherwise.

| Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- |
| SETFLG flags | 10001101 00 flags 0001 | 7 |

### SLA / SLAB / SLAL
**Shift Left Arithmetic**

**SLA dst, src**
**SLAB**
**SLAL**

**dst: R**
**src: IM**

**Operation:**
Do src times:
  C <- dst (msb)
  dst (n + 1) <- dst (n) (for n = msb - 1 to 0)
  dst (0) <- 0

The destination operand is shifted arithmetically left the number of bit positions specified by the source operand. For SLAB, the source is in the range 0 to 8; for SLA, the source is in the range 0 to 16; for SLAL, the source is in the range 0 to 32. The least significant bit of the destination is filled with 0, and the C flag is loaded from the sign bit of the destination. A shift of zero positions does not affect the destination; however, the flags are set according to the destination value with the C flag undefined.

**Flags:**
*   **C:** Set if the last bit shifted from the destination was 1, undefined for zero shift; cleared otherwise.
*   **Z, S, V:** Set according to result.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| R | SLA Rd, #b | 11011110 1w 0000 b | 13+3b |

**Example:**
If register pair RR2 contains %1234ABCD, the statement
```assembly
SLAL RR2, #8
```
will leave the value %34ABCD00 in RR2 and clear the Carry flag.

---

### SLL / SLLB / SLLL
**Shift Left Logical**

**SLL dst, src**
**SLLB**
**SLLL**

**dst: R**
**src: IM**

**Operation:**
Do src times:
  C <- dst (msb)
  dst (n + 1) <- dst (n) (for n = msb - 1 to 0)
  dst (0) <- 0

The destination operand is shifted logically left by the number of bit positions specified by the source operand. The least significant bit of the destination is filled with 0, and the C flag is loaded from the most significant bit (msb) of the destination.

**Flags:**
*   **C:** Set if the last bit shifted from the destination was 1.
*   **Z, S:** Set according to result.
*   **V:** Undefined.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| R | SLL Rd, #b | 1101110w 0100 b | 13+3b |

---

### SRA / SRAB / SRAL
**Shift Right Arithmetic**

**SRA dst, src**
**SRAB**
**SRAL**

**dst: R**
**src: IM**

**Operation:**
Do src times:
  C <- dst (0)
  dst (n) <- dst (n + 1) (for n = 0 to msb - 1)
  dst (msb) <- dst (msb)

The destination operand is shifted arithmetically right by the number of bit positions specified by the source operand. The most significant bit (msb) of the destination is replicated, and the C flag is loaded from bit 0 of the destination.

**Flags:**
*   **C:** Set if the last bit shifted from the destination was 1; cleared otherwise.
*   **V:** Cleared.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| R | SRA Rd, #b | 1101111w 0000 b | 13+3b |

---

### SRL / SRLB / SRLL
**Shift Right Logical**

**SRL dst, src**
**SRLB**
**SRLL**

**dst: R**
**src: IM**

**Operation:**
Do src times:
  C <- dst (0)
  dst (n) <- dst (n + 1) (for n = 0 to msb - 1)
  dst (msb) <- 0

The destination operand is shifted logically right by the number of bit positions specified by the source operand. The most significant bit (msb) of the destination is filled with 0, and the C flag is loaded from bit 0 of the destination.

**Flags:**
*   **C:** Set if the last bit shifted from the destination was 1; cleared otherwise.
*   **V:** Undefined.

| Addressing Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| R | SRL Rd, #b | 1101110w 0000 b | 13+3b |

---

### SUB / SUBB / SUBL
**Subtract**

**SUB dst, src**
**SUBB**
**SUBL**

**dst: R**
**src: R, IM, IR, DA, X**

**Operation:**
dst <- dst - src

The source operand is subtracted from the destination operand and the result is stored in the destination. The contents of the source are not affected. Subtraction is performed by adding the two's complement of the source operand to the destination operand.

**Flags:**
*   **C:** Cleared if there is a carry from the most significant bit; set otherwise, indicating a "borrow".
*   **Z, S, V:** Set according to result.
*   **D:** SUB, SUBL-unaffected; SUBB-set.
*   **H:** SUB, SUBL-unaffected; SUBB-cleared if there is a carry from bit 3; set otherwise, indicating a "borrow".

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | SUB Rd, Rs | 10000011 Rs Rd | 4 | 10000011 Rs Rd | 4 |
| R (Long) | SUBL RRd, RRs | 10100010 RRs RRd | 8 | 10100010 RRs RRd | 8 |
| IM | SUB Rd, #data | 00100010 0000 Rd | 7 | 00100010 0000 Rd | 7 |
| IR | SUB Rd, @Rs | 00000010 Rs 0000 | 7 | 10000011 RRs 0000 | 7 |
| DA | SUB Rd, address | 10110001 0w 0000 Rd | 9 | 01100001 1w 0000 Rd | 10/12 |
| X | SUB Rd, addr(Rs) | 10110001 0w Rs Rd | 10 | 01100001 1w Rs Rd | 10/13 |

---

### TCC / TCCB
**Test Condition Code**

**TCC cc, dst**
**TCCB**

**dst: R**

**Operation:**
if cc is satisfied then
  dst (0) <- 1

This instruction is used to create a Boolean data value based on the flags set by a previous operation. The flags in the FCW are tested to see if the condition specified by "cc" is satisfied. If the condition is satisfied, then the least significant bit of the destination is set. If the condition is not satisfied, bit zero of the destination is not cleared but retains its previous value. All other bits in the destination are unaffected by this instruction.

**Flags:**
No flags affected.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | TCC cc, Rd | 10011101 cc Rd 1000 | 5 | 10011101 cc Rd 1000 | 5 |

### TEST / TESTB / TESTL
**Test**

**TEST dst**
**TESTB**
**TESTL**

**dst: R, IR, DA, X**

**Operation:**
dst OR 0

The destination operand is tested (logically ORed with zero), and the Z, S and P flags are set to reflect the attributes of the result. The flags may then be used for logical conditional jumps. The contents of the destination are not affected.

**Flags:**
*   **C:** Unaffected.
*   **Z:** Set if the result is zero; cleared otherwise.
*   **S:** Set if the most significant bit of the result is set; cleared otherwise.
*   **P:** TEST-unaffected; TESTL-undefined; TESTB-set if parity of the result is even; cleared otherwise.
*   **D, H:** Unaffected.

**Instruction Formats and Execution Times:**

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | TEST Rd | 10001011 0w Rd 0100 | 7 | 10001011 0w Rd 0100 | 7 |
| R (Long) | TESTL RRd | 10111001 RRd 0000 | 13 | 10111001 RRd 0000 | 13 |
| IR | TEST @Rd | 0000110w Rd 0100 | 8 | 1000110w RRd 0100 | 8 |
| DA | TEST address | 10110011 0w 0000 0100| 11 | 01100110 1w 0000 0100 | 12/14 |
| X | TEST addr(Rd) | 10110011 0w Rd 0100 | 12 | 01100110 1w Rd 0100 | 12/15 |

---

### TRDB / TRDRB
**Translate and Decrement / Translate, Decrement and Repeat**

**TRDB dst, src, r**
**TRDRB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src [dst]
AUTODECREMENT dst by 1
r <- r - 1
(TRDRB: repeat until r = 0)

This instruction is used to translate a string of bytes from one code to another code. The contents of the location addressed by the destination register (the "target byte") are used as an index into a table of translation values whose lowest address is contained in the source register. The original contents of register RH1 are lost and are replaced by an undefined value.

**Flags:**
*   **V:** Set if the result of decrementing r is zero (TRDB) or always set (TRDRB).

| Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| IR | TRDB @Rd, @Rs, r | 11011110 00 Rd 0110 / 0000 r Rs 0000 | 25 |
| IR | TRDRB @Rd, @Rs, r | 11011110 00 Rd 0111 / 0000 r Rs 0000 | 11+14n |

---

### TRIB / TRIRB
**Translate and Increment / Translate, Increment and Repeat**

**TRIB dst, src, r**
**TRIRB**

**dst: IR**
**src: IR**

**Operation:**
dst <- src [dst]
AUTOINCREMENT dst by 1
r <- r - 1
(TRIRB: repeat until r = 0)

---

### TRTDB / TRTDRB
**Translate, Test and Decrement / Translate, Test, Decrement and Repeat**

**TRTDB src1, src2, r**
**TRTDRB**

**src1: IR (string)**
**src2: IR (table)**

**Operation:**
RH1 <- src2 [src1]
AUTODECREMENT src1 by 1
r <- r - 1
(TRTDRB: repeat until RH1 != 0 or r = 0)

This instruction is used to scan a string of bytes testing for bytes with special meaning. The Z flag is set if the value loaded into RH1 is zero.

**Flags:**
*   **Z:** Set if the translation value loaded into RH1 is zero.
*   **V:** Set if r becomes zero.

| Mode | Assembler Syntax | Format | Cycles |
| :--- | :--- | :--- | :--- |
| IR | TRTDB @Rs1, @Rs2, r | 11011110 00 Rs1 1010 / 0000 r Rs2 0000 | 25 |
| IR | TRTDRB @Rs1, @Rs2, r | 11011110 00 Rs1 1011 / 0000 r Rs2 0000 | 11+14n |

---

### TRTIB / TRTIRB
**Translate, Test and Increment / Translate, Test, Increment and Repeat**

**TRTIB src1, src2, r**
**TRTIRB**

Similar to TRTDB, but pointers are incremented.

---

### TSET / TSETB
**Test and Set**

**TSET dst**
**TSETB**

**dst: R, IR, DA, X**

**Operation:**
S <- dst(msb)
dst(0:msb) <- 111...111

Tests the most significant bit of the destination operand, copying its value into the S flag, then sets the entire destination to all 1 bits. This instruction provides a locking mechanism. During execution, BUSRQ is not honored between loading and storing to ensure atomicity.

**Flags:**
*   **S:** Set if the MSB of the destination was 1; cleared otherwise.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | TSET Rd | 10001101 0w Rd 0110 | 7 | 10001101 0w Rd 0110 | 7 |
| IR | TSET @Rd | 0000110w Rd 0110 | 11 | 1000110w RRd 0110 | 11 |
| DA | TSET address | 10110011 0w 0000 0110| 14 | 01100110 1w 0000 0110 | 15/17 |
| X | TSET addr(Rd) | 10110011 0w Rd 0110 | 15 | 01100110 1w Rd 0110 | 15/18 |

---

### XOR / XORB
**Exclusive Or**

**XOR dst, src**
**XORB**

**dst: R**
**src: R, IM, IR, DA, X**

**Operation:**
dst <- dst XOR src

**Flags:**
*   **Z, S, P:** Set according to result.

| Addressing Mode | Assembler Syntax | Format (Nonseg) | Cycles | Format (Seg SS/SL) | Cycles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R | XOR Rd, Rs | 10001001 Rs Rd | 4 | 10001001 Rs Rd | 4 |
| IM | XOR Rd, #data | 00100100 0000 Rd | 7 | 00100100 0000 Rd | 7 |
| IR | XOR Rd, @Rs | 00000100 Rs 0000 | 7 | 10001001 RRs 0000 | 7 |

---

## 6.8 EPA Instruction Templates

The Z8000 CPU supports seven "templates" for EPA instructions. These templates correspond to EPA instructions, which combine EPU operations with possible transfers between memory and an EPU, between CPU registers and EPU registers, and between the Flag byte of the CPU's FCW and the EPU.

**1. Load Memory from EPU**
Operation: Memory <- EPU
The CPU performs address calculation and generates n EPU memory write transactions.

**2. Load EPU from Memory**
Operation: EPU <- Memory
The CPU performs address calculation and generates n EPU memory read transactions.

**3. Load CPU from EPU**
Operation: CPU <- EPU registers
The contents of n words are transferred from an EPU to consecutive CPU registers starting with dst.

**4. Load EPU from CPU**
Operation: EPU <- CPU registers
The contents of n words are transferred to an EPU from consecutive CPU registers starting with src.

**5. Load FCW from EPU**
Operation: Flags <- EPU
The Flags in the FCW are loaded with information from an EPU on AD lines AD0-AD7.

**6. Load EPU from FCW**
Operation: EPU <- Flags
The Flags in the FCW are transferred to an EPU.

**7. Internal EPU Operation**
Operation: Internal EPU Operation
The CPU treats this template as a No Op.

# Chapter 7
# Exceptions

## 7.1 Introduction
The Z8000 CPU supports three types of exceptions (conditions that can alter the normal flow of program execution):
* interrupts
* traps
* reset

Interrupts are asynchronous events typically triggered by peripheral devices needing attention. They cause the processor to temporarily suspend its present program execution in order to service the requesting device. Traps are synchronous events that are responses by the CPU to certain events detected during the attempted execution of an instruction. Thus, the major distinction between traps and interrupts is their origin: a trap condition is always reproducible by re-executing the program that created the traps, whereas an interrupt is generally independent of the currently executing task. A reset overrides all other conditions, including all interrupts and traps. It occurs when the RESET line is activated, and it causes certain control registers to be initialized. The action that the Z8000 CPU takes in response to an interrupt, trap, or reset is similar; hence, they are treated together in this chapter.

## 7.2 Interrupts
Three kinds of interrupts are activated by three different pins on the Z8000 CPU. (Interrupt handling for all interrupts is discussed in Section 7.6.)

### 7.2.1 Non-Maskable Interrupt (NMI)
This type of interrupt cannot be disabled (masked) by software. It is typically reserved for highest-priority external events that require immediate attention.

### 7.2.2 Vectored Interrupt (VI)
One result of any interrupt or trap is that a 16-bit identifier word is pushed onto the system stack (see Section 7.6.2). This word may be used to identify the source of the interrupt or trap. In vectored interrupts, this identifier is also used by the CPU hardware as a pointer to select a particular interrupt service routine. The processing of vectored interrupts is thus considerably faster than would be the case if a general trap handler had to first examine the identifier, then branch off to the appropriate service routine. These interrupts can be disabled by software.

### 7.2.3 Nonvectored Interrupts (NVI)
These interrupts also result in an identifier word being pushed onto the system stack. However, the CPU does not use the identifier as a vector to select a service routine: all non-vectored interrupts are handled by the same interrupt procedure. They can be disabled by software.

## 7.3 Traps
The Z8001 and Z8002 CPUs support three traps generated internally. The Z8001 supports a fourth trap, which is generated externally (but synchronously) by the Memory Management Unit. Since a trap always occurs when all its defining conditions are present, traps cannot be disabled. (Trap handling operations are discussed in Section 7.6.)

### 7.3.1 Extended Instruction Trap
This trap occurs when the CPU encounters an extended instruction (see Section 6.2.10) while the EPA bit in the FCW is cleared. This trap allows the program to simulate the operations of the EPU when none is present in the system or to abort the program.

### 7.3.2 Privileged Instruction Trap
This trap occurs whenever an attempt is made to execute a privileged instruction while the CPU is in normal mode (S/N bit in the FCW is cleared). This trap allows the CPU to detect and prevent operation (such as I/O) that could disable the system.

### 7.3.3 System Call Trap
This trap occurs whenever a System Call (SC) instruction is executed. It allows an orderly transition to be made between normal mode and system mode.

### 7.3.4 Segment Trap
This trap occurs whenever the SEGT line is asserted on a Z8001, regardless of the state of the SEG bit in the FCW. This trap is generated by external memory management hardware, such as the Z8010 Memory Management Unit (MMU), and is the result of detecting a memory access violation (such as an offset larger than the assigned segment length) or a write warning (a write into the lowest 256 bytes of a stack).

## 7.4 Reset
A reset initializes selected control registers of the CPU to system specifiable values. A reset can occur at the end of any clock cycle, provided the RESET line is Low.

A system reset overrides all other considerations, including interrupts, traps, bus requests, and stop requests. A reset should be used to initialize a system as part of the power-up sequence.

Within five clock cycles of the RESET becoming Low, AD0-AD15 are 3-stated; AS, DS, MREQ, BUSACK, and MO are forced High; ST0-ST3 are forced High and SN0-SN6 are forced Low. The R/W, B/W, and N/S lines are undefined. RESET must be held Low five clock cycles to properly reset the CPU.

Three clock cycles after RESET has returned to High, consecutive memory read cycles are executed in system mode to initialize the Program Status registers. In the Z8001, the first cycle reads the FCW from location 0002 of segment 0, the next reads the PC from location 0004, and the following initial instruction fetch cycle starts the program. In the Z8002, the first cycle reads the FCW from location 0004 and the following initial instruction fetch cycle starts the program.

## 7.5 Interrupt Disabling
Vectored and nonvectored interrupts can be enabled or disabled independently via software by setting or clearing appropriate control bits in the Flag and Control Word (FCW). Two control bits in the FCW control the maskable interrupts: VIE and NVIE. When VIE is 1, vectored interrupts are enabled; when NVIE is 1, non-vectored interrupts are enabled.

## 7.6 Interrupt and Trap Handling
The CPU response to a trap or interrupt request consists of five steps: acknowledging the external request, saving the old program status information, loading a new program status, executing the service routine, and returning to the interrupted task.

### 7.6.1 Acknowledge Cycle
An external acknowledge cycle is required only for externally generated requests. The main effect of such a cycle is to receive from the external device a 16-bit identifier word, which will be saved with the old program status. Before the acknowledge cycle, the CPU enters segmented (Z8001 only) system mode.

### 7.6.2 Status Saving
The old program status information is saved by being pushed on the system stack in the following order: the Program Counter; the Flag and Control Word (FCW); and finally, the interrupt/trap identifier word.

**PC Value Pushed on Stack:**
| Exception | PC Value Is Address of: |
| :--- | :--- |
| Extended Instruction Trap | Second Word of Instruction |
| Privileged Instruction Trap | Word Following First Word of Instruction |
| System Call Trap | Next Instruction |
| Segment Trap | Next Instruction*† |
| All Interrupts | Next Instruction† |

* Assumes successful completion of instruction fetch.
† If executing an interruptible instruction (e.g., LDIR) and the instruction has not completed, then the next instruction is the current instruction.

**Figure 7.1 Format of Saved Program Status in the System Stack:**

**Z8002 (Nonsegmented):**
```text
LOW ADDRESS  -> [ IDENTIFIER ] <- SYSTEM SP AFTER INTERRUPT
                [ FCW        ]
                [ PC         ] <- SYSTEM SP BEFORE INTERRUPT
HIGH ADDRESS
```

**Z8001 (Segmented):**
```text
LOW ADDRESS  -> [ IDENTIFIER ] <- SYSTEM SP AFTER INTERRUPT
                [ FCW        ]
                [ PC SEGMENT ]
                [ PC OFFSET  ] <- SYSTEM SP BEFORE INTERRUPT
HIGH ADDRESS
```

### 7.6.3 Loading New Program Status
After saving the current program status, the new program status (PC and FCW) is automatically loaded from the Program Status Area (PSA) in system program memory. The Program Status Area is addressed by the Program Status Area Pointer (PSAP).

**Figure 7.2 Program Status Area Layout:**

| Byte Offset (Z8001) | Byte Offset (Z8002) | Exception Type |
| :--- | :--- | :--- |
| %0000 | %0000 | Reserved |
| %0008 | %0004 | Extended Instruction Trap |
| %0010 | %0008 | Privileged Instruction Trap |
| %0018 | %000C | System Call Trap |
| %0020 | - | Segment Trap (Z8001 only) |
| %0028 | %0010 | Non-maskable Interrupt |
| %0030 | %0014 | Non-vectored Interrupt |
| %0038 | %0018 | Vectored Interrupt (FCW) |
| %003C+ | %001C+ | Vectored Interrupt (PC list) |

For vectored interrupts, the identifier's low-order byte is multiplied by 2 and used as an offset following the vectored interrupt FCW to select one of up to 256 (Z8002) or 128 (Z8001) PC values.

### 7.6.4 Executing the Service Routine
Loading the new program status automatically initializes the Program Counter to the starting address of the service routine. Because a new FCW was loaded, the maskable interrupts can be disabled for the initial processing of the service routine.

### 7.6.5 Returning from an Interrupt or Trap
Upon completion, the service routine can execute an Interrupt Return instruction, IRET, to cause execution to continue at the point where the interrupt or trap occurred.

## 7.7 Priority
Because it is possible for several exceptions to occur simultaneously, the CPU enforces a priority scheme. The descending priority order is:
1. Reset
2. Internal Trap (Privileged instruction, System Call, Extended instruction)
3. Non-Maskable Interrupt
4. Segment Trap (Z8001 only)
5. Vectored Interrupt
6. Nonvectored Interrupt

# Chapter 9
# External Interface

## 9.1 Introduction
This chapter covers the external manifestations (e.g., the activity on the CPU pins) that result from the operations described in Chapters 2 through 8. The Z8000 CPU is designed to be compatible with the Zilog Z-Bus protocols.

## 9.2 Bus Operations
Two kinds of operations can occur on the system bus: transactions and requests. A transaction is initiated by the bus master and is responded to by some other device on the bus. Only one transaction can proceed at a time; six kinds of transactions can occur:
*   **Memory transaction:** To transfer 8 or 16 bits to/from memory.
*   **I/O transaction:** To transfer 8 or 16 bits to/from a peripheral or MMU.
*   **EPU transfer:** To transfer data between CPU and an EPU.
*   **Interrupt/Trap Acknowledge:** To read an identifier word from a device.
*   **Refresh:** To refresh dynamic memory (no data transfer).
*   **Internal operation:** No data transfer, status-only cycle.

Four types of requests can occur: Interrupt, Bus (BUSREQ), Resource (Multi-Micro), and Stop.

## 9.3 CPU Pins

### 9.3.1 Transaction Pins
*   **AD0-AD15:** Multiplexed Address/Data lines.
*   **SN0-SN6:** (Z8001 only) Segment Number lines.
*   **ST0-ST3:** Status Lines.
*   **AS:** Address Strobe.
*   **DS:** Data Strobe.
*   **MREQ:** Memory Request.
*   **R/W:** Read/Write (Low = Write).
*   **B/W:** Byte/Word (High = Byte).
*   **N/S:** Normal/System (High = Normal).
*   **WAIT:** Input to extend a bus transaction.

### 9.3.2 Bus Control Pins
*   **BUSREQ:** Bus Request input.
*   **BUSACK:** Bus Acknowledge output.

### 9.3.3 Interrupt/Trap Pins
*   **NMI:** Non-Maskable Interrupt (Edge activated).
*   **NVI:** Non-Vectored Interrupt (Active Low).
*   **VI:** Vectored Interrupt (Active Low).
*   **SEGT:** Segment Trap (Z8001 only, active Low).

### 9.3.4 Multi-Micro Pins
*   **MI:** Multi-Micro In.
*   **MO:** Multi-Micro Out.

## 9.4 Transactions

**Table 9.1 Status Codes:**
| ST3 | ST2 | ST1 | ST0 | Definition |
| :--- | :--- | :--- | :--- | :--- |
| 0 | 0 | 0 | 0 | Internal operation |
| 0 | 0 | 0 | 1 | Memory refresh |
| 0 | 0 | 1 | 0 | Standard I/O |
| 0 | 0 | 1 | 1 | Special I/O |
| 0 | 1 | 0 | 0 | Segment Trap Acknowledge |
| 0 | 1 | 0 | 1 | Non-Maskable Interrupt Ack |
| 0 | 1 | 1 | 0 | Non-Vectored Interrupt Ack |
| 0 | 1 | 1 | 1 | Vectored Interrupt Ack |
| 1 | 0 | 0 | 0 | Data Memory Request |
| 1 | 0 | 0 | 1 | Stack Memory Request |
| 1 | 0 | 1 | 0 | Data Memory Request (EPU) |
| 1 | 0 | 1 | 1 | Stack Memory Request (EPU) |
| 1 | 1 | 0 | 0 | Instruction Space Access |
| 1 | 1 | 0 | 1 | Instruction Fetch (1st word) |
| 1 | 1 | 1 | 0 | CPU-EPA Transfer |
| 1 | 1 | 1 | 1 | Test and Set (Z8003/4 only) |

### 9.4.1 WAIT
WAIT is sampled on a falling clock edge. If Low, another clock cycle is added to the transaction. This allows slow memories or I/O devices to prolong the transaction.

### 9.4.2 Memory Transactions
Memory transactions are three clock cycles long unless extended by WAIT.
*   **Byte selection:** Even addresses (A0=0) use AD8-AD15. Odd addresses (A0=1) use AD0-AD7. During byte writes, the CPU puts the same data on both halves of the bus.

### 9.4.3 I/O Transactions
I/O transactions are four clock cycles long.
*   **Standard I/O:** status 0010. Byte transfers on AD0-AD7.
*   **Special I/O:** status 0011. Byte transfers on AD8-AD15.

### 9.4.5 Interrupt/Trap Acknowledge Transactions
These are eight clock cycles long minimum, including five automatic WAIT cycles to allow the interrupt daisy chain to settle.

## 9.5 CPU and Extended Processing Unit Interaction
The CPU and EPU act as a single unit. The CPU provides address and timing, while the EPU supplies or captures data. EPUs monitor the instruction stream (status 1101) to identify extended instructions via an ID field.

## 9.6 Requests

### 9.6.2 Bus Request
Initiated by BUSREQ Low. If Low at the beginning of a machine cycle, the CPU asserts BUSACK at the end of the current cycle and enters Bus-Disconnect state (3-stating all pins except BUSACK and MO).

### 9.6.3 Resource Request
The CPU generates resource requests by executing the MREQ instruction. If MI is Low, the request is granted; otherwise, the CPU must try again. MO is used to signal the request.

## 9.7 Reset
A hardware reset (RESET Low for at least 5 cycles) puts the CPU in a known state. After RESET returns High for 3 cycles, the CPU fetches new program status (FCW and PC) from the Program Status Area to begin execution.

# Appendix B
# Z8000 Family Specifications

## DC Characteristics
T_A = 0°C to +70°C, V_CC = +5V ± 5%

| Symbol | Parameter | Min | Max | Unit |
| :--- | :--- | :--- | :--- | :--- |
| V_IH | Input High Voltage | 2.0 | V_CC + 0.3 | V |
| V_IL | Input Low Voltage | -0.3 | 0.8 | V |
| V_OH | Output High Voltage | 2.4 | | V |
| V_OL | Output Low Voltage | | 0.4 | V |
| I_LI | Input Leakage Current | | ±10 | µA |
| I_LO | Output Leakage Current | | ±10 | µA |
| I_CC | Power Supply Current | | 300 | mA |

## AC Characteristics (Clock Timing)

| Symbol | Parameter | 4 MHz Min | 4 MHz Max | 6 MHz Min | 6 MHz Max |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T_c | Clock Cycle Time | 250 | 2000 | 165 | 2000 |
| T_wCh | Clock High Width | 105 | | 75 | |
| T_wCl | Clock Low Width | 105 | | 75 | |
| T_rC | Clock Rise Time | | 30 | | 20 |
| T_fC | Clock Fall Time | | 30 | | 20 |

## Bus Timing Summary

| Symbol | Parameter | 4 MHz Min | 4 MHz Max |
| :--- | :--- | :--- | :--- |
| T_dA(AS) | Address to AS Rise Delay | 50 | |
| T_dAS(A) | AS Rise to Address Inactive | 40 | |
| T_wAS | Address Strobe Width | 80 | |
| T_dAS(DS) | AS Rise to DS Fall Delay | 100 | |
| T_wDS | Data Strobe Width | 230 | |
| T_dDS(D) | DS Fall to Read Data Valid | | 175 |
| T_hD(DS) | Read Data Hold after DS Rise | 0 | |
| T_dD(DS) | Write Data to DS Fall Setup | 50 | |
| T_hDS(D) | Write Data Hold after DS Rise | 50 | |

| Mnemonics | Operands | Addr. Modes | Word/Byte Cycles (NS/SS/SL) | Long Word Cycles | Operation | Flags (C Z S V D H) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CPD** | Rx,src,Ry,cc | IR | 20 / 20 / 20 | - | Comp & Decr | U * U * - - |
| **CPDR** | | IR | 11+9n | - | Repeat Version | U * U * - - |
| **CPI** | Rx,src,Ry,cc | IR | 20 / 20 / 20 | - | Comp & Incr | U * U * - - |
| **CPIR** | | IR | 11+9n | - | Repeat Version | U * U * - - |
| **CPSD** | dst,src,R,cc | IR | 25 / 25 / 25 | - | String Comp Decr | C * S V - - |
| **CPSDR** | | IR | 11+14n | - | Repeat Version | C * S V - - |
| **CPSI** | dst,src,R,cc | IR | 25 / 25 / 25 | - | String Comp Incr | C * S V - - |
| **CPSIR** | | IR | 11+14n | - | Repeat Version | C * S V - - |
| **DAB** | dst | R | 5 / 5 / 5 | - | Decimal Adjust | C Z S - - - |
| **DEC** | dst, n | R | 4 / 4 / 4 | - | Decrement | - Z S V - - |
| **DECB** | | IR | 11 / 11 / 11 | - | (n = 1..16) | |
| | | DA | 13 / 14 / 16 | - | | |
| | | X | 14 / 14 / 17 | - | | |
| **DI** | int | - | 7 / 7 / 7 | - | Disable Interrupt | - - - - - - |
| **DIV** | R, src | R | 107 / 107 / 107 | 744 / 744 / 744 | Signed Divide | C Z S V - - |
| **DIVL** | | IM | 107 / 107 / 107 | 744 / 744 / 744 | | |
| | | IR | 107 / 107 / 107 | 744 / 744 / 744 | | |
| | | DA | 108 / 109 / 111 | 745 / 746 / 748 | | |
| | | X | 109 / 110 / 112 | 746 / 746 / 749 | | |
| **DJNZ** | R, dst | RA | 11 / 11 / 11 | - | Decr & Jump NZ | - - - - - - |
| **DBJNZ** | | | | | | |
| **EI** | int | - | 7 / 7 / 7 | - | Enable Interrupt | - - - - - - |
| **EX** | R, src | R | 6 / 6 / 6 | - | Exchange | - - - - - - |
| **EXB** | | IR | 12 / 12 / 12 | - | | |
| | | DA | 15 / 16 / 18 | - | | |
| | | X | 16 / 16 / 19 | - | | |

| Mnemonics | Operands | Addr. Modes | Word/Byte Cycles (NS/SS/SL) | Long Word Cycles (NS/SS/SL) | Operation | Flags (C Z S V D H) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EXTS** | dst | R | 11 / 11 / 11 | 11 / 11 / 11 | Extend Sign | - - - - - - |
| **EXTSB** | | | | | | |
| **EXTSL** | | | | | | |
| **HALT** | - | - | (8 + 3n) | - | HALT | - - - - - - |
| **IN** | R, src | IR | 10 / 10 / 10 | - | Input | - - - - - - |
| **INB** | | DA | 12 / 12 / 12 | - | | |
| **INC** | dst, n | R | 4 / 4 / 4 | - | Increment | - Z S V - - |
| **INCB** | | IR | 11 / 11 / 11 | - | (n = 1..16) | |
| | | DA | 13 / 14 / 16 | - | | |
| | | X | 14 / 14 / 17 | - | | |
| **IND** | dst,src,R | IR | 21 / 21 / 21 | - | Input & Decr | - U - V - - |
| **INDB** | | | | | | |
| **INDR** | dst,src,R | IR | (11 + 10n) | - | Input Decr Rep | - U - V - - |
| **INDRB** | | | | | | |
| **INI** | dst,src,R | IR | 21 / 21 / 21 | - | Input & Incr | - U - V - - |
| **INIB** | | | | | | |
| **INIR** | dst,src,R | IR | (11 + 10n) | - | Input Incr Rep | - U - V - - |
| **INIRB** | | | | | | |
| **IRET** | - | - | 13 / 16 / 16 | - | Interrupt Return| * * * * * * |
| **JP** | cc, dst | IR | 10 / 15 / 15 | - | Jump (Taken) | - - - - - - |
| | | IR | 7 / 7 / 7 | - | (Not Taken) | |
| | | DA | 7 / 8 / 10 | - | (Taken) | |
| | | DA | 7 / 8 / 10 | - | (Not Taken) | |
| | | X | 8 / 8 / 11 | - | (Taken) | |
| | | X | 8 / 8 / 11 | - | (Not Taken) | |
| **JR** | cc, dst | RA | 6 / 6 / 6 | - | Jump Rel | - - - - - - |
| **LD** | R, src | R | 3 / 3 / 3 | 5 / 5 / 5 | Load Register | - - - - - - |
| **LDB** | | IM | 7 / 7 / 7 | 11 / 11 / 11 | | |
| **LDL** | | IR | 7 / 7 / 7 | 11 / 11 / 11 | | |
| | | DA | 9 / 10 / 12 | 12 / 13 / 15 | | |
| | | X | 10 / 10 / 13 | 13 / 13 / 16 | | |
| | | BA | 14 / 14 / 14 | 17 / 17 / 17 | | |
| | | BX | 14 / 14 / 14 | 17 / 17 / 17 | | |
| **LD** | dst, R | IR | 8 / 8 / 8 | 11 / 11 / 11 | Store to Memory| - - - - - - |
| **LDB** | | DA | 11 / 12 / 14 | 14 / 15 / 17 | | |
| **LDL** | | X | 12 / 12 / 15 | 15 / 15 / 18 | | |
| | | BA | 14 / 14 / 14 | 17 / 17 / 17 | | |
| | | BX | 14 / 14 / 14 | 17 / 17 / 17 | | |
| **LD** | dst, IM | IR | 11 / 11 / 11 | - | Store Imm | - - - - - - |
| **LDB** | | DA | 14 / 15 / 17 | - | | |
| | | X | 15 / 15 / 18 | - | | |
| **LDA** | R, src | DA | 12 / 13 / 15 | - | Load Address | - - - - - - |
| | | X | 13 / 13 / 16 | - | | |
| | | BA | 15 / 15 / 15 | - | | |
| | | BX | 15 / 15 / 15 | - | | |
| **LDAR** | R, src | RA | 15 / 15 / 15 | - | Load Addr Rel | - - - - - - |
| **LDCTL** | dst, src | R | 7 / 7 / 7 | - | Load Control Reg| * * * * * * |
| **LDCTLB** | dst, src | R | 7 / 7 / 7 | - | Load Control B | * * * * - - |
| **LDD** | dst,src,R | IR | 20 / 20 / 20 | - | Load & Decr | - U - V - - |
| **LDDB** | | | | | | |
| **LDDR** | dst,src,R | IR | (11 + 9n) | - | Load Decr Rep | - U - V - - |
| **LDDRB** | | | | | | |
| **LDI** | dst,src,R | IR | 20 / 20 / 20 | - | Load & Incr | - U - V - - |
| **LDIB** | | | | | | |
| **LDIR** | dst,src,R | IR | (11 + 9n) | - | Load Incr Rep | - U - V - - |
| **LDIRB** | | | | | | |
| **LDK** | R, src | IM | 5 / 5 / 5 | - | Load Constant | - - - - - - |
| **LDM** | R, src, n | IR | 11+3n | - | Load Multiple | - - - - - - |
| | | DA | 14+3n / 15+3n / 17+3n | - | | |
| | | X | 15+3n / 15+3n / 18+3n | - | | |
| **LDM** | dst, R, n | IR | 11+3n | - | Store Multiple | - - - - - - |
| | | DA | 14+3n / 15+3n / 17+3n | - | | |
| | | X | 15+3n / 15+3n / 18+3n | - | | |

# Appendix D
# Glossary of Terms

**address:** An entity that specifies one particular element in a set of similar elements. May be either a memory address or an I/O address (q.q.v). (See also segmented address, logical address, physical address.)

**address space:** A set of addresses. The Z8000 can access eight separate address spaces: normal-mode program memory space, system-mode program memory space, normal-mode data memory space, system-mode data memory space, normal-mode stack memory space, system-mode stack memory space, standard I/O space, and special I/O space.

**addressing mode:** The way in which the address of an operand (q.v.) is specified. There are eight addressing modes: Register, Immediate, Indirect Register, Direct Address, Index, Base Address, Relative Address, Base Index (q.q.v).

**autodecrement:** The contents of a register are decremented and then used as specified by the instruction.

**autoincrement:** The contents of a register are used as specified by the instruction and then incremented.

**Base address (BA) addressing mode:** A based address consists of a register that contains the base and a 16-bit displacement (q.v.). The displacement is added to the base and the resulting address indicates the effective address (q.v.).

**Base Index (BX) addressing mode:** Based Indexed addressing is similar to Based addressing except that the displacement ("index"), as well as the base, is held in a register.

**BCD digit:** A Binary Coded Decimal digit is an encoding of the ten decimal digits into a 4-bit code that is simply the first ten binary numbers in the binary number system (starting with 0).

**bus:** A group of signal lines, which connects the devices in a system.

**Bus-Disconnect state:** The CPU state during which the CPU is not the bus master and may not initiate transactions (q.v.) on the bus.

**bus master:** The device in control of the bus. Must be a device that is able to initiate transactions.

**bus request:** A request for control of the bus.

**byte:** A byte is eight contiguous bits; a byte in memory starts on an addressable byte boundary.

**byte register:** An 8-bit register. The Z8000 CPU contains 16 general-purpose byte registers, designated RLn and RHn (n = 0-7).

**clock cycle:** One cycle of the CPU clock, beginning with a rising edge.

**condition:** An event detected by the hardware and indicated by setting the appropriate flag. A condition is caused by the execution of an instruction and is always reproducible.

**context switching:** Interrupting the activity in progress and switching to another activity. A context switch involves saving for later restoration the contents of the general-purpose registers, the Program Counter and the Flag and Control Word (q.v.).

**CPU state:** Either Running state, Stop/Refresh state, or Bus-Disconnect state (q.q.v.).

**data memory address space:** A memory address space (q.v.) that is identified by the status codes 1000 or 1010.

**data structure:** A logical organization of primitive elements (e.g. byte or word) whose format and access conventions are well-defined. Examples of data structures are tables, lists and arrays.

**data type:** The way in which bits are grouped and interpreted. For an instruction, the data type of an operand determines its size and the significance of its bits.

**Direct Address (DA) addressing mode:** In this mode, the operand address is contained within the instruction.

**displacement:** A number contained in the instruction for use in calculating the effective address (q.v.) of an operand.

**DMA:** Direct Memory Access is a method for transferring data to or from main memory at high speed by avoiding the CPU registers.

**effective address:** The address obtained after indirect or indexing modification. In systems with memory management, the effective address is the logical address which must be translated to obtain the physical memory address.

**flags:** Bits in the Flag and Control Word (q.v.) that indicate conditions (q.v.).

**Flag and Control Word:** One of the two Program Status registers; it contains flags (q.v.) and bits that control the operation of the CPU.

**Immediate (IM) addressing mode:** In this mode, the operand is contained within the instruction.

**Index (X) addressing mode:** In this mode, the operand address is obtained by adding the contents of an index register (q.v.) to a base address contained in the instruction.

**index register:** A word register used to contain a displacement for use in effective address calculation.

**Indirect Register (IR) addressing mode:** In this mode, the operand address is contained within a register.

**instruction fetch:** An access to program memory address space (q.v.).

**interrupt request:** An event other than a trap or jump or call instruction that changes the normal flow of instruction execution.

**interrupt service routine:** The routine executed in response to an interrupt.

**interrupt/trap acknowledge transaction:** The transaction initiated by the CPU in response to an interrupt or trap. Obtains an identifier word from the interrupting device.

**I/O address:** The address of an I/O port, always 16 bits long.

**I/O transaction:** A transaction that transfers data to or from a peripheral device or memory management hardware.

**logical address:** The address manipulated by the programmer, used by instructions and output by the Z8000.

**long word:** A long word is 32 contiguous bits; a long word in memory starts on an even addressable byte boundary.

**machine cycle:** One basic CPU operation, starting with a bus transaction (q.v.).

**memory address:** An address specifying a location in memory.

**memory management:** The process of translating logical addresses into physical addresses (q.q.v.), plus certain protection functions.

**memory transactions:** A transaction that transfers data to or from main memory.

**normal mode:** A Running-state (q.v.) mode in which the S/N flag in the FCW is 0 and the N/S line is High. In this mode, the CPU may not execute privileged instructions (q.v.).

**non-maskable interrupts:** Interrupts (q.v.) which cannot be disabled.

**nonsegmented mode:** A Running-state mode of the Z8000 CPUs. In this mode, all addresses are generated with the same segment number.

**non-vectored interrupts:** Interrupts (q.v.) which do not use the identifier word as a vector to an interrupt service routine.

**offset:** In a Z8001 CPU, the 16-bit value that appears on the AD lines when an address is generated.

**operand:** An item of data operated on by an instruction.

**physical address:** The address required for accessing the memory, obtained from the logical address generated by the Z8000 by memory management hardware.

**privileged instruction:** An instruction intended for use primarily by an operating system, which can be executed only in System mode.

**Program Counter (PC):** One of the two Program Status registers (q.v.). Contains the address of the current instruction.

**program memory address space:** The memory address space (q.v.) indicated by the status codes (1100 or 1101).

**Program Status Area:** The area in memory reserved for the starting program status of the interrupt and trap service routines.

**Program Status Area Pointer:** The register that contains the starting address of the Program Status Area.

**Program Status registers:** The two registers (PC and FCW) that contain the program status.

**refresh counter:** A register that controls the Z8000 dynamic memory, periodic-refresh mechanism.

**refresh cycle:** A type of transaction used to refresh dynamic memory. It is three clock cycles long.

**Refresh/Stop state:** A CPU state entered whenever the STOP line is asserted. A continuous stream of refresh cycles (q.v.) is generated.

**register:** A storage location in hardware logic other than the memory.

**Register (R) addressing mode:** In this mode, the operand is in a general-purpose register.

**register pair:** One of eight pairs of general-purpose word registers, designated RRn (n = 0,2,4, ... , 14).

**register quad:** One of four groups of four word registers, designated RQn (n = 0, 4, 8, 12).

**Relative Address (RA) addressing mode:** In this mode, the operand address is calculated by adding a displacement found in the instruction to the current PC value.

**request:** Either an interrupt request, bus request, resource request, or STOP request (qq.v.).

**reset:** An internal CPU operation that initializes the Program Status registers. It is activated by the RESET line.

**Running state:** One of the three CPU states. In this state, the CPU is fetching and executing instructions or handling interrupts.

**segment:** In a Z8001, a set of adjacent memory addresses (up to 64K) with the same segment number (q.v.).

**segment number:** A number specifying a memory segment (q.v.). Part of a segmented address (q.v.).

**segmented address:** In segmented Z8000 CPUs, a 23-bit value consisting of a 7-bit segment number (q.v.) and a 16-bit offset (q.v.).

**segmented mode:** One of the Running-state modes of the segmented Z8001 CPU.

**Special I/O address space:** An I/O address space (q.v.) that is identified by the status code 0011.

**stack:** A data structure used for temporary storage or for procedure and interrupt service routine linkages. A stack uses the last-in, first-out concept.

**stack memory address space:** A memory address space (q.v.) that is identified by the status codes 1001 and 1011.

**stack pointer:** A general-purpose register indicating the top (lowest address) of a stack.

**Standard I/O address space:** An I/O address space (q.v.) that is identified by the status code 0010.

**status code:** A 4-bit encoding of the CPU's current transaction.

**status flags:** Status flags are set according to the outcome of certain instructions to direct the subsequent flow of the program as necessary. There are six status flags: Carry, Zero, Sign, Parity/Overflow, Decimal Adjust and Half Carry.

**status lines:** The lines ST0-ST3, which contain the status code during transactions.

**stop request:** A request that is made by activating the STOP line.

**Stop/Refresh state:** See Refresh/Stop state.

**system mode:** A Running-state mode (q.v.) in which the S/N flag in the FCW is 1 and the N/S line is Low.

**transaction:** One of the basic bus operations. A transaction lasts three or more clock cycles and covers a single data movement on the bus.

**trap:** A condition that occurs at the end of an instruction that caused an illegal operation. The 28000 traps are internal traps (system call, privileged instructions) or external traps (segmentation violation).

**vectored interrupts:** Interrupts (q.v.) which use the identifier word as a vector to the interrupt service routine (q.v.).

**WAIT cycle:** A clock cycle during which the WAIT line is active. Used to prolong transactions.

**word:** Two contiguous bytes (16 bits) starting on an even addressable byte boundary.

**word register:** A 16-bit register.