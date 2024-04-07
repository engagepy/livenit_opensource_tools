#!/usr/bin/env python

"""
A C language visitor.

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

from analysis.output.visitors.common import Visitor
from analysis.output.generators.C import *
from analysis.common import *
import analysis.classes
import analysis.namespace
import analysis.operators
import compiler

# Magic function and type numbers.

class Counter:

    "A special class whose instances provide access to magic number sequences."

    # NOTE: Start from a magic place way beyond the built-in type numbers.
    magic_number = 100
    # NOTE: The series size must be compatible with the isinstance runtime
    # NOTE: function.
    series_size = 256
    series = {}
    def get_number(self, name=None):
        if name is None:
            n = Counter.magic_number
            Counter.magic_number += 1
        else:
            series_base, n = Counter.series[name]
            Counter.series[name] = series_base, n + 1
        return n
    def get_base(self, name):
        return Counter.series[name][0]
    def new_series(self, name):
        series_base, remainder = divmod(Counter.magic_number, Counter.series_size)
        Counter.magic_number = (series_base + 1) * Counter.series_size
        Counter.series[name] = Counter.magic_number, Counter.magic_number

# Visitors.

class CVisitor(Visitor):

    "A simple C-emitting visitor."

    constant_start = 0

    def __init__(self, generator, header_generator, module_names):

        """
        Initialise the visitor with the given 'generator' to which the final
        output is sent. Note that the visitor itself maintains a number of
        generators, controlled internally.

        The specified 'header_generator' is used to accept declarations sent by
        the visitor in order to produce a header file which can be referenced by
        other modules in the same program.

        The 'module_names' consist of the names of the entire set of modules
        used in the program.
        """

        Visitor.__init__(self)

        # Output generators.

        self.generator = generator
        self.header_generator = header_generator

        # Module name information.

        self.module_names = module_names

        # Generators which collect program information.

        self.module_declarations = DeclarationsGenerator(Counter())
        self.module_definitions = DefinitionsGenerator(self.module_declarations, Counter())
        self.function_definitions = DefinitionsGenerator(self.module_declarations, Counter())
        self.header_definitions = CGenerator()

        # The main function for a module is placed in the top-level definitions.

        self.main_body = CodeGenerator(self)
        self.definitions = [self.function_definitions]
        self.function_bodies = [self.main_body]

        # Constant table.

        self.constants = []
        self.constant_values = {}

    # Helper methods.

    def _ltype(self, node):
        names = [cls._qualified_name for cls in ltype(node)]
        if len(names) == 0 and len(lobj(node)) != 0:
            return ["function"]
        else:
            return names

    def in_function(self):
        return self.function_bodies[-1]

    # General node processing.

    def default(self, node):

        """
        Handle a 'node' not explicitly handled elsewhere.
        """

        if analysis.operators.is_binary_operator(node):
            self.process_binary_operator(node)
        elif analysis.operators.is_unary_operator(node):
            self.process_unary_operator(node)
        elif analysis.operators.is_sequence_operator(node):
            self.process_sequence_operator(node)

    # Visitor methods for statements.

    def visitModule(self, node):

        # Certain globals should be declared only once in the built-in
        # declarations.

        if self.is_builtin_module(node):
            self.module_definitions.include("runtime")
            self.module_definitions.writeln()
        else:
            self.module_definitions.include("runtime")
            self.module_definitions.include("builtins")
            self.module_definitions.writeln()

        # Include the top-level code: function declarations and typedefs.

        for module_name in self.module_names:
            self.module_definitions.include(module_name)
            self.module_definitions.writeln()

        self.module_definitions.include(node._module_name or "builtins")
        self.module_definitions.writeln()

        # Specially direct module locals to the top-level generator.

        locals = analysis.namespace.get_locals_layout(node, qualified_names=1, include_parameters=0)
        self.module_definitions.locals(locals, self.is_native(node))

        # Generate the code.

        self.dispatch(node.node)

        # Build a constant table, writing it straight out.

        i = CVisitor.constant_start
        for constant in self.constants:
            type_name = self._ltype(constant)[0]
            self.module_definitions.constant(type_name, i, constant.value)
            i += 1
        CVisitor.constant_start = i

        self.module_definitions.writeln()

        # Generate the main program.

        if not self.is_builtin_module(node):
            self.function_definitions.main_definition(node._module_name or "builtins", self.main_body)
            self.module_declarations.main_declaration(node._module_name or "builtins")

        # Include the module and function definitions.

        self.generator.write(self.module_definitions.get_output())
        self.generator.write(self.function_definitions.get_output())

        # Generate separate headers, if requested.

        self.header_definitions.start_guard(node._module_name or "builtins")
        self.header_definitions.writeln()
        self.header_definitions.include("runtime")
        self.header_definitions.writeln()

        # Include the top-level code: function declarations and typedefs.

        self.header_definitions.write(self.module_declarations.get_output())

        self.header_definitions.writeln()
        self.header_definitions.end_guard(node._module_name or "builtins")

        if self.header_generator is not None:
            self.header_generator.write(self.header_definitions.get_output())

    def visitImport(self, node):

        # Generate include directives.

        for _name in node._names:
            self.module_definitions.include(_name.module_name)
            self.module_definitions.module_definition((node._module_name or "builtins") + "." + _name.module_name)

            # Add an invocation of any initialisation section (main program) in the
            # imported module.

            self.main_body.import_module(_name.module_name)

    def visitClass(self, node):

        locals = analysis.namespace.get_locals_layout(node, qualified_names=1, include_parameters=0)
        self.function_definitions.locals(locals, self.is_native(node))

        # Do not write the attributes out where the class is defined as being
        # native.

        if not self.is_native(node):

            # First define the instance structure, if appropriate.

            for instance in getattr(node, "_instances", []):
                self.module_declarations.object_declaration(
                    instance._qualified_name,
                    analysis.classes.get_instance_layout(node).keys()
                    )
                # NOTE: This was only useful when more than one reference could
                # NOTE: exist per class.
                #self.module_declarations.object_type_declaration(instance._qualified_name)
                #self.function_definitions.object_type_definition(instance._qualified_name, node._qualified_name)

        # Then generate the class attribute definitions.

        self.dispatch(node.code)

        # Generate inherited attributes.

        for name, base in node._inherited.items():
            self.in_function().class_attr(node._qualified_name, name)
            self.in_function().write(" = ")
            self.in_function().class_attr(base._qualified_name, name)
            self.in_function().writeln(";")

    def visitFunction(self, node):

        if not hasattr(node, "_specialises"):
            return

        # Do not write the signature or body out where the function is defined
        # as being native.

        if self.is_native(node):
            return

        # Write the signature out as a declaration.

        qualified_argnames = [(node._qualified_name + "." + name) for name in node.argnames]
        self.module_declarations.function_declaration(node._qualified_name, qualified_argnames)

        # Write any special locals out.

        locals = analysis.namespace.get_locals_layout(node, qualified_names=1, include_parameters=0)
        self.definitions[-1].locals(locals)

        # Make new generators for the function.

        self.definitions.append(DefinitionsGenerator(self.module_declarations, Counter()))
        self.function_bodies.append(CodeGenerator(self))

        # Write the body of the function.

        self.dispatch(node.code)

        # Add some special code for initialisers.

        if node._original.name == "__init__":
            self.in_function().write("return ")
            self.in_function()._name(node._qualified_name + ".self")
            self.in_function().writeln(";")

        # Write the body to the function.

        self.definitions[-1].function_definition(node._qualified_name, qualified_argnames, locals, self.in_function())
        self.function_bodies.pop()

        # Write the generated function out to the top level.

        self.function_definitions.write(self.definitions[-1].get_output())
        self.definitions.pop()

    def visitStmt(self, node):
        for statement_node in node.nodes:
            self.dispatch(statement_node)

    def visitDiscard(self, node):
        self.dispatch(node.expr)
        self.in_function().writeln(";")

    def visitPass(self, node):
        self.in_function().writeln("/* Pass */")

    def visitPrintnl(self, node):

        # Store the stream on the expression stack.
        # NOTE: This does not attempt to cast the stream.

        self.in_function()._start_push()
        if node.dest is not None:
            self.dispatch(node.dest)
        else:
            self.in_function().write("stdout")
        self.in_function()._end_push()
        self.in_function().writeln(";")

        # Process the nodes to be printed.

        n = len(node._calls)
        for i in range(0, n):
            call = node._calls[i]
            self.in_function().write("fputs(GET_STRING(")
            self.in_function()._start_push()
            self.dispatch(call.expr)
            self.in_function()._end_push()
            self.in_function().write("?")
            self.in_function().call_function(call)
            self.in_function().write(":0")
            self.in_function()._pop_quiet()
            self.in_function().write("), ")
            self.in_function()._top()
            self.in_function().writeln(");")
            if i < n - 1:
                self.in_function().write("fputs(")
                self.in_function().write('" ", ')
                self.in_function()._top()
                self.in_function().writeln(");")
        self.in_function().write("fputs(")
        self.in_function().write('"\\n", ')
        self.in_function()._top()
        self.in_function().writeln(");")

        # Correct the expression stack.

        self.in_function()._pop_quiet()   # Pop the stream

    def visitIf(self, node):
        first = 1
        short_circuited = 0
        for compare, block in node.tests:
            if short_circuited:
                break

            if not first:
                self.in_function().write("else if")
            else:
                self.in_function().write("if")
                first = 0

            self.in_function().write("(")
            if hasattr(node, "_tests") and node._tests.has_key(compare):
                self.in_function().write("(")
                self.in_function()._start_push()
                self.dispatch(node._tests[compare].expr)
                self.in_function()._end_push()
                self.in_function().write(") && ")
                self.in_function().write("TRUE(")
                self.in_function().call_function(node._tests[compare])
                self.in_function().write(")")
                self.in_function()._pop_quiet()
            else:
                self.in_function().compare(compare)
            self.in_function().writeln(")")

            self.in_function().writeln("{")
            self.in_function().indent()
            if hasattr(compare, "_ignored"):
                self.in_function().writeln("/* Ignored. */")
            else:
                self.dispatch(block)
            self.in_function().dedent()
            self.in_function().writeln("}")

            if hasattr(compare, "_short_circuited"):
                short_circuited = 1

        if node.else_ is not None and not short_circuited:
            self.in_function().writeln("else")
            self.in_function().writeln("{")
            self.in_function().indent()
            self.dispatch(node.else_)
            self.in_function().dedent()
            self.in_function().writeln("}")

    def visitFor(self, node):

        # Push the expression onto the stack.

        self.in_function()._start_push()
        self.dispatch(node.list)
        self.in_function()._end_push()
        self.in_function().writeln(";")

        # Push the iterator onto the stack.

        self.in_function()._start_push()
        self.in_function().call_function(node)
        self.in_function()._end_push()
        self.in_function().writeln(";")

        # Initialise the loop.

        self.in_function().writeln("Try")
        self.in_function().writeln("{")
        self.in_function().indent()

        self.dispatch(node.assign)

        # Start the loop body.

        self.in_function().writeln("while (1)")
        self.in_function().writeln("{")
        self.in_function().indent()
        self.dispatch(node.body)
        self.dispatch(node.assign)
        self.in_function().dedent()
        self.in_function().writeln("}")

        # Terminate the loop body.

        self.in_function().dedent()
        self.in_function().writeln("}")
        self.in_function().writeln("Catch (_exc)")
        self.in_function().writeln("{")
        self.in_function().indent()
        self.in_function().dedent()
        self.in_function().writeln("}")

        # Correct the expression stack.

        self.in_function()._pop_quiet()   # Pop the iterator
        self.in_function()._pop_quiet()   # Pop the expression

        if node.else_ is not None:
            self.dispatch(node.else_)

    def visitWhile(self, node):
        self.in_function().write("while")

        self.in_function().write("(")
        if hasattr(node, "_test"):
            self.in_function().write("(")
            self.in_function()._start_push()
            self.dispatch(node._test.expr)
            self.in_function()._end_push()
            self.in_function().write(") && ")
            self.in_function().write("TRUE(")
            self.in_function().call_function(node._test)
            self.in_function().write(")")
            self.in_function()._pop_quiet()
        else:
            self.in_function().compare(node.test)
        self.in_function().writeln(")")

        self.in_function().writeln("{")
        self.in_function().indent()
        self.dispatch(node.body)
        self.in_function().dedent()
        self.in_function().writeln("}")
        if node.else_ is not None:
            self.dispatch(node.else_)

    def visitAssign(self, node):

        # Push the expression onto the stack.

        self.in_function()._start_push()
        self.dispatch(node.expr)
        self.in_function()._end_push()
        self.in_function().writeln(";")

        # Visit the target nodes.

        for assign_node in node.nodes:
            self.dispatch(assign_node)

        # Correct the expression stack.

        self.in_function()._pop_quiet()

    def visitAugAssign(self, node):

        # Push the expression onto the stack.

        self.in_function()._start_push()
        self.in_function().write("(")
        self.in_function()._start_push()
        self.dispatch(node._op.node)
        self.in_function()._end_push()
        self.in_function().write(") && (")
        self.in_function()._start_push()
        self.dispatch(node._op.expr) # next == node, top == expr
        self.in_function()._end_push()
        self.in_function().write(") && (")
        self.in_function()._start_push()
        assert self.uses_call(node._op)
        self.in_function().call_function(node._op)
        self.in_function()._end_push()
        self.in_function().write(") ?")
        self.in_function()._top()
        self.in_function().write(":")
        self.in_function()._top()
        self.in_function()._pop_quiet()
        self.in_function()._pop_quiet()
        self.in_function()._pop_quiet()
        self.in_function()._end_push()
        self.in_function().writeln(";")

        # Find the type of assignment and make the assignment.

        if isinstance(node.node, compiler.ast.Getattr):
            self._visitAssAttr(node.node)
        elif isinstance(node.node, compiler.ast.Name):
            self.in_function().name(node.node)
            self.in_function().write("=")
            self.in_function()._top()
            self.in_function().writeln(";")
        else:
            # NOTE: Should not occur!
            pass

        self.in_function()._pop_quiet()

    def visitReturn(self, node):
        self.in_function().write("return ")
        self.dispatch(node.value)
        self.in_function().writeln(";")

    def visitGlobal(self, node):
        for name in node.names:
            self.in_function().write("extern reference *%s;" % name)

    def visitRaise(self, node):
        # NOTE: To be completed.
        self.in_function().write("Throw ")
        self.dispatch(node.expr1)
        self.in_function().writeln(";")

    # Visitor methods for expression nodes.

    def process_binary_operator(self, node):

        """
        Produce this:

        (PUSH(left)) && (PUSH(right)) && (PUSH(fn(left, right)) ? top : top
        """

        self.in_function().write("(")
        self.in_function()._start_push()
        self.dispatch(node.left)
        self.in_function()._end_push()
        self.in_function().write(") && (")
        self.in_function()._start_push()
        self.dispatch(node.right) # next == left, top == right
        self.in_function()._end_push()
        self.in_function().write(") && (")
        self.in_function()._start_push()
        if self.uses_call(node):
            self.in_function().call_function(node)
        else:
            self.dispatch(node._default)
        self.in_function()._end_push()
        self.in_function().write(") ?")
        self.in_function()._top()
        self.in_function().write(":")
        self.in_function()._top()
        self.in_function()._pop_quiet()
        self.in_function()._pop_quiet()
        self.in_function()._pop_quiet()

    def process_unary_operator(self, node):
        self.in_function().write("(")
        self.in_function()._start_push()
        self.dispatch(node.expr)
        self.in_function()._end_push()
        self.in_function().write(") && (")
        self.in_function()._start_push()
        assert self.uses_call(node)
        self.in_function().call_function(node)
        self.in_function()._end_push()
        self.in_function().write(") ?")
        self.in_function()._top()
        self.in_function().write(":")
        self.in_function()._top()
        self.in_function()._pop_quiet()
        self.in_function()._pop_quiet()

    process_sequence_operator = process_unary_operator

    def visitAssName(self, node):
        if self.uses_call(node):
            self.in_function().name(node)
            self.in_function().write("=")
            self.in_function().call_function(node)
            self.in_function().writeln(";")
        else:
            self.in_function().name(node)
            self.in_function().write("=")
            self.in_function()._top()
            self.in_function().writeln(";")

    def visitAssTuple(self, node):
        if node._next_call is not None:
            self.in_function()._start_push()
            self.in_function().call_function(node._next_call)
            self.in_function()._end_push()
            self.in_function().writeln("; /* next */");

        if self.uses_call(node):
            self.in_function()._start_push()
            self.in_function().call_function(node)
            self.in_function()._end_push()
            self.in_function().writeln("; /* __iter__ */");

        for assign_node in node.nodes:
            self.dispatch(assign_node)

        self.in_function()._pop_quiet()
        if node._next_call is not None:
            self.in_function()._pop_quiet()

    visitAssList = visitAssTuple

    def visitAssAttr(self, node):

        # This ensures that the next element of any current collection is
        # obtained.

        if self.uses_call(node):
            self.in_function().call_function(node)

        self._visitAssAttr(node)

    def _visitAssAttr(self, node):

        # Get the expression used as target.

        self.in_function().write("(")
        self.in_function()._start_push()
        self.dispatch(node.expr)
        self.in_function()._end_push()
        self.in_function().write(")?")

        # NOTE: attr attribute argument not used.
        # NOTE: This is because it only affects the production of method objects
        # NOTE: which aren't valid on the left hand side of an assignment.

        objs = node._permitted

        if len(objs) == 1:
            obj = objs[0]
            self.in_function().attr(node, obj, None, node.attrname)
            self.in_function().write("=")
            self.in_function()._next()
        else:
            first = 1
            for obj in objs:
                if not first:
                    self.in_function().write(":")
                self.in_function().attr(node, obj, None, node.attrname, write_case=1)
                self.in_function().write("=")
                self.in_function()._next()
                first = 0

            self.in_function().write(": 0")

        # Terminate the expression.

        self.in_function().writeln(": 0;")
        self.in_function()._pop_quiet()

    def visitGetattr(self, node):

        # Get the expression used as target.

        self.in_function().write("(")
        self.in_function()._start_push()
        self.dispatch(node.expr)
        self.in_function()._end_push()
        self.in_function().write(")?")

        items = node._contexts.items()
        single_choice = (len(items) == 1 and len(unique(items[0][1])) == 1 and \
            not (hasattr(node, "_undesirable") and len(node._undesirable) > 0))

        first = 1
        for obj, attrs in items:
            for attr in unique(attrs):
                if not first:
                    self.in_function().write(": ")
                self.in_function().attr(node, obj, attr, node.attrname, write_case=not single_choice)
                first = 0

        if not single_choice:
            self.in_function().write(": ")
        if first or not single_choice:
            if hasattr(node, "_raises"):
                self.in_function().write("THROW(")
                self.in_function().new(node, "_raises")
                self.in_function().write(")")
            else:
                self.in_function().write("0")

        # Terminate the expression.

        self.in_function().write(": 0")
        self.in_function()._pop_quiet()

    def visitCallFunc(self, node):

        """
        Translate this...

        expr(x, y, z)

        ...into this:

        (_tmp = expr) ? (TYPEOF(_tmp) == C) ? new(C, 3) : (TYPEOF(_tmp) == D) ? new(D, 4) : 0 : 0

        ...or this:

        (_tmp = expr) ? (FNAME(_tmp) == FNAME(f)) ? f(x, y, z) : (FNAME(_tmp) == FNAME(g)) ? g(x, y, z) : 0 : 0
        """

        # Optimised function calls.

        if hasattr(node, "_optimised_value"):
            if node._optimised_value:
                self.in_function().write("builtins___True")
            else:
                self.in_function().write("builtins___False")
            return

        # Get the expression used as target.

        self.in_function().write("(")
        self.in_function()._start_push()
        self.dispatch(node.node)
        self.in_function()._end_push()
        self.in_function().write(")?")

        if self.uses_call(node):
            self.in_function().call_function(node)

        # Instantiate classes where appropriate.

        elif hasattr(node, "_instantiates"):
            self.in_function().new(node)

        # Where no call can be made, raise an exception.

        elif hasattr(node, "_raises"):
            self.in_function().write("THROW(")
            self.in_function().new(node, "_raises")
            self.in_function().write(")")

        # Where no exceptions are employed, produce a default.

        elif hasattr(node, "_default"):
            self.in_function().name(node._default)

        else:
            self.in_function().write("0")

        # Terminate the expression.

        self.in_function().write(": 0")
        self.in_function()._pop_quiet()

    def visitName(self, node):
        if not hasattr(node, "_scope"):
            # Unreachable.
            pass
        self.in_function().name(node)

    def visitConst(self, node):
        if self.constant_values.has_key(repr(node.value)):
            n = self.constant_values[repr(node.value)]
        else:
            n = CVisitor.constant_start + len(self.constants)
            self.constants.append(node)
            self.constant_values[repr(node.value)] = n
        self.in_function().write("&_const_%s" % n)

    def visitList(self, node):
        self.in_function().write("(")
        self.in_function()._start_push()
        # NOTE: Either one of these should succeed.
        if self.uses_call(node):
            self.in_function().call_function(node)
        elif hasattr(node, "_instantiates"):
            self.in_function().new(node)
        self.in_function()._end_push()
        self.in_function().write(")?")

        # Generate the sequence of calls to build the list.
        # call1 && call2 && ...

        first = 1
        for call in node._calls:
            if not first:
                self.in_function().write("&&")

            # Cause an expression (the list) to be yielded.

            self.in_function().write("(")
            self.in_function().call_function(call)
            self.in_function().write(")")

            first = 0

        # The calls should always lead to a true result.

        if len(node._calls) != 0:
            self.in_function().write(" ? ")
            self.in_function()._top()
            self.in_function().write(" : ")

        self.in_function()._pop()

        # Or None if no instantiation occurred.

        self.in_function().write(": 0")

    visitTuple = visitList

    def visitCompare(self, node):
        self.in_function().write("(")
        first = 1
        for op in node._ops:
            if not first:
                self.in_function().write("&&")
            self.in_function().write("TRUE(")
            self.process_binary_operator(op)
            self.in_function().write(")")
            first = 0
        self.in_function().write("? builtins___True")
        self.in_function().write(": builtins___False")
        self.in_function().write(")")

    def visitAnd(self, node):
        self.in_function().write("(")
        first = 1
        for op in node._nodes:
            if not first:
                self.in_function().write(" && ")
            # Store the expression used by the __true__ call.
            self.in_function().write("(")
            self.in_function().write("(")
            self.in_function()._start_push()
            self.dispatch(op.expr)
            self.in_function()._end_push()
            self.in_function().write(") && ")
            # Invoke the __true__ call.
            self.in_function().write("TRUE(")
            self.in_function().call_function(op)
            self.in_function().write(")")
            self.in_function().write(")")
            # Make room on the stack for the next iteration.
            self.in_function()._pop_quiet()
            first = 0
        self.in_function().write("?")
        self.in_function()._last()
        self.in_function().write(":")
        self.in_function()._last()
        self.in_function().write(")")

    def visitOr(self, node):
        self.in_function().write("(")
        first = 1
        for op in node._nodes:
            if not first:
                self.in_function().write(" || ")
            # Store the expression used by the __true__ call.
            self.in_function().write("(")
            self.in_function().write("(")
            self.in_function()._start_push()
            self.dispatch(op.expr)
            self.in_function()._end_push()
            self.in_function().write(") && ")
            # Invoke the __true__ call.
            self.in_function().write("TRUE(")
            self.in_function().call_function(op)
            self.in_function().write(")")
            self.in_function().write(")")
            # Make room on the stack for the next iteration.
            self.in_function()._pop_quiet()
            first = 0
        self.in_function().write("?")
        self.in_function()._last()
        self.in_function().write(":")
        self.in_function()._last()
        self.in_function().write(")")

    def visitNot(self, node):
        self.in_function().write("(")
        self.in_function().write("(")
        self.in_function()._start_push()
        self.dispatch(node._true_call.expr) # Evaluate the expression
        self.in_function()._end_push()
        self.in_function().write(") && ")
        self.in_function().write("(")
        self.in_function()._start_push()
        self.in_function().call_function(node._true_call) # Invoke __not__(expr)
        self.in_function()._end_push()
        self.in_function().write(") && ")
        self.in_function().write("TRUE(")
        self.in_function()._start_push()
        self.in_function().call_function(node) # Invoke __true__(...)
        self.in_function()._end_push()
        self.in_function().write(")")
        self.in_function().write(")")
        self.in_function()._pop_quiet()
        self.in_function().write("?")
        self.in_function()._last()
        self.in_function().write(":")
        self.in_function()._last()
        self.in_function()._pop_quiet()
        self.in_function()._pop_quiet()

def write_main(generator, main_module_name):

    """
    Write to the given 'generator' a main function invoking the
    'main_module_name'.
    """

    main_generator = CGenerator()
    main_generator.include(main_module_name)
    main_generator.writeln("int main(int argc, char *argv[])")
    main_generator.writeln("{")
    main_generator.indent()
    main_generator.writeln("SYSINIT;")
    main_generator.writeln("_argc = argc;")
    main_generator.writeln("_argv = argv;")
    main_generator.writeln("Try")
    main_generator.writeln("{")
    main_generator.indent()
    main_generator.writeln("return ___%s_main(argc, argv);" % main_generator._translate(main_module_name))
    main_generator.dedent()
    main_generator.writeln("}")
    main_generator.writeln("Catch_anonymous")
    main_generator.writeln("{")
    main_generator.indent()
    main_generator.writeln("fputs(\"Uncaught exception.\\n\", stderr);")
    main_generator.writeln("return 1;")
    main_generator.dedent()
    main_generator.writeln("}")
    main_generator.dedent()
    main_generator.writeln("}")
    generator.write(main_generator.get_output())

# vim: tabstop=4 expandtab shiftwidth=4
