#!/usr/bin/env python

"""
Class analysis.

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

from analysis.common import *
import compiler

def issubclass(cls1, cls2):

    """
    Check to see if 'cls1' is a subclass of 'cls2' (or the same class),
    returning a true value if this is the case; otherwise a false value is
    returned.
    """

    if cls1 == cls2:
        return 1

    for base in cls1.bases:
        for base_cls in lobj(base, strict=1):
            if base_cls == cls2:
                return 1
            else:
                return issubclass(base_cls, cls2)
    return 0

def get_class_layout(cls):

    """
    Return a list of tuples of the form (name, nodes) indicating the layout of
    definitions for the given class 'cls'.
    """

    return get_class_definitions(cls)

def get_class_definitions(cls):

    """
    Return a dictionary mapping names to nodes for the given class 'cls'.
    """

    return cls._namespace

def get_instance_layout(cls):

    """
    Return a list of tuples of the form (name, definition-nodes) indicating the
    layout of the structure of instances of the class 'cls'.
    """

    layout = {}
    for name, nodes in get_instance_definitions(cls).items():

        # Drop functions.

        only_methods = 1
        for node in nodes:
            if not isinstance(node, compiler.ast.Function):
                only_methods = 0
                break

        if not only_methods:
            layout[name] = nodes

    return layout

def get_instance_definitions(cls):

    """
    Return a dictionary mapping names to definitions for instances of the given
    class 'cls'.
    """

    definitions = {}
    for instance in cls._instances:
        for name, nodes in instance._namespace.items():
            if not definitions.has_key(name):
                definitions[name] = []
            for node in nodes:
                definitions[name].append(node)
    return definitions

# vim: tabstop=4 expandtab shiftwidth=4
