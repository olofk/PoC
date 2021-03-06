# EMACS settings: -*-	tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:          Patrick Lehmann
#
# Python Class:     This SynthCompiler compiles VHDL source files to design checkpoints
#
# Description:
# ------------------------------------
#		TODO:
#		-
#		-
#
# License:
# ==============================================================================
# Copyright 2007-2016 Technische Universitaet Dresden - Germany
#                     Chair for VLSI-Design, Diagnostics and Architecture
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
#
# entry point


if __name__ != "__main__":
	# place library initialization code here
	pass
else:
	from lib.Functions import Exit
	Exit.printThisIsNoExecutableFile("The PoC-Library - Python Module Compiler.XSTCompiler")


# load dependencies
from datetime                 import datetime
from pathlib                  import Path

from Base.Project             import ToolChain, Tool, FileTypes
from Base.Compiler            import Compiler as BaseCompiler, CompilerException, SkipableCompilerException, CompileState
from PoC.Entity               import WildCard
from ToolChains.Xilinx.Vivado import Vivado, VivadoException


class Compiler(BaseCompiler):
	_TOOL_CHAIN =  ToolChain.Xilinx_Vivado
	_TOOL =        Tool.Xilinx_Synth

	def __init__(self, host, dryRun, noCleanUp):
		super().__init__(host, dryRun, noCleanUp)

		self._device =      None
		self._toolChain =   None

		configSection = host.PoCConfig['CONFIG.DirectoryNames']
		self.Directories.Working =  host.Directories.Temp / configSection['VivadoSynthesisFiles']
		self.Directories.XSTFiles = host.Directories.Root / configSection['VivadoSynthesisFiles']
		self.Directories.Netlist =  host.Directories.Root / configSection['NetlistFiles']

		self._PrepareCompiler()

	def _PrepareCompiler(self):
		super()._PrepareCompiler()

		vivadoSection =   self.Host.PoCConfig['INSTALL.Xilinx.Vivado']
		binaryPath =      Path(vivadoSection['BinaryDirectory'])
		version =         vivadoSection['Version']
		self._toolChain = Vivado(self.Host.Platform, self.DryRun, binaryPath, version, logger=self.Logger)

	def RunAll(self, fqnList, *args, **kwargs):
		"""Run a list of netlist compilations. Expand wildcards to all selected netlists."""
		self._testSuite.StartTimer()
		self.Logger.BaseIndent = int(len(fqnList) > 1)
		try:
			for fqn in fqnList:
				entity = fqn.Entity
				if (isinstance(entity, WildCard)):
					self.Logger.BaseIndent = 1
					for netlist in entity.GetVivadoNetlists():
						self.TryRun(netlist, *args, **kwargs)
				else:
					netlist = entity.VivadoNetlist
					self.TryRun(netlist, *args, **kwargs)
		except KeyboardInterrupt:
			self.LogError("Received a keyboard interrupt.")
		finally:
			self._testSuite.StopTimer()

		self.PrintOverallCompileReport()

		return self._testSuite.IsAllSuccess

	def Run(self, netlist, board):
		super().Run(netlist, board)

		netlist.TclFile = self.Directories.Working / (netlist.ModuleName + ".tcl")
		self._WriteTclFile(netlist,board.Device)
		self._prepareTime = self._GetTimeDeltaSinceLastEvent()

		self.LogNormal("Executing pre-processing tasks...")
		self._state = CompileState.PreCopy
		self._RunPreCopy(netlist)
		self._state = CompileState.PrePatch
		self._RunPreReplace(netlist)
		self._preTasksTime = self._GetTimeDeltaSinceLastEvent()

		self.LogNormal("Running Xilinx Vivado Synthesis...")
		self._state = CompileState.Compile
		self._RunCompile(netlist)
		self._compileTime = self._GetTimeDeltaSinceLastEvent()

		self.LogNormal("Executing post-processing tasks...")
		self._state = CompileState.PostCopy
		self._RunPostCopy(netlist)
		self._state = CompileState.PostPatch
		self._RunPostReplace(netlist)
		self._state = CompileState.PostDelete
		self._RunPostDelete(netlist)
		self._postTasksTime = self._GetTimeDeltaSinceLastEvent()

		self._endAt = datetime.now()

	def _WriteSpecialSectionIntoConfig(self, device):
		# add the key Device to section SPECIAL at runtime to change interpolation results
		self.Host.PoCConfig['SPECIAL'] = {}
		self.Host.PoCConfig['SPECIAL']['Device'] =        device.FullName
		self.Host.PoCConfig['SPECIAL']['DeviceSeries'] =  device.Series
		self.Host.PoCConfig['SPECIAL']['OutputDir']	=     self.Directories.Working.as_posix()

	def _RunCompile(self, netlist):
		reportFilePath = self.Directories.Working / (netlist.ModuleName + ".log")

		synth = self._toolChain.GetSynthesizer()
		synth.Parameters[synth.SwitchSourceFile] =  netlist.ModuleName + ".tcl"
		synth.Parameters[synth.SwitchLogFile] =     str(reportFilePath)
		try:
			synth.Compile()
		except VivadoException as ex:
			raise CompilerException("Error while compiling '{0!s}'.".format(netlist)) from ex
		if synth.HasErrors:
			raise SkipableCompilerException("Error while compiling '{0!s}'.".format(netlist))

	def _WriteTclFile(self, netlist, device):
		buffer =""
		for file in self.PoCProject.Files(fileType=FileTypes.VHDLSourceFile):
			buffer += "read_vhdl -library {library} {file} \n". \
				format(file=file.Path.as_posix(), library=file.LibraryName)
		for file in self.PoCProject.Files(fileType=FileTypes.VerilogSourceFile):
			buffer += "read_verilog {file} \n". \
				format(file=file.Path.as_posix())

		topLevelGenerics =  ""
		for keyValuePair in self._GetHDLParameters(netlist.ConfigSectionName).items():
			topLevelGenerics += " -generic {{{0}={1}}}".format(*keyValuePair)

		buffer += "synth_design -top {top} -part {part}{TopLevelGenerics}\n".format(
			top=netlist.ModuleName,
			part=device.ShortName,
			TopLevelGenerics=topLevelGenerics
		)
		buffer += "write_checkpoint -noxdef {top}.dcp \n".format(top=netlist.ModuleName)
		buffer += "catch {{ report_utilization -file {top}_synth.rpt -pb {top}_synth.pb }}\n".format(top=netlist.ModuleName)

		self.LogDebug("Writing Vivado TCL file to '{0!s}'".format(netlist.TclFile))
		with netlist.TclFile.open('w') as tclFileHandle:
			tclFileHandle.write(buffer)
