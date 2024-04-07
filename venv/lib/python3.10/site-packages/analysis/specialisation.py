#!/usr/bin/env python

"""
Creation and retrieval of specialisations.

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

import copy
import compiler
from analysis.common import *
import analysis.node
import sys

class Specialiser:

    """
    A specialiser class, providing support for the retrieval and creation of
    function specialisations.
    """

    def get_specialisation(self, caller, block, locals, signature, add_to_module):

        """
        Return a specialisation, for use by the given 'caller', for the given
        'block' having the given 'locals' and 'signature'. If no existing
        specialisation exists, create a new one.

        If the 'add_to_module' parameter is set to true, add any new
        specialisation as a sibling of the original 'block' in the module.
        """

        # Attempt to get an existing specialisation which either exactly matches the
        # signature or which covers the case expressed by the signature (as well as
        # other signatures).

        spec = self.get_existing_specialisation(caller, block, signature)
        if spec is not None:
            return spec

        # Where neither an existing specialisation nor a matching specialisation
        # exist, create a new one.

        return self.create_specialisation(block, locals, signature, add_to_module)

    def get_existing_specialisation(self, caller, block, signature):

        """
        Return whether the given 'block' has a specialisation with the given
        'signature'.
        """

        if not hasattr(block, "_specialisations"):
            return None

        for spec in block._specialisations:
            if self.are_identical_signatures(signature, spec._signature):
                return spec

        return None

    def is_signature_in_list(self, signature, signatures):

        "Return whether 'signature' is in the 'signatures' list."

        for sig in signatures:
            if self.are_identical_signatures(signature, sig):
                return 1
        return 0

    def are_identical_signatures(self, signature, spec_signature):

        "Return whether 'signature' and 'spec_signature' are identical."

        for arg_name, arg_class_names in signature.items():
            spec_arg_class_names = spec_signature[arg_name]
            spec_arg_class_names.sort()
            arg_class_names.sort()
            if arg_class_names != spec_arg_class_names:
                return 0

        return 1

    def create_specialisation(self, block, locals, signature, add_to_module):

        """
        For the specified 'block', create a new specialisation with the given
        'locals' and 'signature'.

        If the 'add_to_module' parameter is set to true, add the specialisation
        as a sibling of the original 'block' in the module.
        """

        specialisation = self.deepcopy(block)

        if not hasattr(block, "_specialisations"):
            block._specialisations = []
            block._signatures = []
            #block._locals = []

        block._specialisations.append(specialisation)
        block._signatures.append(signature)
        #block._locals.append(locals)

        # Define the name and the original block.

        if hasattr(block, "name"):
            specialisation.name = "%s___%s" % (block.name, len(block._specialisations))

            # Find a suitable qualified name. This employs fixed names for certain
            # native implementations.

            if has_docstring_annotation(specialisation, "NAME"):
                specialisation._qualified_name = get_docstring_name_annotation(specialisation)
            else:
                specialisation._qualified_name = "%s___%s" % (block._qualified_name, len(block._specialisations))

            specialisation._signature = signature
            specialisation._locals = locals
        else:
            specialisation.name = "block___%s" % len(block._specialisations)
            specialisation._qualified_name = "block___%s" % len(block._specialisations)
            specialisation._signature = signature
            specialisation._locals = locals

        # Add the specialisation to the module.

        if add_to_module:
            container = block._parent.nodes
            index = container.index(block)
            container.insert(index + 1, specialisation)
            specialisation._parent = block._parent

        # Mark the specialisation as such.

        specialisation._specialises = block
        return specialisation

    def make_signature(self, ns):

        """
        Make a signature given the namespace 'ns' using reference names.
        """

        signature = {}
        for name, nodes in ns.items():
            signature[name] = defs = []
            for node in nodes:

                # lobj used to support function references.

                for node_type in lobj(node):
                    node_class_name = lclassname(node_type)
                    if node_class_name not in defs:
                        defs.append(node_class_name)

        return signature

    def make_locals(self, ns):

        """
        Make a locals dictionary which is isolated from the actual argument nodes.
        """

        locals = {}
        for name, nodes in ns.items():
            locals[name] = defs = []
            for node in nodes:
                for node_type in lobj(node):
                    if node_type not in defs:
                        defs.append(node_type)

        return locals

    def deepcopy(self, obj, root=None):

        "Copy the given 'obj', avoiding various special protected attributes."

        if root is None:
            root = obj
            root._returns = []
        protected = ["_parent", "_specialises", "_globals", "_specials", "_specialisations", "_signatures", "_locals", "_returns", "defaults"]
        if hasattr(obj, "__dict__"):
            if isinstance(obj, compiler.ast.Return):
                root._returns.append(obj)
            new_obj = copy.copy(obj)
            for name, value in new_obj.__dict__.items():
                if name not in protected:
                    setattr(new_obj, name, self.deepcopy(getattr(new_obj, name), root))
            new_obj._original = obj
        elif type(obj) == type([]):
            new_obj = copy.copy(obj)
            for i in range(0, len(new_obj)):
                new_obj[i] = self.deepcopy(new_obj[i], root)
        elif type(obj) == type(()):
            new_obj = []
            for i in range(0, len(obj)):
                new_obj.append(self.deepcopy(obj[i], root))
            new_obj = tuple(new_obj)
        else:
            new_obj = copy.copy(obj)
        return new_obj

def get_containing_specialisation(node):
    while hasattr(node, "_parent") and not getattr(node, "_specialises", None):
        node = node._parent
    return node

# vim: tabstop=4 expandtab shiftwidth=4
