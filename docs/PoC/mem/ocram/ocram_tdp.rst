
ocram_tdp
#########

Inferring / instantiating true dual-port memory, with:

* dual clock, clock enable,
* 2 read/write ports.

Command truth table for port 1, same applies to port 2:

=== === ================
ce1 we1 Command
=== === ================
0   X   No operation
1   0   Read from memory
1   1   Write to memory
=== === ================

The generalized behavior across Altera and Xilinx FPGAs since
Stratix/Cyclone and Spartan-3/Virtex-5, respectively, is as follows:

Same-Port Read-During-Write
  When writing data through port 1, the read output of the same port
  (``q1``) will output the new data (``d1``, in the following clock cycle)
  which is aka. "write-first behavior". This behavior also applies to Altera
  M20K memory blocks as described in the Altera: "Stratix 5 Device Handbook"
  (S5-5V1). The documentation in the Altera: "Embedded Memory User Guide"
  (UG-01068) is wrong.

  Same applies to port 2.

Mixed-Port Read-During-Write
  When reading at the write address, the read value will be unknown which is
  aka. "don't care behavior". This applies to all reads (at the same
  address) which are issued during the write-cycle time, which starts at the
  rising-edge of the write clock and (in the worst case) extends
  until the next rising-edge of that write clock.

.. WARNING::
   The simulated behavior on RT-level is too optimistic. When reading
   at the write address always the new data will be returned.

.. TODO:: Implement correct behavior for RT-level simulation.



.. rubric:: Entity Declaration:

.. literalinclude:: ../../../../src/mem/ocram/ocram_tdp.vhdl
   :language: vhdl
   :tab-width: 2
   :linenos:
   :lines: 84-104

Source file: `mem/ocram/ocram_tdp.vhdl <https://github.com/VLSI-EDA/PoC/blob/master/src/mem/ocram/ocram_tdp.vhdl>`_



