#!/usr/bin/env python

"""
Common AST visitor routines.

Copyright (C) 2005 Paul Boddie <paul@boddie.org.uk>

This software is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of
the License, or (at your option) any later version.

This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public
License along with this library; see the file LICENCE.txt
If not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""

from compiler.visitor import ASTVisitor
import analysis.reference
from analysis.common import has_docstring_annotation

class Visitor(ASTVisitor):

    "A common visitor superclass."

    def __init__(self):
        ASTVisitor.__init__(self)

    def uses_call(self, node):
        return hasattr(node, "_targets") and len(node._targets) != 0

    def is_native(self, node):
        return node.doc is not None and has_docstring_annotation(node, "NATIVE")

    def is_builtin_module(self, node):
        return node._module_name is None

# vim: tabstop=4 expandtab shiftwidth=4
