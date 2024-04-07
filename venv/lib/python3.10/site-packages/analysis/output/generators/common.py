#!/usr/bin/env python

"""
Code generation classes used by the analysis.output.visitor module classes.

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

import sys

class Generator:
    def __init__(self, stream=None):
        self._indent = 0
        self.stream = stream or sys.stdout

    def _ls(self):
        if self._indent > 0:
            self.stream.write(self._indent * " ")

    def indent(self):
        self._indent += 2

    def dedent(self):
        self._indent -= 2

class RawGenerator(Generator):

    def __init__(self, *args):
        Generator.__init__(self, *args)
        self.start = 1

    def write(self, *args):
        if self.start:
            self._ls()
            self.start = 0
        self.stream.write("".join(args))

    def writeln(self, *args):
        if self.start:
            self._ls()
        self.stream.write("".join(args) + "\n")
        self.start = 1

class AbstractGenerator(Generator):

    def start_of_code(self):
        self._ls(); print >>self.stream, "START OF CODE"

    def end_of_code(self):
        self._ls(); print >>self.stream, "END OF CODE"

    def begin_module_header(self, name):
        self._ls(); print >>self.stream, "MODULE", name

    def end_module_header(self, name):
        self._ls(); print >>self.stream, "CODE FOR MODULE", name
        self.indent()

    def end_module(self, name):
        self.dedent()

    def label(self, name):
        self._ls(); print >>self.stream, "LABEL", name

    def comment(self, text):
        self._ls(); print >>self.stream, ";", text

    def var(self, label_name, name):
        self._ls(); print >>self.stream, "LABEL", label_name,
        print >>self.stream, "VAR", repr(name)

    def const(self, label_name, value):
        self._ls(); print >>self.stream, "LABEL", label_name,
        print >>self.stream, "TYPE",
        if type(value) == type(""):
            print >>self.stream, "STRING"
        elif type(value) == type(0):
            print >>self.stream, "INT"
        elif type(value) == type(0L):
            print >>self.stream, "LONG"
        elif type(value) == type(0.0):
            print >>self.stream, "FLOAT"
        else:
            # NOTE: Other types not yet supported.
            raise NotImplementedError, type(value)
        self._ls(); print >>self.stream, "NO REFCOUNT (CONTENT FOLLOWS)"
        self._ls(); print >>self.stream, "CONST", repr(value)

    def begin_call(self):
        self._ls(); print >>self.stream, "BEGIN CALL"
        self.indent()

    def call(self, name):
        self._ls(); print >>self.stream, "CALL", name

    def end_call(self):
        self.dedent()
        self._ls(); print >>self.stream, "END CALL"

    def context(self):
        self._ls(); print >>self.stream, "CONTEXT (from last value)"

    def fname(self):
        self._ls(); print >>self.stream, "FNAME (from last value)"

    def parameter(self):
        self._ls(); print >>self.stream, "PARAMETER (from last value)"

    def begin_function(self, name):
        self._ls(); print >>self.stream, "BEGIN FUNCTION", name

    def end_function(self, name):
        self._ls(); print >>self.stream, "END FUNCTION", name

    def return_(self):
        self._ls(); print >>self.stream, "RETURN (last value)"

    def load_const(self, name):
        self._ls(); print >>self.stream, "LOAD", name

    def load_local(self, qname, name, index):
        self._ls(); print >>self.stream, "LOAD LOCAL", index

    def load_global(self, qname, name, index):
        self._ls(); print >>self.stream, "LOAD GLOBAL", qname, name, index

    def load_attr(self, name, index):
        self._ls(); print >>self.stream, "LOAD %s AT %s" % (name, index)

    def store_local(self, qname, name, index):
        self._ls(); print >>self.stream, "STORE LOCAL", index

    def store_global(self, qname, name, index):
        self._ls(); print >>self.stream, "STORE GLOBAL", qname, name, index

    def store_attr(self, name, index):
        self._ls(); print >>self.stream, "STORE %s AT %s" % (name, index)

    def dup_top(self):
        self._ls(); print >>self.stream, "DUP TOP"

    def swap_top(self):
        self._ls(); print >>self.stream, "SWAP TOP"

    def pop_top(self):
        self._ls(); print >>self.stream, "POP TOP"

    def compare(self, op):
        self._ls(); print >>self.stream, "COMPARE", op

    def jump(self, state, label):
        self._ls(); print >>self.stream, "JUMP",
        if state is not None:
            if state:
                print >>self.stream, "IF TRUE",
            else:
                print >>self.stream, "IF FALSE",
        print >>self.stream, "TO", label

    def new(self, cls, size):
        self._ls(); print >>self.stream, "NEW", cls, "SIZE", size

    def new_function_ref(self, fname):
        self._ls(); print >>self.stream, "NEW FUNCTION REF", fname

    def begin_table(self):
        self._ls(); print >>self.stream, "BEGIN TABLE"
        self.indent()

    def type_of(self):
        self._ls(); print >>self.stream, "TYPE OF"

    def case(self, value):
        self._ls(); print >>self.stream, "CASE", value

    def end_table(self):
        self.dedent()
        self._ls(); print >>self.stream, "END TABLE"

    def list(self, number):
        self._ls(); print >>self.stream, "LIST OF SIZE", number

# vim: tabstop=4 expandtab shiftwidth=4
