#!/usr/bin/env python

"""
Node manipulations.

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

class BlockedError(Exception):
    pass

class AlsoBlockedError(Exception):
    pass

class HelperNode:
    def __init__(self, graph, expr, **kw):
        self.graph = graph
        self.expr = expr
        for key, value in kw.items():
            setattr(self, key, value)
        self.graph.merge(self, expr)
        self.lineno = self.expr.lineno
        self.filename = getattr(self.expr, "filename", None) or getattr(self, "filename", None)
    def __repr__(self):
        return "<HelperNode dict: %s>" % self.__dict__

class Graph:

    BlockedError = BlockedError
    AlsoBlockedError = AlsoBlockedError
    HelperNode = HelperNode

    def __init__(self):
        self.counter = 0

    def reset(self, node):
        if not hasattr(node, "_contexts"):
            node._contexts = {}

    def helper(self, expr, **kw):
        return HelperNode(self, expr, **kw)

    def block(self, node):
        if hasattr(node, "_contexts"):
            delattr(node, "_contexts")

    def merge(self, target, source, blocking=0):

        """
        Link between 'target' and 'source', copying the contexts of 'source'
        into 'target'.

        If the optional 'blocking' parameter is set to a true value, raise an
        exception if 'source' has no contexts defined. Otherwise, where no contexts
        are defined, none are copied to 'target'.
        """

        self.reset(target)

        if hasattr(source, "_contexts"):
            context_items = source._contexts.items()
        else:
            if blocking:
                raise BlockedError, (target, source)
            else:
                context_items = [(None, [source])]
        self._merge_items(target, context_items)

    def merge_item(self, target, key, value):
        self.reset(target)
        if not target._contexts.has_key(key):
            target._contexts[key] = []
        self._merge_item(target, key, value)

    def _merge_items(self, target, context_items):
        for key, values in context_items:
            if not target._contexts.has_key(key):
                target._contexts[key] = []
            for value in values:
                self._merge_item(target, key, value)

    def _merge_item(self, target, key, value):
        if value not in target._contexts[key]:
            target._contexts[key].append(value)
            self.counter += 1
            #print "*", id(target), target

# vim: tabstop=4 expandtab shiftwidth=4
