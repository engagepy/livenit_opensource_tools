#!/usr/bin/env python

"""
Reference classes.

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

from analysis.common import has_docstring_annotation, lclassname, lname
import compiler
import sys

class Reference:
    def __init__(self, class_, identifier=None):
        self._namespace = {}
        self._class = class_
        self.name = class_._qualified_name
        self._qualified_name = self.name

    def __repr__(self):
        return "<Reference %s of type %s with name %s>" % (id(self), self._class.name, self.name)

class Instantiator:

    "Special object creation."

    def instantiate_class(self, class_, instantiator, annotation="_instantiates"):
        if not hasattr(class_, "_instances"):
            class_._instances = []

        # For interchangeable classes, return the instance associated with the class.

        if class_._instances:
            ref = class_._instances[-1]

        # For other classes, create a new instance and associate it with the class
        # and instantiator node.

        else:
            ref = Reference(class_, id(instantiator))
            class_._instances.append(ref)

        # Note the instantiation operation on the instantiator.

        if not hasattr(instantiator, annotation):
            setattr(instantiator, annotation, [])
        if class_ not in getattr(instantiator, annotation):
            getattr(instantiator, annotation).append(class_)

        return ref

def get_reference_for_class(node, cls):
    return node._instances[cls]

# vim: tabstop=4 expandtab shiftwidth=4
