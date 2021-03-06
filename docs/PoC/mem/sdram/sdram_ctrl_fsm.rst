
sdram_ctrl_fsm
##############

This file contains the FSM as well as parts of the datapath.
The board specific physical layer is defined in another file
sdram_ctrl_phy_*.vhdl

Generics:
---------
SDRAM_TYPE activates some special cases:
- 0 for SDR-SDRAM
- 1 for DDR-SDRAM
- 2 for DDR2-SDRAM (no special support yet like ODT)

2**A_BITS specifies the number of memory cells in the SDRAM. This is the
size of th memory in bits divided by the native data-path width of the SDRAM
(also in bits).

D_BITS is the native data-path width of the SDRAM. The width might be doubled
by the physical interface for DDR interfaces.

Furthermore, the memory array is divided into
2**R_BITS rows, 2**C_BITS columns and 2**B_BITS banks.

For example, the MT46V32M16 has 512 Mbit = 8M x 4 banks x 16 bit =
32M cells x 16 bit, with 8K rows and 1K columns.
- A_BITS = log2ceil(32M) = 25
- D_BITS = 16
- data-path width of phy on user side: 32-bit because of DDR
- R_BITS = log2ceil(8K)  = 13
- C_BITS = log2ceil(1K)  = 10
- B_BITS = log2ceil(4)   =  2

Set cas latency (CL, MR_CL) and  burst length (BL, MR_BL) according to
your needs.

If you have a DDR-SDRAM then set INIT_DLL = true, otherwise false.

The definition and values of generics T_* can be calculated from the
datasheets of the specific SDRAM (e.g. MT46V). Just divide the
minimum/maximum times by clock period.
Auto refreshs are applied periodically, the datasheet either specifies the
average refresh interval (T_REFI) or the total refresh cycle time (T_REF).
In the latter case, divide the total time by the row count to get the
average refresh interval. Substract about 50 clock cycles to
account for pending read/writes.

INIT_WAIT specifies the time period to wait after the SDRAM is powered up.
It is typically 100--200 us long, see datasheet. The waiting time is
specified in number of average refresh periods (specified by T_REFI):
INIT_WAIT = ceil(wait_time / clock_period / T_REFI)
e.g. INIT_WAIT = ceil(200 us / 10 ns / 700) = 29

Signals:
--------

After user_cmd_valid is asserted high, the command (user_write) and address
(user_addr) must be hold until user_got_cmd is asserted.

The FSM automatically waits for user_wdata_valid on writes. The data should
be available soon. Otherwise the auto refresh might fail. The FSM only waits
for the first word to write. All successive words of a burst must be valid
in the following cycles. (A burst can't be stalled.) ATTENTION: During
writes, user_cmd_got is asserted only if user_wdata_valid is set.

The write data must directly connected to the physical layer.



.. rubric:: Entity Declaration:

.. literalinclude:: ../../../../src/mem/sdram/sdram_ctrl_fsm.vhdl
   :language: vhdl
   :tab-width: 2
   :linenos:
   :lines: 120-164

Source file: `mem/sdram/sdram_ctrl_fsm.vhdl <https://github.com/VLSI-EDA/PoC/blob/master/src/mem/sdram/sdram_ctrl_fsm.vhdl>`_



