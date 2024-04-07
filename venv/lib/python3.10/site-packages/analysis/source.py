#!/usr/bin/env python

"""
Source code analysis.

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
from compiler.visitor import ASTVisitor

from analysis.common import *
from analysis.namespace import NamespaceRegister
import analysis.arguments
import analysis.classes
import analysis.node
import analysis.operators
import analysis.reference
import analysis.specialisation
import sys, os

# Utility classes.

class ModifiedDict(dict):

    """
    This modified dictionary is just a normal dictionary with an additional
    status attribute.
    """

    def __init__(self, *args, **kw):
        self.first = 1
        dict.__init__(self, *args, **kw)

# Exceptions.

class NoTargetsError(Exception):

    "An exception signalling that no suitable invocation targets can be found."

    pass

class InvalidTargetError(Exception):

    """
    An exception signalling that the suggested invocation target is not
    callable.
    """

    pass

# The visitor infrastructure.

class AnalysisVisitor(ASTVisitor):

    # Top-level node processing.

    def __init__(self, session=None, filename=None, module_name=None):

        """
        Initialise the visitor with an optional 'session', 'filename', and an
        optional 'module_name'.
        """

        ASTVisitor.__init__(self)
        self.session = session
        self.filename = filename
        self.module_name = module_name

        # The specialiser and instantiator dictate the behaviour of the analysis
        # in terms of providing function specialisations and type/class
        # references.

        self.specialiser = analysis.specialisation.Specialiser()
        self.instantiator = analysis.reference.Instantiator()

        # Special tracking of current operations.

        self.current_module = None
        self.current_callers = []
        self.current_specialisations = []
        self.current_blockages = []
        self.graph = analysis.node.Graph()

        # Initialise namespaces.

        self.globals = {}

        # Where no builtins module exists (because we are currently processing
        # it), make the builtins the same as the globals and set up various
        # special name definitions.

        if self.session is None or self.session.builtins is None:
            self.builtins = self.globals
            self.true, self.false, self.undefined, self.none = None, None, None, None

        # Where a builtins module exists, refer to it, obtaining the special
        # names from it.

        else:
            # Convert from module node to a plain namespace.

            self.builtins = self.session.builtins._namespace
            self.true = self.builtins["True"][0]
            self.false = self.builtins["False"][0]
            self.undefined = self.builtins["Undefined"][0]
            self.none = self.builtins["None"][0]

    # General node processing.

    def dispatch(self, node, *args):

        """
        Dispatch to the handler method for 'node', providing the additional 'args'.
        """

        ASTVisitor.dispatch(self, node, *args)

    def default(self, node, handler):

        """
        Handle a 'node' not explicitly handled elsewhere, using the given
        namespace 'handler'.
        """

        if analysis.operators.is_binary_operator(node):
            self.process_binary_operator(node, handler)
        elif analysis.operators.is_unary_operator(node):
            self.process_unary_operator(node, handler)
        else:
            self.depth_first(node, handler)

    def depth_first(self, node, handler, right_to_left=0):

        """
        Traverse the children of the given 'node', using the given 'handler'. If the
        optional 'right_to_left' flag is set, traverse the children in reverse
        order.

        See also visitStmt which also traverses child nodes.
        """

        child_nodes = list(node.getChildNodes())
        if right_to_left:
            child_nodes.reverse()
        for child_node in child_nodes:

            # For convenience, add the parent node.

            child_node._parent = node
            self.dispatch(child_node, handler)

    def process_block(self, node, handler):

        """
        Process the 'node' with the given namespace 'handler' for a block of code.
        """

        self.depth_first(node, handler)
        node._namespace = handler.locals

    # Specific node handlers.

    def visitModule(self, module, handler=None):

        """
        Process the given 'module' node with the optional 'builtins' dictionary.
        If 'builtins' is not specified, combine the globals and built-ins in the
        processed module.
        If the optional 'module_name' is specified, names defined in this module
        will be suitably qualified by this information.
        """

        handler = NamespaceRegister(self.graph, {}, self.globals, self.globals, self.builtins,
            name_qualifier=self.module_name, name_context="module",
            module_name=self.module_name)

        # Add the constants table to the module.

        self.current_module = module
        module._constants_table = []

        # Process the module.

        self.process_block(module, handler)

        # Add the module name to the module.

        module._qualified_name = module._module_name = self.module_name

    def visitAnd(self, and_, handler):

        "Process the given 'and_' node using the given 'handler'."

        self.depth_first(and_, handler)

        nodes = getattr(and_, "_nodes", [])

        for node, helper in map(None, and_.nodes, nodes):
            self.graph.merge(and_, node)

            # Introduce a helper node for the __true__ invocation.

            if helper is None:
                helper = self.graph.helper(node, _parent=and_, filename=self.filename)
                nodes.append(helper)
            self.reset_specialisations(helper)
            self.attach_true(helper, node, "top", handler)

        and_._nodes = nodes

    def visitAssign(self, assign, handler):

        "Process the given 'assign' node using the given 'handler'."

        assign.expr._parent = assign
        self.dispatch(assign.expr, handler)
        self.graph.merge(assign, assign.expr)

        # Store the expression for use by descendant nodes.

        nodes = assign.nodes[:]
        nodes.reverse()
        for node in nodes:
            node._parent = assign
            self.dispatch(node, handler)

    def visitAssAttr(self, assattr, handler):

        "Process the given 'assattr' node using the given 'handler'."

        self.reset_specialisations(assattr)
        if isinstance(assattr._parent, compiler.ast.AssTuple) or \
            isinstance(assattr._parent, compiler.ast.AssList) or \
            isinstance(assattr._parent, compiler.ast.For):

            self.attach_next_iteration(assattr, assattr._parent, handler)
        else:
            self.graph.merge(assattr, assattr._parent)

        self.depth_first(assattr, handler)

        # Link the found attributes to this node's contexts.

        undesirable_accesses = []
        permitted_accesses = []

        for obj in lobj(assattr.expr, strict=1):

            # Detect undesirable cases of assignment.

            if hasattr(obj, "_class") and has_docstring_annotation(obj._class, "ATOMIC"):
                if obj not in undesirable_accesses:
                    undesirable_accesses.append(obj)
                    handler.filter(assattr.expr, obj)
                continue
            else:
                if obj not in permitted_accesses:
                    permitted_accesses.append(obj)

            # Link to this node in the attribute entry.

            if not obj._namespace.has_key(assattr.attrname):
                obj._namespace[assattr.attrname] = [assattr]
            else:
                obj._namespace[assattr.attrname].append(assattr)

        assattr._undesirable = undesirable_accesses
        assattr._permitted = permitted_accesses

        # Filter out undesirable accesses from the types associated with the
        # expression, if this is feasible.

        for obj in assattr._undesirable:
            handler.filter(assattr.expr, obj)

        if assattr._undesirable:
            self.attach_error(assattr, "AttributeError", handler)

    def visitAssName(self, assname, handler):

        "Process the given 'assname' node using the given 'handler'."

        self.reset_specialisations(assname)
        if isinstance(assname._parent, compiler.ast.AssTuple) or \
            isinstance(assname._parent, compiler.ast.AssList) or \
            isinstance(assname._parent, compiler.ast.For):

            self.attach_next_iteration(assname, assname._parent, handler)
        else:
            self.graph.merge(assname, assname._parent)

        handler.store(assname)

    def visitAssTuple(self, asstuple, handler):

        "Process the given 'asstuple' node using the given 'handler'."

        self.reset_specialisations(asstuple)
        next_call = getattr(asstuple, "_next_call", None)

        if isinstance(asstuple._parent, compiler.ast.AssTuple) or \
            isinstance(asstuple._parent, compiler.ast.AssList) or \
            isinstance(asstuple._parent, compiler.ast.For):

            if next_call is None:
                next_call = self.graph.helper(asstuple._parent, _parent=asstuple, filename=self.filename)
            self.reset_specialisations(next_call)
            self.attach_next_iteration(next_call, next_call.expr, handler)
        else:
            self.graph.merge(asstuple, asstuple._parent)

        refcontext = "top"

        # Investigate this node's contexts.
        # These will either be the result of a next method call, or the parent
        # node's contexts.

        if next_call is not None:
            self.attach_iteration(asstuple, next_call, refcontext, handler)
        else:
            self.attach_iteration(asstuple, asstuple._parent, refcontext, handler)

        for node in asstuple.nodes:
            node._parent = asstuple
            self.dispatch(node, handler)

        # Remember the call to next.

        asstuple._next_call = next_call

    def visitAugAssign(self, augassign, handler):

        "Process the given 'augassign' node using the given 'handler'."

        self.depth_first(augassign, handler)

        if not hasattr(augassign, "_op"):
            helper = self.graph.helper(augassign.expr, node=augassign.node, _parent=augassign, filename=self.filename)
        else:
            helper = augassign._op

        self.reset_specialisations(helper)
        method_name = analysis.operators.augmented_methods[augassign.op]
        self._process_binary_operator(helper, helper.node, helper.expr, method_name, None, "aug-assign", None, handler)

        undesirable_accesses = []
        permitted_accesses = []

        if isinstance(augassign.node, compiler.ast.Name):

            # Process like AssName.

            self.graph.merge(augassign.node, helper)
            handler.store(augassign.node)

        elif isinstance(augassign.node, compiler.ast.Getattr):

            # Process like AssAttr.

            self.graph.merge(augassign, helper)

            # Link the found attributes to this node's contexts.

            for obj in lobj(augassign.node.expr, strict=1):

                # Detect undesirable cases of assignment.

                if hasattr(obj, "_class") and has_docstring_annotation(obj._class, "ATOMIC"):
                    if obj not in undesirable_accesses:
                        undesirable_accesses.append(obj)
                        handler.filter(augassign.node.expr, obj)
                    continue
                else:
                    if obj not in permitted_accesses:
                        permitted_accesses.append(obj)

                # Link to this node in the attribute entry.

                if not obj._namespace.has_key(augassign.node.attrname):
                    obj._namespace[augassign.node.attrname] = [augassign]
                else:
                    obj._namespace[augassign.node.attrname].append(augassign)

        else:

            # NOTE: Should never occur!

            pass

        augassign._op = helper
        augassign._undesirable = undesirable_accesses
        augassign._permitted = permitted_accesses

        # Filter out undesirable accesses from the types associated with the
        # expression, if this is feasible.

        for obj in augassign._undesirable:
            handler.filter(augassign.node.expr, obj)

        if augassign._undesirable:
            self.attach_error(augassign, "AttributeError", handler)

    def visitClass(self, class_, handler):

        "Process the given 'class_' node using the given 'handler'."

        new_handler = NamespaceRegister(self.graph, 
            {}, {}, handler.globals, handler.builtins,
            specials={class_.name : [class_]},
            name_qualifier=handler.get_qualified_name(class_.name),
            name_context="class", module_name=self.module_name)

        # Process the class.

        self.process_block(class_, new_handler)

        # Add inherited attributes and methods to the class's namespace.
        # As a consequence of process_block, the base class name nodes should refer
        # to actual base class definitions.
        # NOTE: This only gets inherited attributes from the first superclass
        # NOTE: found.

        class_._inherited = {}
        bases = class_.bases[:]
        bases.reverse()
        for base in bases:
            for node in lobj(base, strict=1):
                for key, values in node._namespace.items():
                    if not class_._namespace.has_key(key):
                        class_._namespace[key] = values
                        class_._inherited[key] = node

        # Store the class, adding various details to the node.

        handler.store(class_)

    def visitCallFunc(self, callfunc, handler):

        "Process the given 'callfunc' node using the given 'handler'."

        self.graph.reset(callfunc)
        self.depth_first(callfunc, handler)
        self.reset_specialisations(callfunc)

        # Prepare contexts - normal function calls do not have any object reference
        # associated with them.

        context_items = callfunc.node._contexts.items()

        # Loop over contexts, annotating the node.

        attributes_found = 0
        undesirable_inputs = []
        undesirable_targets = []

        for obj, attributes in context_items:
            if attributes != []:
                for attribute in attributes:

                    if isinstance(attribute, compiler.ast.Function):
                        args = self.get_context_args(callfunc, obj)

                        # Make a specialisation with the arguments.

                        try:
                            self.call_specialisation(callfunc, attribute, args,
                                "context", handler,
                                callfunc.star_args, callfunc.dstar_args)
                            attributes_found = 1
                        except InvalidTargetError, exc:
                            undesirable_targets.append(exc)
                        except NoTargetsError, exc:
                            undesirable_targets.append(exc)

                    elif isinstance(attribute, compiler.ast.Class):

                        # Make a reference to the class.
                        # NOTE: This should be made dependent on the self argument.

                        ref = self.instantiator.instantiate_class(attribute, callfunc)
                        self.graph.merge_item(callfunc, None, ref)
                        args = self.get_context_args(callfunc, ref)

                        # NOTE: Find any __init__ method.

                        if attribute._namespace.has_key("__init__"):
                            methods = attribute._namespace["__init__"]

                            # Try and call the initialiser.

                            if methods != []:
                                for method in methods:

                                    # Make a specialisation.

                                    try:
                                        self.call_specialisation(callfunc, method, args,
                                            "new", handler,
                                            callfunc.star_args, callfunc.dstar_args)
                                        attributes_found = 1
                                    except InvalidTargetError, exc:
                                        undesirable_targets.append(exc)
                                    except NoTargetsError, exc:
                                        undesirable_targets.append(exc)

                            # Where no initialiser exists, just accept the "no
                            # operation".

                            else:
                                attributes_found = 1
                        else:
                            attributes_found = 1
            else:
                undesirable_inputs.append(obj)
                handler.filter(callfunc.node, obj)

        callfunc._undesirable = undesirable_inputs

        # Filter out undesirable accesses from the types associated with the
        # callable, if this is feasible.

        for obj in callfunc._undesirable:
            handler.filter(callfunc.node, obj)

        if callfunc._undesirable:
            self.attach_error(callfunc, "TypeError", handler)

        if not attributes_found:
            raise NoTargetsError, (callfunc, self.current_callers[:], undesirable_targets)

    def visitCompare(self, compare, handler):

        "Process the given 'compare' node using the given 'handler'."

        # Compare nodes have an expression and then a sequence of comparisons:
        # expr          1
        #   op1 expr1     < x
        #   op2 expr2     < 5
        # This is equivalent to...
        # and
        #   expr op1 expr1
        #   expr1 op2 expr2

        operations = []

        if not hasattr(compare, "_ops"):
            compare._ops = []
            last_expr = compare.expr
            for op, expr in compare.ops:
                compare._ops.append(analysis.operators.Op(last_expr, op, expr, self.filename))
                last_expr = expr

        first = 1
        for op in compare._ops:
            op._parent = compare
            if first:
                op.left._parent = op
                self.dispatch(op.left, handler)
                first = 0
            op.right._parent = op
            self.dispatch(op.right, handler)

            # Check the operator for special comparisons.

            if op.op == "is":
                self.reset_specialisations(op)
                method = handler.builtins["__is__"][0]
                self.call_specialisation(op, method, [op.left, op.right], "left-right", handler)

            elif op.op == "is not":
                self.reset_specialisations(op)
                method = handler.builtins["__is_not__"][0]
                self.call_specialisation(op, method, [op.left, op.right], "left-right", handler)

            # Produce appropriate specialisations.

            else:
                self._process_binary_operator(op, op.left, op.right, op.left_method_name, op.right_method_name, "left-right", "right-left", handler, strict=0)

        # Link to the result of any comparison.

        self.graph.merge(compare, op)

    def visitConst(self, const, handler):

        "Process the given 'const' node using the given 'handler'."

        # Test type(const.value) against int, float, string, unicode, complex,
        # producing a reference to built-in objects.

        if type(const.value) == type(0):
            definitions = handler.builtins["int"]
        elif type(const.value) == type(0L):
            definitions = handler.builtins["long"]
        elif type(const.value) == type(0.0):
            definitions = handler.builtins["float"]
        elif type(const.value) == type(""):
            definitions = handler.builtins["string"]
        elif type(const.value) == type(u""):
            definitions = handler.builtins["unicode"]
        elif type(const.value) == type(0j):
            definitions = handler.builtins["complex"]
        elif type(const.value) == type(False):
            definitions = handler.builtins["boolean"]
        else:
            raise TypeError, "Constant with value %s not handled." % repr(const.value)

        for definition in definitions:
            ref = self.get_const_ref(const, definition)
            self.graph.merge(const, ref)

    def visitFor(self, for_, handler):

        "Process the given 'for_' node using the given 'handler'."

        for_.list._parent = for_
        self.dispatch(for_.list, handler)

        # Process iteration over the "list" expression.

        self.reset_specialisations(for_)
        self.attach_iteration(for_, for_.list, "top", handler)

        # Process the assignment for each iteration.
 
        for_.assign._parent = for_
        for_.body._parent = for_

        self.current_specialisations.append(for_)
        try:
            while 1:
                for_._counter = self.graph.counter
                self.dispatch(for_.assign, handler)

                # Process the loop contents.

                self.process_conditional(for_.body, handler, handler.locals, handler.filtered_locals)
                if for_.else_ is not None:
                    for_.else_._parent = for_
                    self.process_conditional(for_.else_, handler, handler.locals, handler.filtered_locals)

                if for_._counter == self.graph.counter:
                    break
        finally:
            self.current_specialisations.pop()

    def visitFunction(self, function, handler):
        function._globals = handler.globals
        function._specials = handler.specials
        function._module_name = handler.module_name
        handler.store(function)

    def visitGetattr(self, getattr, handler):

        "Process the given 'getattr' node using the given 'handler'."

        self.depth_first(getattr, handler)

        # Use a mechanism which properly distinguishes between class and
        # instance attributes.

        self.graph.reset(getattr)
        undesirable_accesses = []
        permitted_accesses = []

        for obj in lobj(getattr.expr, strict=1):

            # Test for special attributes.

            if getattr.attrname == "__class__":
                attributes = [obj._class]
            else:
                attributes = obj._namespace.get(getattr.attrname, [])

            # Set the name context.
            # NOTE: This rules out any mixtures of classes and instances handled
            # NOTE: by generated code which relies on this feature (since only a
            # NOTE: single name context is permitted).

            if not attributes:
                attributes = obj._class._namespace.get(getattr.attrname, [])

                # Discover cases where no attribute was found and flag them as
                # undesirable.

                if not attributes:
                    if obj not in undesirable_accesses:
                        undesirable_accesses.append(obj)
                        handler.filter(getattr.expr, obj)
                    continue
                else:
                    getattr._name_context = "class"

            elif isinstance(obj, compiler.ast.Class):
                getattr._name_context = "class"
            else:
                getattr._name_context = "instance"

            permitted_accesses.append(obj)

            for attribute in attributes:

                # NOTE: Special case handling?

                if hasattr(attribute, "_contexts"):
                    for ref in lobj(attribute, strict=1):
                        self.graph.merge_item(getattr, obj, ref)
                elif isinstance(attribute, compiler.ast.Function):
                    self.graph.merge_item(getattr, obj, attribute)
                elif isinstance(attribute, compiler.ast.Class):
                    self.graph.merge_item(getattr, obj, attribute)

        getattr._undesirable = undesirable_accesses
        getattr._permitted = permitted_accesses

        # Filter out undesirable accesses from the types associated with the
        # expression, if this is feasible.

        for obj in getattr._undesirable:
            handler.filter(getattr.expr, obj)

        if getattr._undesirable:
            self.attach_error(getattr, "AttributeError", handler)

    def visitGlobal(self, global_, handler):
        handler.make_global(global_)

    def visitIf(self, if_, handler):

        "Process the given 'if_' node using the given 'handler'."

        blocks = if_.tests[:]
        if if_.else_ is not None:
            blocks.append((None, if_.else_))

        modified_locals = ModifiedDict()
        modified_filtered_locals = ModifiedDict()
        short_circuited = 0

        if_._tests = getattr(if_, "_tests", {})

        for compare, block in blocks:

            # For convenience, add the parent node.

            block._parent = if_

            if hasattr(compare, "_ignored"):
                delattr(compare, "_ignored")
            if hasattr(compare, "_short_circuited"):
                delattr(compare, "_short_circuited")

            if compare is not None:
                compare._parent = if_
                self.dispatch(compare, handler)

                # Short-circuit evaluation for compile-time optimisations.

                if lobj(compare, strict=1) == [self.false]:
                    compare._ignored = 1
                    continue
                elif lobj(compare, strict=1) == [self.true]:
                    compare._short_circuited = 1

                # Additional processing to produce a boolean result.

                else:
                    if not if_._tests.has_key(compare):
                        helper = self.graph.helper(compare, _parent=if_, filename=self.filename)
                    else:
                        helper = if_._tests[compare]
                    self.reset_specialisations(helper)
                    self.attach_true(helper, compare, "top", handler)
                    if_._tests[compare] = helper

            # Skip the block if short-circuited.

            if short_circuited:
                break

            self.process_conditional(block, handler, modified_locals, modified_filtered_locals)

            if hasattr(compare, "_short_circuited"):
                short_circuited = 1

        # Merge in existing locals where no "else" clause was specified.

        if if_.else_ is None and not short_circuited:
            self.merge_locals(modified_locals, handler.locals)
            #self.merge_locals(modified_filtered_locals, handler.filtered_locals)

        # Replace the existing locals.

        handler.locals = modified_locals
        handler.filtered_locals = modified_filtered_locals

    def visitImport(self, import_, handler):

        "Process the given 'import_' node using the given 'handler'."

        import_._module_name = self.module_name

        # NOTE: Only process once!

        if not hasattr(import_, "_names"):
            import_._names = []
            for module_name, as_name in import_.names:
                module = self.session.process_name(module_name)
                import_._names.append(
                    self.graph.helper(
                        module, module_name=module_name, as_name=as_name, name=(as_name or module_name), _parent=import_, filename=self.filename
                        )
                    )

        for _name in import_._names:
            handler.store(_name)

    def visitList(self, list, handler):

        "Process the given 'list' node using the given 'handler'."

        self.depth_first(list, handler)
        self.reset_specialisations(list)

        list_class = handler.builtins["list"][0]

        # Make a reference to the class.
        # NOTE: This should be made dependent on the self argument.

        ref = self.instantiator.instantiate_class(list_class, list)
        args = [ref]

        # NOTE: Find the first __init__ method.

        if list_class._namespace.has_key("__init__"):
            method = list_class._namespace["__init__"][0]

            # Make a specialisation.

            self.call_specialisation(list, method, args,
                "new", handler)

        # NOTE: Call the first append method.

        append_method = list_class._namespace["append"][0]

        calls = getattr(list, "_calls", [])
        for node, call in map(None, list.nodes, calls):

            # Make a wrapper around the node as a place to add the call to the
            # append method.

            if call is None:
                call = self.graph.helper(node, _parent=list, filename=self.filename)
                calls.append(call)

            self.reset_specialisations(call)
            method_args = [ref, node]

            # Using top as refcontext to use the recently instantiated list
            # object.

            self.call_specialisation(call, append_method, method_args, "top",
                handler)

        list._calls = calls
        self.graph.merge(list, ref)

    def visitName(self, name, handler):

        "Process the given 'name' node using the given 'handler'."

        handler.load(name)

    def visitNot(self, not_, handler):

        "Process the given 'not_' node using the given 'handler'."

        not_.expr._parent = not_
        self.dispatch(not_.expr, handler)
        self.reset_specialisations(not_)

        # NOTE: Not particularly sure about this, but if there is an optimised
        # NOTE: value (from SPECIAL functions), propagate it here inverted.

        if hasattr(not_.expr, "_optimised_value"):
            not_._optimised_value = not not_.expr._optimised_value
            if lobj(not_.expr, strict=1) == [self.true]:
                self.graph.merge_item(not_, None, self.false)
                return
            elif lobj(not_.expr, strict=1) == [self.false]:
                self.graph.merge_item(not_, None, self.true)
                return
            else:
                # NOTE: This should not occur!
                pass

        # Create a wrapper around the expression and use it to construct the
        # call to __true__.

        if not hasattr(not_, "_true_call"):
            call = self.graph.helper(not_.expr, _parent=not_, filename=self.filename)
        else:
            call = not_._true_call

        self.reset_specialisations(call)
        self.attach_true(call, call.expr, "top", handler)

        # Add the negation operation.

        method = handler.builtins["__not__"][0]
        for obj in lobj(call, strict=1):
            method_args = [obj]
            self.call_specialisation(not_, method, method_args, "top", handler)

        not_._true_call = call

    def visitOr(self, or_, handler):

        "Process the given 'or_' node using the given 'handler'."

        self.depth_first(or_, handler)

        nodes = getattr(or_, "_nodes", [])
        for node, helper in map(None, or_.nodes, nodes):
            self.graph.merge(or_, node)

            # Introduce a helper node for the __true__ invocation.

            if helper is None:
                helper = self.graph.helper(node, _parent=or_, filename=self.filename)
                nodes.append(helper)
            self.reset_specialisations(helper)
            self.attach_true(helper, node, "top", handler)

        or_._nodes = nodes

    def visitPrint(self, print_, handler):

        "Process the given 'print_' node using the given 'handler'."

        # NOTE: Do not yet handle writing to streams.

        self.depth_first(print_, handler)

        calls = getattr(print_, "_calls", [])
        for node, call in map(None, print_.nodes, calls):
            if call is None:
                call = self.graph.helper(node, _parent=print_, filename=self.filename)
                calls.append(call)
            self.reset_specialisations(call)

            for expr_input in lobj(node, strict=1):
                if expr_input._namespace.has_key("__str__"):
                    methods = expr_input._namespace["__str__"]
                elif expr_input._class._namespace.has_key("__str__"):
                    methods = expr_input._class._namespace["__str__"]
                else:
                    methods = []

                method_args = [expr_input]
                for method in methods:
                    self.call_specialisation(call, method, method_args, "top",
                        handler)

        print_._calls = calls

    visitPrintnl = visitPrint

    def visitReturn(self, return_, handler):

        "Process the given 'return_' node using the given 'handler'."

        self.depth_first(return_, handler)

        self.graph.merge(return_, return_.value)
        handler.return_node(return_)

    def visitStmt(self, stmt, handler):

        "Process the given 'stmt' node using the given 'handler'."

        child_nodes = list(stmt.getChildNodes())

        for child_node in child_nodes:

            # For convenience, add the parent node.

            child_node._parent = stmt

            try:
                self.dispatch(child_node, handler)

            except self.graph.BlockedError, (to_node, from_node):
                handler.add_blocked_node(to_node)
                self.current_blockages.append(from_node)

            except self.graph.AlsoBlockedError, from_node:
                pass

    def visitSlice(self, slice, handler):

        "Process the given 'slice' node using the given 'handler'."

        self.depth_first(slice, handler)
        self.reset_specialisations(slice)

        # Create a node for default argument purposes.

        if not hasattr(slice, "_none"):
            slice._none = compiler.ast.Name("None")
            self.dispatch(slice._none, handler)

        for expr_input in lobj(slice.expr, strict=1):
            if expr_input._namespace.has_key("__getslice__"):
                methods = expr_input._namespace["__getslice__"]
            elif expr_input._class._namespace.has_key("__getslice__"):
                methods = expr_input._class._namespace["__getslice__"]
            else:
                methods = []

            # Need the actual expression node as an argument.

            method_args = [expr_input]
            if slice.lower is not None:
                method_args.append(slice.lower)
            else:
                # This must be a genuine node since it is processed as such
                # by the visitors.

                method_args.append(slice._none)

            if slice.upper is not None:
                method_args.append(slice.upper)
            else:
                # This must be a genuine node since it is processed as such
                # by the visitors.

                method_args.append(slice._none)

            for method in methods:
                self.call_specialisation(slice, method, method_args, "top",
                    handler)

    def visitSubscript(self, subscript, handler):

        "Process the given 'subscript' node using the given 'handler'."

        self.depth_first(subscript, handler)
        self.reset_specialisations(subscript)

        for expr_input in lobj(subscript.expr, strict=1):
            if expr_input._namespace.has_key("__getitem__"):
                methods = expr_input._namespace["__getitem__"]
            elif expr_input._class._namespace.has_key("__getitem__"):
                methods = expr_input._class._namespace["__getitem__"]
            else:
                methods = []

            # Need the actual expression node as an argument.

            method_args = [expr_input] + subscript.subs
            for method in methods:
                self.call_specialisation(subscript, method, method_args, "top",
                    handler)

    # NOTE: This is like visitList, but use of an append method is not really
    # NOTE: appropriate for a tuple.

    def visitTuple(self, tuple, handler):

        "Process the given 'tuple' node using the given 'handler'."

        self.depth_first(tuple, handler)
        self.reset_specialisations(tuple)

        tuple_class = handler.builtins["tuple"][0]

        # Make a reference to the class.
        # NOTE: This should be made dependent on the self argument.

        ref = self.instantiator.instantiate_class(tuple_class, tuple)
        args = [ref]

        # NOTE: Find the first __init__ method.

        if tuple_class._namespace.has_key("__init__"):
            method = tuple_class._namespace["__init__"][0]

            # Make a specialisation.

            self.call_specialisation(tuple, method, args,
                "new", handler)

        # NOTE: Call the first append method.

        append_method = tuple_class._namespace["append"][0]

        calls = getattr(tuple, "_calls", [])

        for node, call in map(None, tuple.nodes, calls):

            # Make a wrapper around the node as a place to add the call to the
            # append method.

            if call is None:
                call = self.graph.helper(node, _parent=tuple, filename=self.filename)
                calls.append(call)

            self.reset_specialisations(call)
            method_args = [ref, node]

            # Using top as refcontext to use the recently instantiated tuple
            # object.

            self.call_specialisation(call, append_method, method_args, "top",
                handler)

        tuple._calls = calls
        self.graph.merge(tuple, ref)

    def visitWhile(self, while_, handler):

        "Process the given 'while_' node using the given 'handler'."

        # For convenience, add the parent node.

        while_.test._parent = while_
        while_.body._parent = while_

        # NOTE: Should loop over the body (and possibly the test which should also
        # NOTE: be affected by the modified namespace). The else clause should be
        # NOTE: affected by the modifications to the namespace.

        self.current_specialisations.append(while_)
        try:
            while 1:
                while_._counter = self.graph.counter
                self.process_conditional(while_.test, handler, handler.locals, handler.filtered_locals)

                # Add a helper which wraps the test in a __true__ invocation.

                if not hasattr(while_, "_test"):
                    helper = self.graph.helper(while_.test, _parent=while_, filename=self.filename)
                else:
                    helper = while_._test

                self.reset_specialisations(helper)
                self.attach_true(helper, while_.test, "top", handler)
                while_._test = helper

                self.process_conditional(while_.body, handler, handler.locals, handler.filtered_locals)
                if while_._counter == self.graph.counter:
                    break
        finally:
            self.current_specialisations.pop()

        if while_.else_ is not None:
            while_.else_._parent = while_
            self.process_conditional(while_.else_, handler, handler.locals, handler.filtered_locals)

    # Internal methods.

    def attach_error(self, node, error_name, handler):

        """
        Attach an annotation to 'node' indicating that an error of the given
        'error_name' may be raised, using the given 'handler' to locate the
        named class.
        """

        error_class = handler.builtins[error_name][0]
        self.instantiator.instantiate_class(error_class, node, "_raises")

    def attach_true(self, node, arg, refcontext, handler):

        """
        On the given 'node', attach invocations of the __true__ method for the
        given 'arg', defining 'refcontext' for the invocations, and using the
        given 'handler'.
        """

        # Attach __true__ calls to each of the nodes.

        methods_found = 0
        expr_inputs = lobj(arg, strict=1)
        undesirable_targets = []

        for expr_input in expr_inputs:
            if expr_input._namespace.has_key("__true__"):
                methods = expr_input._namespace["__true__"]
            elif expr_input._class._namespace.has_key("__true__"):
                methods = expr_input._class._namespace["__true__"]
            else:
                methods = []

            # Provide a specialised version of the argument.

            method_args = [expr_input]

            for method in methods:
                try:
                    self.call_specialisation(node, method, method_args, refcontext,
                        handler)
                    methods_found = 1
                except InvalidTargetError, exc:
                    undesirable_targets.append(exc)
                except NoTargetsError, exc:
                    undesirable_targets.append(exc)

        if not methods_found:
            raise NoTargetsError, (node, self.current_callers[:], undesirable_targets)

    def attach_iteration(self, node, arg, refcontext, handler):

        """
        On the given 'node', attach access to the __iter__ method of the given
        'arg', using the 'refcontext' to indicate the meaning of the reference,
        as well as the 'handler'.
        """

        methods_found = 0
        objs = lobj(arg, strict=1)
        undesirable_targets = []

        for obj in objs:

            # Access an iterator on the expression.
            # ie. iter = expr.__iter__()

            if obj._namespace.has_key("__iter__"):
                methods = obj._namespace["__iter__"]
            elif obj._class._namespace.has_key("__iter__"):
                methods = obj._class._namespace["__iter__"]
            else:
                continue

            # Provide a specialised version of the argument.

            for method in methods:
                try:
                    self.call_specialisation(node, method, [obj], refcontext, handler)
                    methods_found = 1
                except InvalidTargetError, exc:
                    undesirable_targets.append(exc)
                except NoTargetsError, exc:
                    undesirable_targets.append(exc)

        if not methods_found:
            raise NoTargetsError, (node, self.current_callers[:], undesirable_targets)

    def attach_next_iteration(self, node, arg, handler):

        """
        On the given 'node', attach a call to the next method of an iterator
        found on the given 'arg', using the given 'handler'.
        """

        # Find appropriate access methods.

        methods_found = 0
        iter_objs = lobj(arg, strict=1)
        undesirable_targets = []

        for iter_obj in iter_objs:

            # Access a next method on an iterator.
            # ie. iter.next()

            if iter_obj._namespace.has_key("next"):
                next_methods = iter_obj._namespace["next"]
            elif iter_obj._class._namespace.has_key("next"):
                next_methods = iter_obj._class._namespace["next"]
            else:
                continue

            # Attach a specialisation call to the node, indicating the means of
            # accessing the assignment expression.

            for next_method in next_methods:

                # Provide a specialised version of the argument.

                try:
                    self.call_specialisation(node, next_method, [iter_obj], "top",
                        handler)
                    methods_found = 1
                except InvalidTargetError, exc:
                    undesirable_targets.append(exc)
                except NoTargetsError, exc:
                    undesirable_targets.append(exc)

        if not methods_found:
            raise NoTargetsError, (node, self.current_callers[:], undesirable_targets)

    def process_conditional(self, block, handler, modified_locals, modified_filtered_locals):

        """
        Process the conditional 'block' using the given 'handler'.
        Store modifications to the namespace in the 'modified_locals' dictionary.
        """

        # Preserve locals by copying the dictionaries.

        locals = {}
        locals.update(handler.locals)
        filtered_locals = {}
        filtered_locals.update(handler.filtered_locals)

        # Make a separate handler for this block.

        new_handler = NamespaceRegister(self.graph, filtered_locals, locals,
            handler.globals, handler.builtins,
            name_qualifier=handler.name_qualifier, name_context=handler.name_context,
            module_name=handler.module_name)

        self.dispatch(block, new_handler)

        # Merge locals back into handler here.
        # NOTE: This may not deal with global definitions properly.

        self.merge_locals(modified_locals, new_handler.locals)

        # NOTE: Need to find a way of merging filtered locals from the block
        # NOTE: into its parent.

        #self.merge_locals(modified_filtered_locals, new_handler.filtered_locals)

        # Capture results from the local handler.

        handler.return_nodes += new_handler.return_nodes
        handler.blocked_nodes += new_handler.blocked_nodes

    def merge_locals(self, modified_locals, locals):

        """
        Add entries to the given 'modified_locals' dictionary by examining the
        'locals'.
        """

        for name, values in locals.items():

            # Initialise the entry.

            if not modified_locals.has_key(name):

                # If the modified locals do not already have a record for this
                # name, yet a block has already been processed, add an undefined
                # value to the entry.

                if hasattr(modified_locals, "first") and modified_locals.first:
                    modified_locals[name] = []
                else:
                    modified_locals[name] = [self.undefined]

            # Append alternative values.

            for value in values:
                if value not in modified_locals[name]:
                    modified_locals[name].append(value)

        # Add undefined values for names not used in the current block.

        self.merge_undefined(modified_locals, locals)

        # Set the modified flag where appropriate.

        if hasattr(modified_locals, "first"):
            modified_locals.first = 0

    def merge_undefined(self, modified_locals, locals=None):

        """
        Add undefined values for all entries in the given 'modified_locals' not
        found in the given 'locals'.
        """

        locals = locals or {}

        for name, values in modified_locals.items():
            if not locals.has_key(name) and self.undefined not in values:
                values.append(self.undefined)

    def process_unary_operator(self, operator, handler):

        "Process the given 'operator' node using the given 'handler'."

        self.depth_first(operator, handler)
        method_name = analysis.operators.get_unary_method(operator)

        # Make specialisations.

        self.reset_specialisations(operator)

        expr_inputs = lobj(operator.expr, strict=1)
        method_args = [operator.expr]

        undesirable_inputs = []
        undesirable_targets = []
        methods_found = 0

        for expr_input in expr_inputs:
            if expr_input._namespace.has_key(method_name):
                methods = expr_input._namespace[method_name]
            elif expr_input._class._namespace.has_key(method_name):
                methods = expr_input._class._namespace[method_name]
            else:
                methods = []

            if methods != []:

                # Make a specialisation for the operation method.

                for method in methods:
                    try:
                        self.call_specialisation(operator, method, method_args, "top", handler)
                        methods_found = 1
                    except UnboundLocalError, exc:
                        if exc.args[0] == "TypeConstraintError":
                            if expr_input not in undesirable_inputs:
                                undesirable_inputs.append(expr_input)
                                handler.filter(operator.expr, expr_input)
                        else:
                            raise
                    except InvalidTargetError, exc:
                        undesirable_targets.append(exc)
                    except NoTargetsError, exc:
                        if expr_input not in undesirable_inputs:
                            undesirable_inputs.append(expr_input)
                            handler.filter(operator.expr, expr_input)
                        undesirable_targets.append(exc)
            else:
                if expr_input not in undesirable_inputs:
                    undesirable_inputs.append(expr_input)
                    handler.filter(operator.expr, expr_input)

        operator._undesirable = undesirable_inputs

        # Filter out undesirable accesses from the types associated with the
        # expression, if this is feasible.

        for obj in operator._undesirable:
            handler.filter(operator.expr, obj)

        if operator._undesirable:
            self.attach_error(operator, "TypeError", handler)

        if not methods_found:
            raise NoTargetsError, (operator, self.current_callers[:], undesirable_targets)

    def process_binary_operator(self, operator, handler, strict=1):

        """
        Process the given 'operator' node using the given 'handler'. If the
        optional 'strict' parameter is set to a true value (as is the default),
        treat incompatible types as undesirable inputs to the operator.
        """

        self.depth_first(operator, handler)

        # Get the method names.

        left_method_name, right_method_name = analysis.operators.get_binary_methods(operator)

        self._process_binary_operator(operator, operator.left, operator.right,
            left_method_name, right_method_name, "left-right", "right-left", handler, strict)

    def _process_binary_operator(self, node, left, right, left_method_name, right_method_name, left_refcontext, right_refcontext, handler, strict=1):

        """
        Process the binary operator 'node', with the given 'left' and 'right'
        hand side arguments, the specified 'left_method_name' and
        'right_method_name', 'left_refcontext' and 'right_refcontext', and the
        given 'handler'.
        If the optional 'strict' parameter is set to a true value (as is the
        default), treat incompatible types as undesirable inputs to the
        operator.
        """

        self.reset_specialisations(node)

        left_inputs = lobj(left, strict=1)
        right_inputs = lobj(right, strict=1)

        # Remember details of left-right combinations that do not work, such
        # combinations that do work, and whether we found any methods for a
        # left operand.

        incapable_combinations = []
        capable_combinations = []
        undesirable_targets = []
        methods_found = 0

        for left_input in left_inputs:

            # Left operand supports the operation.

            if left_input._namespace.has_key(left_method_name):
                methods = left_input._namespace[left_method_name]
            elif left_input._class._namespace.has_key(left_method_name):
                methods = left_input._class._namespace[left_method_name]
            else:
                methods = []

            if methods != []:
                for right_input in right_inputs:
                    method_args = [left_input, right_input]

                    # Make a specialisation for the operation method.

                    for method in methods:
                        try:
                            self.call_specialisation(node, method, method_args,
                                left_refcontext, handler)
                            methods_found = 1
                            if (left_input, right_input) not in capable_combinations:
                                capable_combinations.append((left_input, right_input))
                        except UnboundLocalError, exc:
                            if exc.args[0] == "TypeConstraintError":
                                if (left_input, right_input) not in incapable_combinations:
                                    incapable_combinations.append((left_input, right_input))
                            else:
                                raise
                        except InvalidTargetError, exc:
                            undesirable_targets.append(exc)
                        except NoTargetsError, exc:
                            if (left_input, right_input) not in incapable_combinations:
                                incapable_combinations.append((left_input, right_input))
                            undesirable_targets.append(exc)

            else:
                for right_input in right_inputs:
                    if (left_input, right_input) not in incapable_combinations:
                        incapable_combinations.append((left_input, right_input))

        # Handle cases where the left input does not have the appropriate method.

        undesirable_combinations = []
        for (left_input, right_input) in incapable_combinations:

            # Right operand supports the operation.

            if right_input._namespace.has_key(right_method_name):
                methods = right_input._namespace[right_method_name]
            elif right_input._class._namespace.has_key(right_method_name):
                methods = right_input._class._namespace[right_method_name]
            else:
                methods = []

            if methods != []:
                method_args = [right_input, left_input]

                # Make a specialisation for the operation method.

                for method in methods:
                    try:
                        self.call_specialisation(node, method,
                            method_args, right_refcontext, handler)
                        methods_found = 1
                        if (left_input, right_input) not in capable_combinations:
                            capable_combinations.append((left_input, right_input))
                    except UnboundLocalError, exc:
                        if exc.args[0] == "TypeConstraintError":
                            if (left_input, right_input) not in undesirable_combinations:
                                undesirable_combinations.append((left_input, right_input))
                        else:
                            raise
                    except InvalidTargetError, exc:
                        undesirable_targets.append(exc)
                    except NoTargetsError, exc:
                        if (left_input, right_input) not in incapable_combinations:
                            undesirable_combinations.append((left_input, right_input))
                        undesirable_targets.append(exc)
            else:
                if (left_input, right_input) not in undesirable_combinations:
                    undesirable_combinations.append((left_input, right_input))

        node._undesirable_combinations = undesirable_combinations

        # Filter out undesirable accesses from the types associated with the
        # operation, if this is feasible (and desirable).

        if strict:
            capable_left = []
            capable_right = []
            for left_input, right_input in capable_combinations:
                if left_input not in capable_left:
                    capable_left.append(left_input)
                if right_input not in capable_right:
                    capable_left.append(right_input)

            undesirable = []
            for left_input, right_input in undesirable_combinations:
                if left_input not in capable_left:
                    handler.filter(left, left_input)
                    undesirable.append(left_input)
                if right_input not in capable_right:
                    handler.filter(right, right_input)
                    undesirable.append(right_input)

            if undesirable:
                self.attach_error(node, "TypeError", handler)

        # Create a node for default result purposes.

        elif not hasattr(node, "_default"):
            node._default = compiler.ast.Name("False")
            self.dispatch(node._default, handler)
            self.graph.merge(node, self.false)

        if not methods_found and strict:
            raise NoTargetsError, (node, self.current_callers[:], undesirable_targets)

    def get_context_args(self, node, obj):

        """
        For the given 'node', add the self argument as defined by 'obj'.
        """

        if obj is not None and isinstance(obj, analysis.reference.Reference):
            # NOTE: Hack! This may be a tuple!
            args = list(node.args[:])
            args.insert(0, obj)
            args = tuple(args)
        else:
            args = node.args
        return args

    def make_const(self, instantiator, value):

        """
        Make a new constant for use by the 'instantiator', having the given 'value'.
        """

        const = compiler.ast.Const(value, instantiator.lineno)
        return const

    def get_const_ref(self, const, definition):

        """
        Get the reference to a constant using the given 'const' node and the
        'definition' of the constant type as found in the built-in types.
        """

        ref = self.instantiator.instantiate_class(definition, const)

        # Add the constants to the constants table.

        if const.value not in self.current_module._constants_table:
            self.current_module._constants_table.append(const.value)

        return ref

    def reset_specialisations(self, caller):

        """
        For the given 'caller', reset the specialisations associated with that
        node.
        """

        # Remember called specialisations.

        caller._targets = []

        # We remember arguments used for each specialisation here.

        caller._signatures = []
        caller._locals = []
        caller._argnames = []
        caller._argnodes_keys = []

        # The argument nodes dictionary maps methods to namespaces/parameters.
        # NOTE: This prevents star arg lists being created continually.

        if not hasattr(caller, "_argnodes"):
            caller._argnodes = {}

        # We also remember the context of any reference arguments.

        caller._refcontexts = []

    def call_specialisation(self, caller, method, args, refcontext, handler, star_args=None, dstar_args=None):

        """
        On the given 'caller' node, invoke the given 'method' with the given
        'args', using the specified 'refcontext' to define the meaning of any
        references involved and the 'handler' to provide namespace information.
        The optional 'star_args' and 'dstar_args' may be used to provide
        additional argument information.

        Establish the special _targets attribute on 'caller', and link results
        to that node.
        """

        # Reject non-callables.
        # NOTE: Improve/verify!

        if not isinstance(method, compiler.ast.Function):
            raise InvalidTargetError, (method, self.current_callers[:])

        # Add support for isinstance and other compile-time optimisations.

        if method.doc is not None and has_docstring_annotation(method, "SPECIAL"):
            if self.optimise_specialisation(caller, method, args, handler):
                return

        # Prepare the arguments, unify them with the parameters, specialise the
        # given function, and link to the result.
        # This caches the unified parameters, avoiding repeated instantiation of
        # default or constructed objects, but has to depend on more than just
        # the method in order to support binary operators.
        # NOTE: Need to include star_args, dstar_args.

        argnodes_key = (tuple(args), method)

        if caller._argnodes.has_key(argnodes_key):
            ns, defaults, star_values, dstar_values = caller._argnodes[argnodes_key]
        else:
            star_args = star_args or []
            dstar_args = dstar_args or []
            ns, defaults, star_values, dstar_values = analysis.arguments.unify_arguments(args, star_args, dstar_args, method)

        # Process the returned value lists, resolving references to names or constants.

        for values in (defaults, star_values, dstar_values):
            for value in values:
                value._parent = caller
                self.dispatch(value, handler)

        # Get a set of locals from the argument/parameter unification, "sealing"
        # them so that their types remain independent from the original nodes.

        locals = self.specialiser.make_locals(ns)

        # Here, the locals (typically the parameters) are "cached" using signatures
        # for faster lookup.

        signature = self.specialiser.make_signature(locals)

        # Either get an existing specialisation or create a new one.

        spec = self.specialiser.get_specialisation(caller, method, locals, signature, add_to_module=1)
        if spec is None:
            raise NoTargetsError, (caller, self.current_callers[:])

        try:
            # If this specialisation is already being processed (due to recursion),
            # do not process it again.

            if spec in self.current_specialisations:
                pass

            # Specialise the function and then merge the results into the caller.

            else:
                self.process_specialisation(caller, spec, method, locals, handler)

            # If the specialisation is already being processed and has no results,
            # a blockage will occur and the call will be aborted.

            self.graph.merge(caller, spec, blocking=1)

        except self.graph.BlockedError:
            #self._show_spec("Blocked on", spec)
            raise

        except self.graph.AlsoBlockedError:
            #self._show_spec("Also blocked on", spec)
            raise

        except NoTargetsError:
            raise

        # Then link to the results of each specialisation.
        # We need to permit multiple argument specifications referring to the
        # same target since recursive calls within methods may map different
        # references to the same method.

        if not (self.specialiser.is_signature_in_list(signature, caller._signatures) and spec in caller._targets):
            caller._targets.append(spec)
            caller._signatures.append(spec._signature)
            caller._locals.append(locals)
            caller._argnames.append(spec.argnames)
            caller._refcontexts.append(refcontext)
            caller._argnodes_keys.append(argnodes_key)
            caller._argnodes[argnodes_key] = ns, defaults, star_values, dstar_values

    def optimise_specialisation(self, caller, method, args, handler):

        """
        Using the given 'caller' node, 'method' node, 'args' and namespace 'handler'
        determine whether the call can be optimised at compile time, returning a
        true value and linking the 'caller' appropriately to the optimised result
        value if possible; otherwise, a false value is returned.
        """

        # NOTE: To remove previous, now possibly invalid, inferences.

        if hasattr(caller, "_optimised_value"):
            delattr(caller, "_optimised_value")

        if method.name == "isinstance":
            obj, cls_ref_node = args[0:2]

            # Where the object is always an instance of one of the given classes,
            # link directly to a true value. Where the object is never an instance
            # of one of those classes, link directly to a false value. Otherwise,
            # process the specialisation.

            is_subclass = None

            # Get each class...

            for cls in lobj(cls_ref_node, strict=1):

                # Get each object type/class...

                for obj_cls in ltype(obj):
                    obj_cls_is_subclass = analysis.classes.issubclass(obj_cls, cls)

                    # If not a subclass, if this contradicts previous tests then the
                    # status is undecided.

                    if not obj_cls_is_subclass:
                        if is_subclass == 1:
                            is_subclass = None
                            break
                        else:
                            is_subclass = 0

                    # If a subclass, if this contradicts previous tests then the
                    # status is undecided.

                    elif obj_cls_is_subclass:
                        if is_subclass == 0:
                            is_subclass = None
                            break
                        else:
                            is_subclass = 1

            if is_subclass == 1:
                self.graph.merge_item(caller, None, self.true)
                caller._optimised_value = 1
                return 1
            elif is_subclass == 0:
                self.graph.merge_item(caller, None, self.false)
                caller._optimised_value = 0
                return 1

        # Otherwise, process the specialisation...

        return 0

    # Special AST transformations.

    def process_specialisation(self, caller, specialisation, function, locals, handler):

        """
        Process the given 'function' node using the given 'locals' namespace and the
        given 'handler', producing a specialised version of the function and
        returning a node for that specialisation.
        """

        self.current_specialisations.append(specialisation)
        self.current_callers.append(caller)

        # Switch to the specialisation's signature.

        signature = specialisation._signature

        # Loop until the specialisation is no longer blocking.

        try:
            while 1:
                #self._stack()
                specialisation._counter = self.graph.counter
                self.run_specialisation(specialisation, function, handler)

                if specialisation in self.current_blockages:
                    self.current_blockages.remove(specialisation)
                    #self._show_spec("Retrying", specialisation)
                elif self.current_blockages or specialisation._counter == self.graph.counter:
                    break
                else:
                    #self._show_counter(specialisation)
                    pass

        finally:

            # Remove the specialisation from the list of those being processed.

            self.current_specialisations.pop()
            self.current_callers.pop()

        return specialisation

    def run_specialisation(self, specialisation, function, handler):

        # Duplicate the locals in order to avoid modification issues.

        locals = {}
        locals.update(specialisation._locals)

        # Shorthand...

        qualified_name = specialisation._qualified_name

        # Prepare a new namespace for the specialisation.

        new_handler = NamespaceRegister(self.graph, {}, locals, function._globals, handler.builtins,
            specials=function._specials,
            name_qualifier=qualified_name, name_context="function",
            module_name=function._module_name)

        self.process_block(specialisation, new_handler)

        # Attach result information to the specialisation.

        if new_handler.return_nodes:
            #self._show_return(specialisation, repr(new_handler.return_nodes))
            for return_node in new_handler.return_nodes:
                self.graph.merge(specialisation, return_node)

        # Detect functions with no ready results.

        elif new_handler.blocked_nodes:
            #self._show_return(specialisation, "No results")
            self.graph.reset(specialisation)
            if not specialisation in self.current_blockages:
                raise self.graph.AlsoBlockedError, specialisation

        # Detect functions with no apparently ready results.

        elif getattr(specialisation, "_returns", []):
            self.graph.reset(specialisation)
            raise self.graph.AlsoBlockedError, specialisation

        # Detect non-constructor functions with no results whatsoever.

        elif hasattr(function, "name") and function.name != "__init__":
            #self._show_return(specialisation, "None")
            self.graph.merge(specialisation, self.none)

        else:
            #self._show_return(specialisation, "Reset")
            self.graph.reset(specialisation)

    # Debugging methods.

    def _show_return(self, specialisation, msg):
        print >>sys.stderr, getattr(specialisation, "_qualified_name", "None")
        print >>sys.stderr, "->", msg

    def _stack(self):
        for spec in self.current_specialisations:
            if spec in self.current_blockages:
                print >>sys.stderr, "*",
            else:
                print >>sys.stderr, " ",
            print >>sys.stderr, getattr(spec, "_qualified_name", spec.__class__.__name__)
            print >>sys.stderr, "    " + repr(getattr(spec, "_signature", None))
        print >>sys.stderr

    def _show_spec(self, msg, spec):
        print >>sys.stderr, msg, spec._qualified_name
        print >>sys.stderr

    def _show_counter(self, spec):
        print >>sys.stderr, "New contexts for", spec._qualified_name, ":", self.graph.counter - spec._counter
        print >>sys.stderr

class AnalysisSession:

    """
    A class whose objects hold information related to the above
    AnalysisVisitor class.
    """

    def __init__(self):
        self.builtins = None
        self.current_filenames = []
        self.modules = {}

    def process_builtins(self):

        "Process the builtins module, obtained from a special location."

        if self.builtins is None:
            filename = os.path.join("lib", "builtins.py")
            builtins = compiler.parseFile(filename)
            visitor = AnalysisVisitor(self, filename=filename)
            compiler.walk(builtins, visitor, visitor)
            self.builtins = builtins

            # Set the filename on the completed tree.

            compiler.misc.set_filename(filename, builtins)

            # Define the special values.
            # NOTE: If more than one reference per class becomes permitted, this
            # NOTE: workaround will no longer be necessary and it will become possible
            # NOTE: to just get False and True from the built-in definitions.

            builtins_ns = self.builtins._namespace
            builtins_ns["False"] = [analysis.reference.Reference(builtins_ns["boolean"][0], "False")]
            builtins_ns["True"] = [analysis.reference.Reference(builtins_ns["boolean"][0], "True")]
            builtins_ns["Undefined"] = [analysis.reference.Reference(builtins_ns["undefined"][0], "Undefined")]
            builtins_ns["None"] = [analysis.reference.Reference(builtins_ns["none"][0], "None")]

    def process(self, s):

        "Process the string 's', returning a module root node."

        self.process_builtins()
        module = compiler.parse(s)
        visitor = AnalysisVisitor(self)
        compiler.walk(module, visitor, visitor)
        return module

    def process_file(self, filename):

        """
        Process the file with the given 'filename', returning a module root
        node.
        """

        self.process_builtins()
        return self._process_file(filename)

    def _process_file(self, filename):

        # Set the filename in this module because set_filename only works on
        # completed trees.

        self.current_filenames.append(filename)

        module = compiler.parseFile(filename)
        module_name = self.get_module_name(filename)
        visitor = AnalysisVisitor(self, filename=filename, module_name=module_name)
        compiler.walk(module, visitor, visitor)

        # Remember the module and remove the module from the list of those
        # currently being processed.

        self.modules[module_name] = module
        self.current_filenames.pop()

        # Set the filename on the completed tree.

        compiler.misc.set_filename(filename, module)
        return module

    def process_name(self, module_name):

        """
        Process the module identified by the given 'module_name'. This involves
        the importing of the named module whose root node is then returned. An
        ImportError is raised if the module could not be located.
        """

        # NOTE: To be completed.
        for d in ["tests", "lib"]:
            pathname = os.path.join(d, module_name + os.path.extsep + "py")
            if os.path.exists(pathname):
                return self.process_file(pathname)
        raise ImportError, module_name

    # Utility functions.

    def get_module_name(self, filename):
        parts = []
        head, ext = os.path.splitext(filename)
        head, tail = os.path.split(head)
        return tail

    def get_entry(self, node):
        filename, lineno = self.get_lineno(node)
        line = self.get_line(filename, lineno)
        function = analysis.specialisation.get_containing_specialisation(node)
        qname = getattr(function, "_qualified_name", "?")
        signature = getattr(function, "_signature", "?")
        return '  File "%s", line %d, in %s %s\n    %s\n' % (filename, lineno, qname, signature, line.strip())

    def get_line(self, filename, lineno):
        if filename is None:
            return ""

        f = open(filename)
        lines = f.readlines()
        f.close()
        try:
            return lines[lineno - 1]
        except IndexError:
            return ""

    def get_lineno(self, node):
        if hasattr(node, "filename"):
            filename = node.filename
        else:
            filename = self.current_filenames[-1]
        return filename, node.lineno

    # The big reset button - use this before starting to compile or process a new
    # program.

    def reset(self):
        self.builtins = None

# One-off functions.

def process(s):

    "Process the string 's', returning a module root node."

    session = AnalysisSession()
    return session.process(s)

def process_file(filename):

    "Process the file with the given 'filename', returning a module root node."

    session = AnalysisSession()
    return session.process_file(filename)

# vim: tabstop=4 expandtab shiftwidth=4
