#!/usr/bin/python3
# EMACS settings: -*-  tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:               Thomas B. Preusser
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
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# distributed under the License is distributed on an "AS IS" BASIS,default
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""
[http://stackoverflow.com/questions/18673694/referencing-current-branch-in-github-readme-md]

Referencing current branch in github readme.md[1]

This pre-commit hook[2] updates the README.md file's
Travis badge with the current branch. Gist at[4].

[1] http://stackoverflow.com/questions/18673694/referencing-current-branch-in-github-readme-md
[2] http://www.git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
[3] https://docs.travis-ci.com/user/status-images/
[4] https://gist.github.com/dandye/dfe0870a6a1151c89ed9
"""
from subprocess import check_output, check_call
import os

# Collecting values to substitute
substitutions = {}
substitutions["BRANCH"] = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], universal_newlines=True).strip()
substitutions["GENERATED_HEADER"] = '<!--- DO NOT EDIT! This file is generated from .tpl --->'

# Patch templates .tpl to generate specialized .md files
git_root  = check_output(['git', 'rev-parse', '--show-toplevel'], universal_newlines=True).strip()
for root, dirs, files in os.walk(git_root):
	for file in files:
		if file.endswith('.tpl'):
			trgt = file[:-3]+'md'
			print('  generate ' + file + ' -> ' + trgt);
			tpl = open(os.path.join(root, file), 'r', encoding='utf-8')
			md  = open(os.path.join(root, trgt), 'w', encoding='utf-8')
			for line in tpl:
				for key in substitutions:
					line = line.replace('{@'+key+'@}', substitutions[key])
				md.write(line)
			md .close()
			tpl.close()
			check_call(['git', 'add', trgt ])
