#!/usr/bin/env python

"""
Operator definitions.

Copyright (C) 2005, 2006 Paul Boddie <paul@boddie.org.uk>

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

import compiler

# Classes.

class Op:

    "Special comparison operator node."

    def __init__(self, left, op, right, filename):

        """
        Initialise the node with the 'left' hand side expression, operator 'op',
        and the 'right' hand side expression. The additional 'filename'
        parameter is used primarily for debugging purposes.
        """

        self.left = left
        self.op = op
        self.right = right

        self.filename = filename
        self._contexts = {}

        # NOTE: The results of the following call are not completely defined.
        # See below for the accessor function and table.

        self.left_method_name, self.right_method_name = get_comparison_methods(op)

        # Useful information.

        self.lineno = self.left.lineno

    def __repr__(self):
        return "Op(%s, '%s', %s)" % (self.left, self.op, self.right)

# Tables and constants.

binary_methods = {
    # left, right operators
    compiler.ast.Add : ("__add__", "__radd__"),
    compiler.ast.Div : ("__div__", "__rdiv__"),
    compiler.ast.LeftShift : ("__lshift__", "__rlshift__"),
    compiler.ast.Mod : ("__mod__", "__rmod__"),
    compiler.ast.Mul : ("__mul__", "__rmul__"),
    compiler.ast.Power : ("__pow__", "__rpow__"),
    compiler.ast.RightShift : ("__rshift__", "__rrshift__"),
    compiler.ast.Sub : ("__sub__", "__rsub__"),
    }

list_methods = {
    # nodes operators (binary)
    compiler.ast.Bitand : ("__and__", "__rand__"),
    compiler.ast.Bitor : ("__or__", "__ror__"),
    compiler.ast.Bitxor : ("__xor__", "__rxor__"),
    }

unary_method = {
    # expr operators (unary)
    compiler.ast.Invert : "__invert__",
    compiler.ast.UnaryAdd : "__pos__",
    compiler.ast.UnarySub : "__neg__",
    }

comparison_methods = {
    "<" : ("__lt__", "__gt__"),
    "<=" : ("__le__", "__ge__"),
    ">" : ("__gt__", "__lt__"),
    ">=" : ("__ge__", "__le__"),
    "==" : ("__eq__", "__eq__"),
    "!=" : ("__ne__", "__ne__"),
    "in" : ("__contains__", None),
    "is" : (None, None),
    "is not" : (None, None),
    }

augmented_methods = {
    "+=" : "__iadd__",
    "-=" : "__isub__",
    "*=" : "__imul__",
    "/=" : "__idiv__",
    # NOTE: Any others?
    }

def is_binary_operator(node):
    return node.__class__ in binary_methods.keys()

def is_list_operator(node):
    return node.__class__ in list_methods.keys()

def is_unary_operator(node):
    return node.__class__ in unary_method.keys()

def is_sequence_operator(node):
    return isinstance(node, compiler.ast.Slice) or isinstance(node, compiler.ast.Subscript)

def get_binary_methods(operator):
    return binary_methods[operator.__class__]

def get_list_methods(operator):
    return list_methods[operator.__class__]

def get_unary_method(operator):
    return unary_method[operator.__class__]

def get_comparison_methods(operator_name):
    return comparison_methods[operator_name]

# vim: tabstop=4 expandtab shiftwidth=4
