-- EMACS settings: -*-  tab-width: 2; indent-tabs-mode: t -*-
-- vim: tabstop=2:shiftwidth=2:noexpandtab
-- kate: tab-width 2; replace-tabs off; indent-width 2;
-- =============================================================================
-- Authors:				 	Patrick Lehmann
--
-- Entity:				 	XADC wrapper for temperature supervision applications
--
-- Description:
-- -------------------------------------
-- This module wraps a Series-7 XADC to report if preconfigured temperature values
-- are overrun. The XADC was formerly known as "System Monitor".
--
-- .. rubric:: Temperature Curve
--
-- .. code-block:: none
--
--                    |                      /-----\
--    Temp_ov   on=80 | - - - - - - /-------/       \
--                    |            /        |        \
--    Temp_ov  off=60 | - - - - - / - - - - | - - - - \----\
--                    |          /          |              |\
--                    |         /           |              | \
--    Temp_us   on=35 | -  /---/            |              |  \
--    Temp_us  off=30 | - / - -|- - - - - - |- - - - - - - |- -\------\
--                    |  /     |            |              |           \
--    ----------------|--------|------------|--------------|-----------|--------
--    pwm =           |   min  |  medium    |   max        |   medium  |  min
--
-- License:
-- =============================================================================
-- Copyright 2007-2015 Technische Universitaet Dresden - Germany
--										 Chair for VLSI-Design, Diagnostics and Architecture
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--		http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
-- =============================================================================

library IEEE;
use			IEEE.STD_LOGIC_1164.all;
use			IEEE.NUMERIC_STD.all;

library	UniSim;
use			UniSim.vComponents.all;


entity xil_SystemMonitor_Series7 is
	port (
		Reset								: in	std_logic;				-- Reset signal for the System Monitor control logic

		Alarm_UserTemp			: out	std_logic;				-- Temperature-sensor alarm output
		Alarm_OverTemp			: out	std_logic;				-- Over-Temperature alarm output
		Alarm								: out	std_logic;				-- OR'ed output of all the Alarms
		VP									: in	std_logic;				-- Dedicated Analog Input Pair
		VN									: in	std_logic
	);
end entity;


architecture xilinx of xil_SystemMonitor_Series7 is
	signal FLOAT_VCCAUX_ALARM		: std_logic;
	signal FLOAT_VCCINT_ALARM		: std_logic;
	signal FLOAT_VBRAM_ALARM		: std_logic;
	signal FLOAT_MUXADDR				: std_logic_vector(4 downto 0);
	signal aux_channel_p				: std_logic_vector(15 downto 0);
	signal aux_channel_n				: std_logic_vector(15 downto 0);
	signal XADC_Alarm						: std_logic_vector(7 downto 0);

	begin

	genAUXChannel : for i in 0 to 15 generate
		aux_channel_p(i) <= '0';
		aux_channel_n(i) <= '0';
	end generate;

	SysMonitor : XADC
		generic map (
			INIT_40							=> x"8000",					-- config reg 0
			INIT_41							=> x"8f0c",					-- config reg 1
			INIT_42							=> x"0400",					-- config reg 2
			INIT_48							=> x"0000",					-- Sequencer channel selection
			INIT_49							=> x"0000",					-- Sequencer channel selection
			INIT_4A							=> x"0000",					-- Sequencer Average selection
			INIT_4B							=> x"0000",					-- Sequencer Average selection
			INIT_4C							=> x"0000",					-- Sequencer Bipolar selection
			INIT_4D							=> x"0000",					-- Sequencer Bipolar selection
			INIT_4E							=> x"0000",					-- Sequencer Acq time selection
			INIT_4F							=> x"0000",					-- Sequencer Acq time selection
			INIT_50							=> x"9c87",					-- Temp alarm trigger
			INIT_51							=> x"57e4",					-- Vccint upper alarm limit
			INIT_52							=> x"a147",					-- Vccaux upper alarm limit
			INIT_53							=> x"b363",					-- Temp alarm OT upper
			INIT_54							=> x"99fd",					-- Temp alarm reset
			INIT_55							=> x"52c6",					-- Vccint lower alarm limit
			INIT_56							=> x"9555",					-- Vccaux lower alarm limit
			INIT_57							=> x"a93a",					-- Temp alarm OT reset
			INIT_58							=> x"5999",					-- Vbram upper alarm limit
			INIT_5C							=> x"5111",					-- Vbram lower alarm limit
			SIM_DEVICE					=> "7SERIES",
			SIM_MONITOR_FILE		=> "design.txt"
		)
		port map (
			-- Control and Clock
			RESET								=> Reset,
			CONVSTCLK						=> '0',
			CONVST							=> '0',
			-- DRP port
			DCLK								=> '0',
			DEN									=> '0',
			DADDR								=> "0000000",
			DWE									=> '0',
			DI									=> x"0000",
			DO									=> open,
			DRDY								=> open,
			-- External analog inputs
			VAUXN								=> aux_channel_n(15 downto 0),
			VAUXP								=> aux_channel_p(15 downto 0),
			VN									=> VN,
			VP									=> VP,
			-- Alarms
			OT									=> Alarm_OverTemp,
			ALM									=> XADC_Alarm,
			-- Status
			MUXADDR							=> FLOAT_MUXADDR,
			CHANNEL							=> open,
			BUSY								=> open,
			EOC									=> open,
			EOS									=> open,

			JTAGBUSY						=> open,
			JTAGLOCKED					=> open,
			JTAGMODIFIED				=> open
	 );

	Alarm						<= XADC_Alarm(7);
	Alarm_UserTemp	<= XADC_Alarm(0);
end;
