# This file is part of Rubber and thus covered by the GPL
# (c) Emmanuel Beffara, 2008
"""
Support for nomenclatures with package 'nomencl'.

This module simply wraps the functionality of the 'index' module with default
values for the 'nomencl' package.
"""

import rubber.index
import rubber.module_interface

class Module (rubber.module_interface.Module):

    def __init__ (self, document, opt):
        self.dep = rubber.index.Index (document, 'nlo', 'nls', 'ilg')
        self.dep.style = 'nomencl.ist'
