# This file is part of Rubber and thus covered by the GPL
# (c) Emmanuel Beffara, 2002--2006
# vim: noet:ts=4
"""
This module contains the code for
the class Environment, which contains all information about a given
building process.
"""

import os, os.path, sys, subprocess
import re

from rubber.util import _, msg, prog_available
import rubber.converters
import rubber.depend
from rubber.convert import Converter

class Environment:
	"""
	This class contains all state information related to the building process
	for a whole document, the dependency graph and conversion rules.
	"""
	def __init__ (self):
		"""
		Initialize the environment. The optional argument is the path to the
		reference directory for compilation, by default it is the current
		working directory.
		"""
		self.path = [os.getcwd ()]
		self.conv_prefs = {}

		# Represents a set of dependency nodes. Nodes can be accessed by absolute
		# path name using the dictionary interface.
		self.depends = dict()
		self.converter = Converter (self)
		self.converter.read_ini (os.path.join (rubber.__path__[0], 'rules.ini'))

		self.doc_requires_shell_ = False
		self.synctex = False
		self.main = None
		self.final = None
		self.graphics_suffixes = []

	def find_file (self, name, suffix=None):
		"""
		Look for a source file with the given name, and return either the
		complete path to the actual file or None if the file is not found.
		The optional argument is a suffix that may be added to the name.
		"""
		for path in self.path:
			test = os.path.join(path, name)
			if suffix and os.path.exists(test + suffix) and os.path.isfile(test + suffix):
				return test + suffix
			elif os.path.exists(test) and os.path.isfile(test):
				return test
		return None

	def conv_set (self, file, vars):
		"""
		Define preferences for the generation of a given file. The argument
		'file' is the name of the target and the argument 'vars' is a
		dictionary that contains imposed values for some variables.
		"""
		self.conv_prefs[file] = vars

	def convert (self, target, prefixes=[""], suffixes=[""], check=None, context=None):
		"""
		Use conversion rules to make a dependency tree for a given target
		file, and return the final node, or None if the file does not exist
		and cannot be built. The optional arguments 'prefixes' and 'suffixes'
		are lists of strings that can be added at the beginning and the end of
		the name when searching for the file. Prefixes are tried in order, and
		for each prefix, suffixes are tried in order; the first file from this
		order that exists or can be made is kept. The optional arguments
		'check' and 'context' have the same meaning as in
		'Converter.best_rule'.
		"""
		# Try all suffixes and prefixes until something is found.

		last = None
		for t in [p + target + s for s in suffixes for p in prefixes]:

			# Define a check function, according to preferences.

			if t in self.conv_prefs:
				prefs = self.conv_prefs[t]
				def do_check (vars, prefs=prefs):
					if prefs is not None:
						for key, val in prefs.items():
							if not (key in vars and vars[key] == val):
								return 0
					return 1
			else:
				prefs = None
				do_check = check

			# Find the best applicable rule.

			ans = self.converter.best_rule(t, check=do_check, context=context)
			if ans is not None:
				if last is None or ans["cost"] < last["cost"]:
					last = ans

			# Check if the target exists.

			if prefs is None and os.path.exists(t):
				if last is not None and last["cost"] <= 0:
					break
				msg.log(_("`%s' is `%s', no rule applied") % (target, t))
				return rubber.depend.Leaf(self.depends, t)

		if last is None:
			return None
		msg.log(_("`%s' is `%s', made from `%s' by rule `%s'") %
				(target, last["target"], last["source"], last["name"]))
		return self.converter.apply(last)

	def may_produce (self, name):
		"""
		Return true if the given filename may be that of a file generated by
		any of the converters.
		"""
		return self.converter.may_produce(name)

	def execute (self, prog, env={}, pwd=None, out=None):
		"""
		Silently execute an external program. The `prog' argument is the list
		of arguments for the program, `prog[0]' is the program name. The `env'
		argument is a dictionary with definitions that should be added to the
		environment when running the program. The standard output is passed
		line by line to the `out' function (or discarded by default).
		"""
		msg.info(_("executing: %s") % " ".join (prog))
		if pwd:
			msg.log(_("  in directory %s") % pwd)
		if env != {}:
			msg.log(_("  with environment: %r") % env)

		progname = prog_available(prog[0])
		if not progname:
			msg.error(_("%s not found") % prog[0])
			return 1

		penv = os.environ.copy()
		for (key,val) in env.items():
			penv[key] = val

		process = subprocess.Popen(prog,
			executable = progname,
			env = penv,
			cwd = pwd,
			stdin = subprocess.DEVNULL,
			stdout = subprocess.PIPE,
			stderr = None)

		if out is not None:
			for line in process.stdout:
				out(line)
		else:
			process.stdout.readlines()

		ret = process.wait()
		msg.log(_("process %d (%s) returned %d") % (process.pid, prog[0],ret))
		return ret
