#!/usr/bin/env python

"""
Namespace handling.

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
from analysis.common import *

class ScopeError(Exception):

    """
    An exception indicating that a node previously associated with a particular
    scope has also been associated with another scope, thus suggesting an error
    situation.
    """

    pass

class NamespaceRegister:

    "A name register for a given namespace."

    def __init__(self, graph, filtered_locals, locals, globals, builtins,
        specials=None, name_qualifier=None, name_context=None,
        module_name=None):

        """
        Initialise the register with the following namespaces:

        'filtered_locals'   Local names whose types have been restricted by
                            the outcomes of various operations.
        'locals'            Local names as defined by parameters or assignment.
        'globals'           Global names as defined in the current module.
        'builtins'          Names of built-in types, values and functions.
        'specials'          An optional namespace principally used to provide
                            names of classes to the code within such classes.
                            Such names appear to be global to namespaces but do
                            not reside in the module global definitions.

        The optional 'name_qualifier' is used to qualify certain names.
        The optional 'name_context' is used to indicate the kind of local
        scope encapsulated by this namespace.
        The optional 'module_name' is used to remember which module a name is
        defined within.
        """

        self.graph = graph

        self.filtered_locals = filtered_locals
        self.locals = locals
        self.globals = globals
        self.builtins = builtins
        self.specials = specials or {}

        self.name_qualifier = name_qualifier
        self.name_context = name_context
        self.module_name = module_name

        self.return_nodes = []
        self.blocked_nodes = []
        self.global_names = []

    def load(self, node):

        "Find the name associated with the given 'node' in a namespace."

        self.graph.reset(node)

        found_nodes, scope = self._load_name(node.name)
        for found_node in found_nodes:
            self.graph.merge(node, found_node)

        if hasattr(node, "_scope") and node._scope != scope:
            raise ScopeError, node

        node._scope = scope
        node._name_context = self.name_context
        self.set_qualified_name(node, found_nodes)

    def _load_name(self, name):

        """
        Find the 'name' in the namespace hierarchy, returning a list of
        definitions corresponding to that name in the most local namespace
        possible, along with a scope identifier indicating in which scope the
        definitions were found.
        """

        for namespace, scope in [
            (self.filtered_locals, "locals"),
            (self.locals, "locals"), (self.specials, "specials"), (self.globals, "globals"), (self.builtins, "builtins")
            ]:
            if namespace.has_key(name):
                return namespace[name], scope

        raise UnboundLocalError, name

    def store(self, node):

        """
        Store the name associated with the given 'node' in the local namespace.
        """

        if node.name in self.global_names:
            self.globals[node.name] = [node]
            scope = "globals"
        else:
            self.locals[node.name] = [node]
            scope = "locals"

        if hasattr(node, "_scope") and node._scope != scope:
            raise ScopeError, node

        node._scope = scope
        node._name_context = self.name_context
        self.set_qualified_name(node)
        node._module_name = self.module_name

    def make_global(self, node):

        """
        Remove the name associated with the given 'node' in the local namespace.
        This is used when establishing global usage.
        """

        for name in node.names:
            if self.locals.has_key(name):
                del self.locals[name]
            #self.globals[name] = [node]
            if name not in self.global_names:
                self.global_names.append(name)

    def filter(self, node, obj):

        """
        Using the given 'node', filter 'obj' from the list of possible types
        associated with a name.
        """

        if isinstance(node, compiler.ast.Name):
            if not self.filtered_locals.has_key(node.name):
                nodes, scope = self._load_name(node.name)
                self.filtered_locals[node.name] = []
                for n in nodes:
                    for no in lobj(n, strict=1):
                        if not no in self.filtered_locals[node.name]:
                            self.filtered_locals[node.name].append(no)
            if obj in self.filtered_locals[node.name]:
                self.filtered_locals[node.name].remove(obj)

    def ensure(self, node, obj):

        """
        Using the given 'node', ensure that 'obj' is associated with a name.
        """

        if isinstance(node, compiler.ast.Name):
            if not self.filtered_locals.has_key(node.name):
                self.filtered_locals[node.name] = []
            if not obj in self.filtered_locals[node.name]:
                self.filtered_locals[node.name].append(obj)

    def return_node(self, node):
        self.return_nodes.append(node)

    def add_blocked_node(self, node):
        self.blocked_nodes.append(node)

    def set_qualified_name(self, node, found_nodes=None):

        # References to globals or anything found in a module must be qualified
        # by the module name.

        if node._scope == "globals" or (node._scope == "specials" or node._scope == "locals") and node._name_context == "module":
            node._qualified_name = self.get_global_name(node.name)

        # References to special names must involve the original qualified name.
        # NOTE: We assume that the first node is as good as any.

        elif node._scope == "specials":
            node._qualified_name = found_nodes[0]._qualified_name

        # Built-in objects are referred to via the builtins module.

        elif node._scope == "builtins":
            node._qualified_name = "builtins." + node.name

        #elif node._scope == "locals" and node._name_context == "function":
        #    node._qualified_name = node.name

        else:
            node._qualified_name = self.get_qualified_name(node.name)

    def get_qualified_name(self, name):
        if self.name_qualifier:
            return self.name_qualifier + "." + name
        else:
            return "builtins." + name

    def get_global_name(self, name):
        if self.module_name:
            return self.module_name + "." + name
        else:
            return "builtins." + name

def get_locals_layout(node, qualified_names=0, include_parameters=1):

    """
    Return a list of tuples of the form (name, definition-nodes) indicating the
    layout of parameter and local variable definitions for the given function
    (or other namespace-bearing) 'node'.
    """

    if hasattr(node, "argnames"):
        argnames = list(node.argnames[:])
    else:
        argnames = []

    # NOTE: This may not deal with name deletion.

    locals = []
    names = node._namespace.keys()
    names.sort()
    for name in names:
        if name not in argnames or include_parameters:
            if qualified_names:
                full_name = (node._qualified_name or "builtins") + "." + name
            else:
                full_name = name
            locals.append((full_name, node._namespace[name]))
    return locals

# vim: tabstop=4 expandtab shiftwidth=4
