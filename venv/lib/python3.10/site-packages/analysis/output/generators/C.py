#!/usr/bin/env python

"""
A C language generator.

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
from analysis.output.generators.common import RawGenerator
import analysis.reference
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class CGenerator(RawGenerator):

    "The common generator for C programs and headers."

    def __init__(self):
        RawGenerator.__init__(self, StringIO())

    def _translate(self, name):

        "Return a translation of 'name' compatible with C syntax."

        # Replace reference name characters.

        return name.replace(".", "___").replace("-", "___")

    def include(self, module_name):
        self.writeln('#include "%s.h"' % module_name)

    def start_guard(self, module_name):
        self.writeln("#ifndef _%s_H_" % self._translate(module_name).upper())
        self.writeln("#define _%s_H_" % self._translate(module_name).upper())

    def end_guard(self, module_name):
        self.writeln("#endif /* _%s_H_ */" % self._translate(module_name).upper())

    def function_signature(self, name, argnames):
        self.write("reference *%s" % self._translate(name))
        arg_defs = []
        for argname in argnames:
            arg_defs.append("reference *%s" % self._translate(argname))
        self.write("(%s)" % ", ".join(arg_defs))

    def main_signature(self, name):
        self.write("int ___%s_main(int argc, char *argv[])" % self._translate(name))

    def get_output(self):
        return self.stream.getvalue()

class DeclarationsGenerator(CGenerator):

    "A generator for C declarations."

    def __init__(self, counter):
        CGenerator.__init__(self)
        self.counter = counter

    def function_declaration(self, name, argnames):
        self.function_signature(name, argnames)
        self.writeln(";")

    def main_declaration(self, name):
        self.main_signature(name)
        self.writeln(";")

    def object_declaration(self, name, attrnames):
        self.writeln("typedef struct object_%s" % self._translate(name))
        self.writeln("{")
        self.indent()
        self.writeln("int type;")
        for attrname in attrnames:
            self.writeln("reference *%s;" % self._translate(attrname))
        self.dedent()
        self.writeln("} object_%s;" % self._translate(name))
        self.writeln()

    def object_type_declaration(self, name):
        self.writeln("int type_%s;" % self._translate(name))
        self.writeln()

    def method_declaration(self, name):
        self.writeln("object_method _%s;" % self._translate(name))
        self.writeln("reference *%s;" % self._translate(name))

    def class_declaration(self, name):
        # Write a base type number.
        # NOTE: This list needs to be replaced with a more maintainable mechanism.
        # NOTE: These types are already defined in the runtime, since they are
        # NOTE: central to the functioning of various runtime facilities.
        if name not in ("builtins.none", "builtins.int", "builtins.float", "builtins.string", "builtins.long", "builtins.buffer", "builtins.boolean"):
            self.counter.new_series(name)
            self.writeln("#define type_%s %d" % (self._translate(name), self.counter.get_base(name)))
        # Write the reference declaration.
        self.writeln("reference *%s;" % self._translate(name))

    def other_declaration(self, name):
        self.writeln("reference *%s;" % self._translate(name))

class DefinitionsGenerator(CGenerator):

    "A generator for C definitions: actual function bodies and so on."

    def __init__(self, declarations, counter):
        CGenerator.__init__(self)
        self.declarations = declarations
        self.counter = counter

    def get_const_value(self, value):
        if isinstance(value, str):
            return '"' + value.replace('"', '\\"') + '"'
        else:
            return str(value)

    def stack(self, highest):
        for i in range(1, highest + 1):
            self.writeln("reference *_stack_%d;" % i)
        self.writeln()

    def method_definition(self, name):
        self.writeln("object_method _%s = {type_method, (reference *) %d, 0};" %
            (self._translate(name), self.counter.get_number()))
        self.writeln("reference *%s = (reference *) &_%s;" %
            (self._translate(name), self._translate(name)))

    def function_definition(self, name, argnames, locals, code_generator):
        self.function_signature(name, argnames)
        self.writeln()
        self.writeln("{")
        self.indent()
        self.locals(locals, function_locals=1)
        self.stack(code_generator.get_highest_local())
        self.dedent()
        self.write(code_generator.get_output())
        self.writeln("}")
        self.writeln()

    def main_definition(self, name, code_generator):
        self.main_signature(name)
        self.writeln()
        self.writeln("{")
        self.indent()
        self.stack(code_generator.get_highest_local())
        self.dedent()
        self.write(code_generator.get_output())
        self.indent()
        self.writeln("return 0;")
        self.dedent()
        self.writeln("}")
        self.writeln()

    def object_type_definition(self, name, class_name):
        self.writeln("int type_%s = %d;" % (self._translate(name), self.counter.get_number(class_name)))

    def class_definition(self, name):
        # Write a reference definition for the class.
        self.writeln("reference *%s = (reference *) type_%s;" % (self._translate(name), self._translate(name)))

    def module_definition(self, name):
        self.counter.new_series(name)
        self.writeln("reference *%s = (reference *) %d;" % (self._translate(name), self.counter.get_base(name)))

    def constant(self, type_name, number, value):
        self.writeln("object_%s _const_%s = {type_%s, %s};" %
            (self._translate(type_name), number, self._translate(type_name),
            self.get_const_value(value)))

    # Node-dependent methods.

    def _is_function(self, nodes):
        return reduce(lambda result, node: result or isinstance(node, compiler.ast.Function), nodes, 0)

    def _is_specialised_function(self, nodes):
        return self._is_function(nodes) and reduce(lambda result, node: result or getattr(node, "_specialisations", []), nodes, 0)

    def _is_class(self, nodes):
        return reduce(lambda result, node: result or isinstance(node, compiler.ast.Class), nodes, 0)

    def _is_module(self, nodes):
        return reduce(lambda result, node: result or isinstance(node, compiler.ast.Module), nodes, 0)

    def locals(self, locals, native=0, function_locals=0):

        """
        Write the given 'locals' (a list of 2-tuples each containing a name
        and a list of nodes).

        Specially generate magic values for function, class and module
        identifiers.
        NOTE: This doesn't work with nodes which could be mixtures of
        NOTE: functions, classes and instances.
        """

        if not locals:
            return

        for name, nodes in locals:
            # NOTE: Could check for specialised functions here, but subclasses
            # NOTE: may inherit these names, and we would have to be more
            # NOTE: careful about which ones actually get defined.
            if not function_locals and self._is_function(nodes):
                self.declarations.method_declaration(name)
                self.method_definition(name)
            elif not function_locals and self._is_class(nodes):
                self.declarations.class_declaration(name)
                self.class_definition(name)
            elif not function_locals and self._is_module(nodes):
                self.declarations.other_declaration(name)
                self.module_definition(name)
            elif not native:
                is_function_local = 0
                is_special_local = 0
                for node in nodes:
                    if hasattr(node, "_name_context") and node._name_context == "function":
                        is_function_local = 1
                        break
                    if hasattr(node, "_name_context") and node._name_context == "special":
                        is_special_local = 1
                        break
                if function_locals and is_function_local:
                    self.writeln("reference *%s;" % self._translate(name))
                else:
                    self.declarations.other_declaration(name)

        self.writeln()

class CodeGenerator(CGenerator):

    "A generator for C program instructions."

    def __init__(self, visitor):
        CGenerator.__init__(self)
        self.visitor = visitor

        # Variable counters representing the expression stack.

        self.counter = 0
        self.highest = 0
        self.indent()

    def get_highest_local(self):
        return self.highest

    def get_argnodes(self, node, key):
        return node._argnodes[key][0]

    def get_argnode(self, node, argname, key):
        return self.get_argnodes(node, key)[argname][0]

    def uses_reference(self, node, argnames, key):
        # NOTE: May not be an exhaustive enough test, although mixtures of
        # NOTE: references and non-references would only occur occasionally.
        if len(argnames) > 0:
            obj_refs = self.get_argnodes(node, key)[argnames[0]]
            if len(obj_refs) > 0 and isinstance(obj_refs[0], analysis.reference.Reference):
                return 1
        return 0

    def _start_push(self):
        self.write("PUSH(")

    def _end_push(self):
        if self.counter + 1 > self.highest:
            self.highest = self.counter + 1
        self.counter = self.counter + 1
        self.write(", _stack_%d)" % self.counter)

    def _top(self):
        self.write("_stack_%d" % self.counter)

    def _next(self):
        self.write("_stack_%d" % (self.counter - 1))

    def _last(self):
        self.write("_stack_%d" % (self.counter + 1))

    def _nth(self, n):
        self.write("_stack_%d" % (self.counter - n))

    def _pop(self):
        self.write("_stack_%d" % self.counter)
        self.counter = self.counter - 1

    def _pop_quiet(self):
        self.counter = self.counter - 1

    def type_of_choice(self, node, choice):
        self.write("(")
        first = 1
        for local in choice:
            if not first:
                self.write(" || ")
                self._pop_quiet()
            self.type_of(node, local._qualified_name)
            first = 0
        self.write(")")

    def type_of(self, node, name):
        self.write("(TYPEOF(")
        self._start_push()
        self.visitor.dispatch(node)
        self._end_push()
        self.write(") == type_%s)" % self._translate(name))

    def type_of_stack_choice(self, choice, func):
        self.write("(")
        first = 1
        for local in choice:
            if not first:
                self.write(" || ")
            self.type_of_stack(local, func)
            first = 0
        self.write(")")

    def type_of_stack(self, obj, func):
        self.write("(TYPEOF(")
        func()
        self.write(") == type_%s)" % self._translate(obj._qualified_name))

    def type_of_stack_class(self, cls, func):
        self.write("(")
        func()
        self.write(" == (reference *) type_%s)" % self._translate(cls._qualified_name))

    def type_of_stack_context_choice(self, choice, func):
        self.write("(")
        first = 1
        for local in choice:
            if not first:
                self.write(" || ")
            self.type_of_stack_context(local, func)
            first = 0
        self.write(")")

    def type_of_stack_context(self, obj, func):
        self.write("(TYPEOF(CONTEXT(")
        func()
        self.write(")) == type_%s)" % self._translate(obj._qualified_name))

    def fname_top(self, name):
        self.write("(FNAME(")
        self._top()
        self.write(") == FNAME(%s))" % self._translate(name))

    def start_test(self):
        self.write("(")

    def end_test(self):
        self.write(")? ")

    def _name(self, name):
        self.write(self._translate(name))

    def start_statement(self):
        pass

    def end_statement(self):
        self.writeln(";")

    def import_module(self, name):
        self.writeln("___%s_main(argc, argv);" % self._translate(name))

    def compare(self, compare):
        if hasattr(compare, "_optimised_value"):
            if compare._optimised_value:
                self.write("1")
            else:
                self.write("0")
        else:
            self.write("TRUE(")
            self.call_function(compare)
            self.write(")")

    def class_test(self, name):
        self.write("(")
        self._top()
        self.write(" == ", self._translate(name), ")? ")

    module_test = class_test

    def class_attr(self, name, attrname):
        self.write("%s___%s" % (self._translate(name), attrname))

    module_attr = class_attr

    def instance_attr(self, name, attrname):
        if attrname == "__class__":
            self.write(self._translate(name))
        else:
            self.write("((object_%s *)" % self._translate(name))
            self._top()
            self.write(")->%s" % attrname)

    def method_attr(self, name):
        self.write("NEW_METHOD(FNAME(")
        self._name(name)
        self.write(") ,")
        self._top()
        self.write(")")

    def new_object(self, name):
        self.write("NEW_OBJECT(%s)" % self._translate(name))

    # Node-dependent methods.

    def name(self, node):
        self._name(node._qualified_name)

    def attr(self, node, obj, attr, attrname, write_case=0):

        """
        For the given 'node' expressing an attribute lookup, Write a reference
        to the attribute of the given object or class 'obj' using the suggested
        'attr' and having the given 'attrname'.
        """

        #self.write("/* " + repr(node) + " -> " + repr(obj) + "." + repr(attr) + " */")

        if isinstance(obj, compiler.ast.Class):
            if write_case:
                self.class_test(obj._qualified_name)
            self.class_attr(obj._qualified_name, attrname)

        elif isinstance(obj, analysis.reference.Reference):
            if write_case:
                self.start_test()
                self.type_of_stack(obj, self._top)
                self.end_test()

            # Only create new method references when the method is first
            # extracted through a lookup on the class.

            if hasattr(node, "_name_context") and node._name_context == "class":
                if isinstance(attr, compiler.ast.Function):
                    self.method_attr(attr._qualified_name)
                else:
                    self.class_attr(obj._class._qualified_name, attrname)
            else:
                self.instance_attr(obj._qualified_name, attrname)

        elif isinstance(obj, compiler.ast.Module):
            if write_case:
                self.module_test(obj._qualified_name)
            self.module_attr(obj._qualified_name, attrname)

    def new(self, node, annotation="_instantiates"):

        """
        Write a reference to a new object instantiated by the given 'node'.
        """

        classes = getattr(node, annotation)

        # Produce the instantiation code.

        if len(classes) > 1:

            for cls in classes:
                self.type_of_stack_class(cls, self._top)
                self.write("? ")
                self.new_object(cls._qualified_name)
                self.write(" : ")

            # Where no instantiation can occur, raise an exception.
            # NOTE: Check the exception type.

            if hasattr(node, "_raises"):
                self.write("THROW(")
                self.new(node, "_raises")
                self.write(")")
            else:
                self.write("0")

        elif len(classes) == 1:
            cls = classes[0]
            self.new_object(cls._qualified_name)

    def call_function(self, node):

        """
        Write function calls, associated with the given 'node'.
        """

        if len(node._targets) > 1 or hasattr(node, "_undesirable") and len(node._undesirable) > 0 or hasattr(node, "_raises"):

            for target, t_locals, t_argnames, refcontext, key in \
                map(None, node._targets, node._locals, node._argnames, node._refcontexts, node._argnodes_keys):

                self.start_target_test(node, t_locals, t_argnames, refcontext, target, key)
                self._name(target._qualified_name)
                self.parameters(node, t_locals, t_argnames, refcontext, target, key)
                self.write(" : ")
                self.end_target_test(refcontext)

            # Where no call can be made, raise an exception.
            # NOTE: Check the exception type.

            if hasattr(node, "_raises"):
                self.write("THROW(")
                self.new(node, "_raises")
                self.write(")")
            else:
                self.write("0")

        elif len(node._targets) == 1:
            target, t_locals, t_argnames, refcontext, key = node._targets[0], node._locals[0], node._argnames[0], node._refcontexts[0], node._argnodes_keys[0]
            self._name(target._qualified_name)
            self.parameters(node, t_locals, t_argnames, refcontext, target, key)

    def start_target_test(self, node, locals, argnames, refcontext, target, key):

        """
        Write the test which selects a particular function call.
        """

        # Generate binary operator tests.

        if refcontext == "left-right":
            self.write("(")
            self.type_of_stack_choice(locals[argnames[0]], self._next)
            self.write(" && ")
            self.type_of_stack_choice(locals[argnames[1]], self._top)
            self.write(")? ")

        elif refcontext == "right-left":
            self.write("(")
            self.type_of_stack_choice(locals[argnames[0]], self._top)
            self.write(" && ")
            self.type_of_stack_choice(locals[argnames[1]], self._next)
            self.write(")? ")

        # Generate augmented assignment tests.

        elif refcontext == "aug-assign":
            self.write("(")
            self.type_of_stack_choice(locals[argnames[0]], self._top)
            self.write(" && ")
            self.type_of_stack_choice(locals[argnames[1]], self._next)
            self.write(")? ")

        # Generate active stack object tests.

        elif refcontext == "top":
            self.type_of_stack_choice(locals[argnames[0]], self._top)
            self.write("? ")

        # Generate method tests.

        elif self.uses_reference(node, argnames, key):
            self.write("(")
            self.type_of_stack_context_choice(locals[argnames[0]], self._top)
            self.write(" && ")
            self.fname_top(target._original._qualified_name)
            self.write(")")
            self.write("? ")

        # Generate local function tests.

        elif refcontext == "context":
            self.fname_top(target._original._qualified_name)
            self.write("? ")

    def end_target_test(self, refcontext):

        """
        Write the end of the function call selection test.
        """

        pass

    def parameters(self, node, locals, argnames, refcontext, target, key):

        """
        Write the parameters associated with the given function call 'node'
        using the given call 'locals' and a 'refcontext' used to indicate how
        reference objects used in the call are to be represented.
        """

        # NOTE: Support star and dstar arguments.

        self.write("(")

        # Write binary operator parameters.

        if refcontext in ("left-right", "right-left"):
            call_args = []
            if refcontext == "left-right":
                self._next()
            elif refcontext == "right-left":
                self._top()
            self.write(",")
            if refcontext == "left-right":
                self._top()
            elif refcontext == "right-left":
                self._next()

        # Write augmented assignment parameters.

        elif refcontext == "aug-assign":
            call_args = []
            self._next()
            self.write(",")
            self._top()

        # Write conventional method initial parameter.

        elif self.uses_reference(node, argnames, key):
            call_args = argnames[1:]

            # Normal method calls.

            if refcontext == "context":
                self.write("CONTEXT(")
                self._top()
                self.write(")")

            # Initialiser method calls.

            elif refcontext == "new":
                self.new(node)

            # Expression-related method calls (see visitList).

            elif refcontext == "top":
                self._top()

            first = 0

        # Functions use all parameters.

        else:
            call_args = argnames
            first = 1

        # Write remaining parameters.
        # NOTE: Wrap parameters in stack operations in order to provide distinct
        # NOTE: references; otherwise, it appears that the compiler may be
        # NOTE: tempted, where code like the following occurs, to optimise the
        # NOTE: call:
        # NOTE: fn(PUSH(x, _stack_5) ? _stack_5 : _stack_5, PUSH(y, _stack_5) ? _stack_5 : _stack_5)
        # NOTE: -> PUSH(x, _stack_5) && PUSH(y, _stack_5) && fn(_stack_5, _stack_5)

        for arg in call_args:
            if not first:
                self.write(",")
            self._start_push()
            self.visitor.dispatch(self.get_argnode(node, arg, key))
            self._end_push()
            first = 0

        self.write(")")

        # NOTE: Pop the above stack operations.

        for arg in call_args:
            self._pop_quiet()

# vim: tabstop=4 expandtab shiftwidth=4
