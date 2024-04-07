#!/usr/bin/env python

"""
Common analysis functions.

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

import compiler

def ldir(node, name_str=None):

    """
    List the members of the namespace defined for 'node'. If the optional
    'node_str' is defined, use it as a path identifying objects within the
    namespace (and sub-namespaces).
    """

    if name_str is not None:
        return _ldir(node, name_str.split("."))
    else:
        return _ldir(node, [])

def _ldir(node, names):
    nodes = _lref(node, names)
    keys = []
    for node in nodes:
        namespaces = _get_ns(node)
        for namespace in namespaces:
            keys.append(namespace.keys())
    return keys

def _get_ns(node):
    if hasattr(node, "_specialisations"):
        return [spec._namespace for spec in node._specialisations]
    elif hasattr(node, "_namespace"):
        return [node._namespace]
    elif hasattr(node, "_contexts"):
        ns = []
        for attrs in node._contexts.values():
            for attr in attrs:
                ns += _get_ns(attr)
        return ns
    else:
        return []

def flatten(values):
    return reduce(lambda a, b: a + b, values, [])

def unique(values):
    d = {}
    for value in values:
        d[value] = None
    return d.keys()

def lref(node, name_str=None):

    """
    Identify nodes within the namespace defined for 'node' using the optional
    'name_str' as a path into the namespace (and sub-namespaces). If no such
    path is specified, return a list containing 'node'.
    """

    if name_str is not None:
        return _lref(node, name_str.split("."))
    else:
        return _lref(node, [])

def _lref(node, names):
    new_nodes = nodes = [node]
    for name in names:
        new_nodes = []
        for node in nodes:
            namespaces = _get_ns(node)
            for namespace in namespaces:
                new_nodes += namespace[name]
        nodes = new_nodes
    return new_nodes

def ltype(node, name_str=None):

    """
    Identify the possible types within the namespace defined for 'node' using
    the optional 'name_str' as a path into the namespace (and sub-namespaces).
    If no such path is specified, return a list containing the possible types of
    'node'.

    Return a unique list of type nodes. Note that functions are not associated
    with types and yield no such nodes.
    """

    ref_nodes = lref(node, name_str)
    types = []
    for ref_node in ref_nodes:
        types += _ltype(ref_node)
    return unique(types)

def _ltype(node):

    "Return a list of type/class nodes defining the type of the given 'node'."

    if hasattr(node, "_class"):
        return [node._class]
    elif hasattr(node, "_contexts"):
        types = []
        for attr in flatten(node._contexts.values()):
            types += _ltype(attr)
        return types
    else:

        # Functions yield this result.

        return []

def lobj(node, strict=0):

    """
    Return a list of object nodes corresponding to possible values for the given
    'node'. If the optional 'strict' parameter is set to a true value, filter
    out all nodes with no object nodes defined for them.
    """

    return unique(flatten(_lobj(node, strict)))

def _lobj(node, strict):

    """
    Return a list of lists of object nodes corresponding to possible values for
    the given 'node'.
    """

    if hasattr(node, "_contexts"):
        return node._contexts.values()
    elif not strict:
        return [[node]]
    else:
        return []

def lname(obj):
    if hasattr(obj, "_qualified_name"):
        if isinstance(obj, compiler.ast.Function):
            return "function " + obj._qualified_name
        else:
            return "class " + obj._qualified_name
    else:
        return obj.name

def lclassname(obj):
    if hasattr(obj, "_class"):
        return "class " + obj._class._qualified_name
    else:
        return lname(obj)

def has_docstring_annotation(node, name):

    """
    Return whether the given 'node' (typically a class, function or method) has
    a docstring annotation for the given 'name'.
    """

    return node.doc is not None and name in [line.strip().split(":")[0] for line in node.doc.split("\n")]

def get_docstring_name_annotation(node):

    "Return the NAME annotation from the docstring associated with 'node'."

    return node.doc.split(":")[1].split("\n")[0].strip()

# vim: tabstop=4 expandtab shiftwidth=4
