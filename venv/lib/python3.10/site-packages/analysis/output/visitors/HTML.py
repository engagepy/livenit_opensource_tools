#!/usr/bin/env python

"""
An AST visitor emitting HTML.

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
from analysis.common import lobj, lname
import textwrap # docstring processing

class HTMLVisitor(Visitor):

    """
    A simple HTML-emitting visitor which annotates the source code according to
    certain properties.
    """

    def __init__(self, generator):

        "Initialise the visitor with the given 'generator'."

        Visitor.__init__(self)
        self.generator = generator
        self.usage_limit = 4

    def _text(self, text):
        return text.replace("<", "&lt;").replace(">", "&gt;")

    def _attr(self, text):
        return self._text(text).replace("'", "&apos;").replace('"', "&quot;")

    def _keyword(self, keyword):
        self.generator.write("<span class='keyword'>")
        self.generator.write(self._text(keyword))
        self.generator.writeln("</span>")

    def _name_def(self, name, qualified_name):
        self.generator.write("<span class='name-def'>")
        self.generator.writeln("<a name='%s'>" % self._attr(qualified_name))
        self.generator.indent()
        self._name(name)
        self.generator.dedent()
        self.generator.writeln("</a>")
        self.generator.writeln("</span>")

    def _name(self, name):
        self.generator.write("<span class='name-value'>")
        self.generator.write(self._text(name))
        self.generator.writeln("</span>")

    def _qualified_name(self, node):
        if hasattr(node, "_qualified_name"):
            self.generator.write("<span class='qualified-name'>")
            self.generator.write(self._text(node._qualified_name))
            self.generator.writeln("</span>")

    def _name_ref(self, name, qualified_name, target_module_name=None):
        self.generator.writeln("<span class='name'>")
        self.generator.indent()
        self.generator.write("<span class='name-value'>")
        if target_module_name is not None:
            self.generator.write("<a href='%s.html'>" % self._attr(target_module_name))
        else:
            self.generator.write("<a href='#%s'>" % self._attr(qualified_name))
        self.generator.write(self._text(name))
        self.generator.write("</a>")
        self.generator.writeln("</span>")
        self.generator.dedent()
        self.generator.writeln("</span>")

    def _doc(self, doc):
        if doc is not None:
            self.generator.write("<pre class='body'>")
            self.generator.write('"""')
            output = textwrap.dedent(doc.replace('"""', '\\"\\"\\"'))
            self.generator.write(self._text(output))
            self.generator.write('"""')
            self.generator.writeln("</pre>")

    def _op(self, name, node):
        self.generator.write("<span class='op"); self._usage_targets(node)
        self.generator.indent()
        self.generator.write("<span class='op-value'>")
        self.generator.write(self._text(name))
        self.generator.writeln("</span>")
        self._targets(node)
        self.generator.dedent()
        self.generator.writeln("</span>")

    def _usage_targets(self, node):
        if hasattr(node, "_targets"):
            n = len(node._targets)
            if n > self.usage_limit:
                self.generator.writeln(" usage-n'>")
            elif n == 0 and hasattr(node, "_instantiates"):
                self.generator.writeln(" usage-1'>")
            else:
                self.generator.writeln(" usage-%s'>" % len(node._targets))
        else:
            self.generator.writeln(" usage-0'>")

    def _usage_specialisation(self, node):
        if hasattr(node, "_specialises"):
            self.generator.writeln(" usage-1'>")
        else:
            self.generator.writeln(" usage-0'>")

    def _types(self, node, name=None, class_="types"):
        self.generator.writeln("<div class='%s'>" % self._attr(class_))
        self.generator.indent()
        types = []
        for obj in lobj(node):
            qualified_name = lname(obj)
            if not qualified_name in types:
                types.append(qualified_name)
        for qualified_name in types:
            self._type(qualified_name, name)
        self._undesirables(node)
        self._raises(node)
        self._default(node)
        self.generator.dedent()
        self.generator.writeln("</div>")

    def _type(self, qualified_name, name=None):
        self.generator.writeln("<div class='type'>")
        self.generator.indent()
        if name is not None:
            self.generator.write("%s : " % self._text(name))
        self.generator.writeln(self._text(qualified_name))
        self.generator.dedent()
        self.generator.writeln("</div>")

    def _undesirables(self, node):
        if hasattr(node, "_undesirable"):
            for obj in node._undesirable:
                qualified_name = lname(obj)
                self._undesirable(qualified_name)

    def _raises(self, node):
        if hasattr(node, "_raises"):
            for obj in node._raises:
                qualified_name = lname(obj)
                self._raise(qualified_name)

    def _undesirable(self, qualified_name):
        self.generator.writeln("<div class='undesirable'>")
        self.generator.indent()
        self.generator.writeln(self._text(qualified_name))
        self.generator.dedent()
        self.generator.writeln("</div>")

    def _raise(self, qualified_name):
        self.generator.writeln("<div class='raise'>")
        self.generator.indent()
        self.generator.writeln(self._text(qualified_name))
        self.generator.dedent()
        self.generator.writeln("</div>")

    def _default(self, node):
        if hasattr(node, "_default"):
            qualified_name = lname(node._default)
            self.generator.writeln("<div class='default'>")
            self.generator.indent()
            self.generator.writeln(self._text(qualified_name))
            self.generator.dedent()
            self.generator.writeln("</div>")

    def _name_context(self, node):
        if hasattr(node, "_name_context"):
            self.generator.writeln("<div class='name-context'>")
            self.generator.indent()
            self.generator.write(self._text(node._name_context))
            self.generator.dedent()
            self.generator.writeln("</div>")

    def _targets(self, node, style_class="targets"):
        if len(node._targets) == 0:
            return
        self.generator.writeln("<div class='%s'>" % style_class)
        self.generator.indent()
        for target, argnames, locals in map(None, node._targets, node._argnames, node._locals):
            self._target(node, target, argnames, locals)
        self._undesirables(node)
        self._raises(node)
        self._default(node)
        self.generator.dedent()
        self.generator.writeln("</div>")

    def _target(self, node, target, argnames, locals):
        if target._module_name is None:
            self.generator.write("<a href='builtins.html#%s'>" % self._attr(target._qualified_name))
        elif target._module_name != self.module_name:
            self.generator.write("<a href='%s.html#%s'>" % (target._module_name, self._attr(target._qualified_name)))
        else:
            self.generator.writeln("<a href='#%s'>" % self._attr(target._qualified_name))
        self.generator.indent()
        self.generator.write(self._text(target._qualified_name))
        self.generator.write("(")
        # NOTE: Support keyword arguments.
        first = 1
        for argname in argnames:
            if not first:
                self.generator.write(", ")
            type_names = []
            for local in locals[argname]:
                type_names.append(local._qualified_name)
            self.generator.write("|".join(type_names))
            first = 0
        self.generator.writeln(")")
        self.generator.dedent()
        self.generator.writeln("</a>")

    # Visitor methods for statements.

    def visitModule(self, node):
        self.module_name = node._module_name

        self.generator.writeln("<html>")
        self.generator.indent()
        self.generator.writeln("<head>")
        self.generator.indent()
        self.generator.writeln("<title>Source Code</title>")
        self.generator.writeln("<style>")
        self.generator.indent()
        self.generator.writeln(
            "body {"
            "   padding-top: 4em; padding-bottom: 4em;"
            "   font-size: 14pt; font-family: monospace;"
            "   background-color: black; color: white;"
            "}")
        self.generator.writeln(".class { margin-bottom: 1em; }")
        self.generator.writeln(".function { margin-bottom: 1em; }")
        self.generator.writeln(".keyword { color: yellow; }")
        self.generator.writeln(".comment { color: blue; }")
        self.generator.writeln(".name-value { color: cyan; }")
        self.generator.writeln(".name-value a { color: cyan; text-decoration: none; }")
        self.generator.writeln(".body { padding-left: 4em; }")
        self.generator.writeln(".usage-0 { color: #555555; }")
        self.generator.writeln(".usage-1 { }")
        self.generator.writeln(".usage-2 { background-color: #440000; }")
        self.generator.writeln(".usage-3 { background-color: #880000; }")
        self.generator.writeln(".usage-4 { background-color: #CC0000; }")
        self.generator.writeln(".usage-n { background-color: #FF0000; }")
        self.generator.writeln(".undesirable { background-color: #FF0000; }")
        self.generator.writeln(".raise { background-color: #FF0000; }")
        self.generator.writeln(".default { background-color: #FF7700; }")
        # Add pop-up containers here:
        self.generator.writeln(
            ".raise-value,"
            ".print-node, .for-assign,"
            ".sequence-node, .in,"
            ".class-base, .and-expr, .or-expr,"
            ".assattr-attrname, .getattr-attrname, .slice-expr,"
            ".subscript-expr, .return-value, .callfunc-expr,"
            ".op, .assname, .name {"
            "   position: relative;"
            "}")
        # Add pop-up definitions here:
        self.generator.writeln(
            ".raise-types {"
            "   display: none; z-index: 1;"
            "   position: absolute; bottom: 2em; left: -5em;"
            "   padding: 0.5em; background-color: #770000;"
            "}")
        self.generator.writeln(
            ".return-types {"
            "   display: none; z-index: 1;"
            "   position: absolute; bottom: 2em; left: -5em;"
            "   padding: 0.5em; background-color: #770000;"
            "}")
        self.generator.writeln(
            ".types {"
            "   display: none; z-index: 2;"
            "   position: absolute; top: 3em; left: 0.5em;"
            "   padding: 0.5em; background-color: #0000FF;"
            "}")
        self.generator.writeln(
            ".qualified-name {"
            "   display: none; z-index: 2;"
            "   position: absolute; top: 1em; left: 7.5em;"
            "   padding: 0.5em; background-color: #00AAFF;"
            "}")
        self.generator.writeln(
            ".name-context {"
            "   display: none; z-index: 2;"
            "   position: absolute; top: 1em; left: 0.5em;"
            "   padding: 0.5em; background-color: #0077FF;"
            "}")
        self.generator.writeln(
            ".targets {"
            "   display: none; z-index: 2;"
            "   position: absolute; bottom: 1em; left: 0.5em;"
            "   padding: 0.5em; background-color: #007700;"
            "}")
        self.generator.writeln(
            ".logical-targets {"
            "   display: none; z-index: 2;"
            "   position: absolute; bottom: 6em; left: 0.5em;"
            "   padding: 0.5em; background-color: #007700;"
            "}")
        self.generator.writeln(".targets a, .logical-targets a { display: block; color: white; text-decoration: none; }")
        # Add pop-up rules here:
        self.generator.writeln(
            ".print-node:hover > .targets,"
            ".for-assign:hover > .targets,"
            ".sequence-node:hover > .targets,"
            ".in:hover > .targets,"
            ".class-base:hover > .types,"
            ".class-base:hover > .qualified-name,"
            ".and-expr:hover > .logical-targets,"
            ".or-expr:hover > .logical-targets,"
            ".assattr-attrname:hover > .name-context,"
            ".assattr-attrname:hover > .types,"
            ".getattr-attrname:hover > .name-context,"
            ".getattr-attrname:hover > .types,"
            ".slice-expr:hover > .targets,"
            ".subscript-expr:hover > .targets,"
            ".return-value:hover > .return-types,"
            ".callfunc-expr:hover > .targets,"
            ".op:hover > .targets,"
            ".assname:hover > .name-context,"
            ".assname:hover > .types,"
            ".assname:hover > .qualified-name,"
            ".name:hover > .name-context,"
            ".name:hover > .types,"
            ".name:hover > .qualified-name"
            "{"
            "   display: block;"
            "}")
        self.generator.dedent()
        self.generator.writeln("</style>")
        self.generator.dedent()
        self.generator.writeln("</head>")
        self.generator.writeln("<body>")
        self.default(node)
        self.generator.writeln("</body>")
        self.generator.dedent()
        self.generator.writeln("</html>")

    def visitImport(self, node):
        self.generator.writeln("<div class='import'>")
        self.generator.indent()
        self._keyword("import")
        first = 1
        for _name in node._names:
            if not first:
                self.generator.write(", ")
            self._name_ref(_name.module_name, _name._qualified_name, target_module_name=_name.module_name)
            if _name.as_name is not None:
                self.generator.write(" ")
                self._keyword("as")
                self.generator.write(" ")
                self._name(_name.as_name)
            first = 0
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitClass(self, node):
        self.generator.writeln("<div class='class'>")
        self.generator.indent()
        self._keyword("class")
        self._name_def(node.name, node._qualified_name)
        if node.bases:
            self.generator.writeln("(")
            first = 1
            for base in node.bases:
                if not first:
                    self.generator.write(", ")
                self.generator.writeln("<span class='class-base'>")
                self.generator.indent()
                self._name(base.name)
                self._qualified_name(base)
                self._types(base)
                self.generator.dedent()
                self.generator.writeln("</span>")
                first = 0
            self.generator.write(")")
        self.generator.writeln(":")
        self._doc(node.doc)

        self.generator.writeln("<div class='body'>")
        self.generator.indent()
        self.dispatch(node.code)
        self.generator.dedent()
        self.generator.writeln("</div>")
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitFunction(self, node):
        if not hasattr(node, "_specialises"):
            self.generator.writeln("<div class='comment'>")
            self.generator.indent()
            self.generator.writeln("# (Function %s)" % node.name)
            self.generator.writeln()
            self.generator.dedent()
            self.generator.writeln("</div>")
            return

        self.generator.write("<div class='function"); self._usage_specialisation(node)
        self.generator.indent()
        self._keyword("def")
        self._name_def(node.name, node._qualified_name)
        self.generator.writeln("(")
        # NOTE: Support keyword arguments.
        first = 1
        for argname in node.argnames:
            if not first:
                self.generator.write(", ")
            self.generator.writeln("<span class='name'>")
            self.generator.indent()
            self._name(argname)
            self.generator.writeln("<div class='types'>")
            self.generator.indent()
            for qualified_name in node._signature[argname]:
                self._type(qualified_name, argname)
            self.generator.dedent()
            self.generator.writeln("</div>")
            self.generator.dedent()
            self.generator.writeln("</span>")
            first = 0
        self.generator.write("):")
        self._doc(node.doc)

        self.generator.writeln("<div class='body'>")
        self.generator.indent()
        self.dispatch(node.code)
        self.generator.dedent()
        self.generator.writeln("</div>")
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitPrint(self, node):
        self.generator.writeln("<div class='print'>")
        self.generator.indent()
        self._keyword("print")
        if node.dest is not None:
            self.generator.write(">>")
            self.dispatch(node.dest)
        for call in node._calls:
            self.dispatch(call.expr)
            self.generator.writeln("<span class='print-node'>")
            self.generator.write(", ")
            self._targets(call)
            self.generator.writeln("</span>")
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitPrintnl(self, node):
        self.generator.writeln("<div class='println'>")
        self.generator.indent()
        self._keyword("print")
        if node.dest is not None:
            self.generator.write(">>")
            self.dispatch(node.dest)
        last = node._calls[-1]
        for call in node._calls:
            self.dispatch(call.expr)
            self.generator.writeln("<span class='print-node'>")
            if not call is last:
                self.generator.write(", ")
            else:
                self.generator.write("#")
            self._targets(call)
            self.generator.writeln("</span>")
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitDiscard(self, node):
        self.generator.writeln("<div class='discard'>")
        self.generator.indent()
        self.default(node)
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitIf(self, node):
        self.generator.writeln("<div class='if'>")
        self.generator.indent()
        first = 1
        short_circuited = 0
        for compare, body in node.tests:
            if short_circuited:
                break
            self.generator.writeln("<div class='test'>")
            self.generator.indent()
            if first:
                self._keyword("if")
            else:
                self._keyword("elif")
            self.dispatch(compare)
            self.generator.writeln(":")
            self.generator.dedent()
            self.generator.writeln("</div>")
            self.generator.writeln("<div class='body'>")
            self.generator.indent()
            if hasattr(compare, "_ignored"):
                self._keyword("pass")
                self.generator.write("<span class='comment'># Ignored</span>")
            else:
                self.dispatch(body)
            self.generator.dedent()
            self.generator.writeln("</div>")
            first = 0
            if hasattr(compare, "_short_circuited"):
                short_circuited = 1

        if node.else_ is not None and not short_circuited:
            self.generator.writeln("<div class='test'>")
            self.generator.indent()
            self._keyword("else")
            self.generator.writeln(":")
            self.generator.dedent()
            self.generator.writeln("</div>")
            self.generator.writeln("<div class='body'>")
            self.generator.indent()
            self.dispatch(node.else_)
            self.generator.dedent()
            self.generator.writeln("</div>")
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitFor(self, node):
        self.generator.writeln("<div class='for'>")
        self.generator.indent()
        self._keyword("for")
        self.generator.writeln("<span class='for-assign'>")
        self.generator.indent()
        self.dispatch(node.assign)
        self._targets(node.assign)
        self.generator.dedent()
        self.generator.writeln("</span>")
        self.generator.writeln("<span class='in'>")
        self._keyword("in")
        self._targets(node)
        self.generator.writeln("</span>")
        self.generator.writeln("<span class='for-list'>")
        self.generator.indent()
        self.dispatch(node.list)
        self.generator.dedent()
        self.generator.writeln("</span>")
        self.generator.writeln(":")
        self.generator.writeln("<div class='body'>")
        self.generator.indent()
        self.dispatch(node.body)
        self.generator.dedent()
        self.generator.writeln("</div>")
        if node.else_:
            self.generator.writeln("<div class='test'>")
            self.generator.indent()
            self._keyword("else")
            self.generator.writeln(":")
            self.generator.dedent()
            self.generator.writeln("</div>")
            self.generator.writeln("<div class='body'>")
            self.generator.indent()
            self.dispatch(node.else_)
            self.generator.dedent()
            self.generator.writeln("</div>")
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitWhile(self, node):
        self.generator.writeln("<div class='while'>")
        self.generator.indent()
        self.generator.writeln("<div class='test'>")
        self.generator.indent()
        self._keyword("while")
        self.dispatch(node.test)
        self.generator.writeln(":")
        self.generator.dedent()
        self.generator.writeln("</div>")
        self.generator.writeln("<div class='body'>")
        self.generator.indent()
        self.dispatch(node.body)
        self.generator.dedent()
        self.generator.writeln("</div>")
        if node.else_:
            self.generator.writeln("<div class='test'>")
            self.generator.indent()
            self._keyword("else")
            self.generator.writeln(":")
            self.generator.dedent()
            self.generator.writeln("</div>")
            self.generator.writeln("<div class='body'>")
            self.generator.indent()
            self.dispatch(node.else_)
            self.generator.dedent()
            self.generator.writeln("</div>")
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitReturn(self, node):
        self.generator.writeln("<div class='return'>")
        self.generator.indent()
        self.generator.writeln("<span class='return-value'>")
        self.generator.indent()
        self._keyword("return")
        self.generator.write(" ")
        self.dispatch(node.value)
        self._types(node.value, class_="return-types")
        self.generator.dedent()
        self.generator.writeln("</span>")
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitRaise(self, node):
        self.generator.writeln("<div class='raise-statement'>")
        self.generator.indent()
        self.generator.writeln("<span class='raise-value'>")
        self.generator.indent()
        self._keyword("raise")
        self.generator.write(" ")
        # NOTE: To be expanded.
        self.dispatch(node.expr1)
        #self._types(node.expr1, class_="raise-types")
        self.generator.dedent()
        self.generator.writeln("</span>")
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitGlobal(self, node):
        self.generator.writeln("<div class='global'>")
        self.generator.indent()
        self._keyword("global")
        self.generator.write(" ")
        first = 1
        for name in node.names:
            if not first:
                self.generator.write(", ")
            self.generator.write(name)
            first = 0
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitAssign(self, node):
        self.generator.writeln("<div class='assign'>")
        self.generator.indent()
        first = 1
        for n in node.nodes:
            if not first:
                self.generator.write(", ")
            self.dispatch(n)
            first = 0
        self.generator.write(" = ")
        self.dispatch(node.expr)

        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitAugAssign(self, node):
        self.generator.writeln("<div class='assign'>")
        self.generator.indent()
        self.generator.writeln("<span class='aug-assign'>")
        self.generator.indent()
        self.dispatch(node.node)
        self._op(self._text(node.op), node._op)
        self.dispatch(node.expr)
        self.generator.dedent()
        self.generator.writeln("</span>")
        self.generator.dedent()
        self.generator.writeln("</div>")

    def visitPass(self, node):
        self.generator.write("<div class='pass'>")
        self._keyword("pass")
        self.generator.writeln("</div>")

    # Visitor methods for expression nodes.

    def visitName(self, node):
        self.generator.writeln("<span class='name'>")
        self.generator.indent()
        self._name(node.name)
        self._name_context(node)
        self._qualified_name(node)
        self._types(node, node.name)
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitConst(self, node):
        self.generator.writeln("<span class='const'>")
        self.generator.indent()
        self.generator.writeln(self._text(repr(node.value)))
        self.generator.dedent()
        self.generator.writeln("</span>")

    def _visitTuple(self, node):
        for n in node._calls:
            self.dispatch(n.expr)
            self.generator.writeln("<span class='sequence-node'>")
            self.generator.write(", ")
            self._targets(n)
            self.generator.writeln("</span>")

    def visitTuple(self, node):
        self.generator.writeln("<span class='tuple'>")
        self.generator.indent()
        self.generator.write("(")
        self._visitTuple(node)
        self.generator.writeln(")")
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitList(self, node):
        self.generator.writeln("<span class='list'>")
        self.generator.indent()
        self.generator.write("[")
        self._visitTuple(node)
        self.generator.writeln("]")
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitAssName(self, node):
        self.generator.writeln("<span class='assname'>")
        self.generator.indent()
        self._name(node.name)
        self._name_context(node)
        self._qualified_name(node)
        self._types(node, node.name)
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitAssAttr(self, node):
        self.generator.writeln("<span class='assattr'>")
        self.generator.indent()
        self.dispatch(node.expr)
        self.generator.writeln("<span class='assattr-attrname'>")
        self.generator.indent()
        self.generator.write(".")
        self._name(node.attrname)
        self._name_context(node)
        self._types(node)
        self.generator.dedent()
        self.generator.writeln("</span>")
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitGetattr(self, node):
        self.generator.writeln("<span class='getattr'>")
        self.generator.indent()
        self.dispatch(node.expr)
        self.generator.writeln("<span class='getattr-attrname'>")
        self.generator.indent()
        self.generator.write(".")
        self._name(node.attrname)
        self._name_context(node)
        self._types(node)
        self.generator.dedent()
        self.generator.writeln("</span>")
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitAssTuple(self, node):
        self.generator.write("(")
        first = 1
        for n in node.nodes:
            if not first:
                self.generator.write(", ")
            self.dispatch(n)
            first = 0
        if len(node.nodes) == 1:
            self.generator.write(", ")
        self.generator.write(")")

    def visitAssList(self, node):
        self.generator.write("[")
        self.visitAssTuple(node)
        self.generator.write("]")

    def visitCallFunc(self, node):
        self.generator.write("<span class='callfunc"); self._usage_targets(node)
        self.generator.indent()
        self.generator.writeln("<span class='callfunc-expr'>")
        self.generator.indent()
        self.dispatch(node.node)
        self._targets(node)
        self.generator.dedent()
        self.generator.writeln("</span>")
        self.generator.writeln("(")
        # NOTE: Support keyword arguments.
        first = 1
        for arg in node.args:
            if not first:
                self.generator.write(", ")
            self.dispatch(arg)
            first = 0
        if node.star_args is not None:
            if not first:
                self.generator.write(", ")
            self.generator.write("*")
            self.dispatch(node.star_args)
            first = 0
        if node.dstar_args is not None:
            if not first:
                self.generator.write(", ")
            self.generator.write("**")
            self.dispatch(node.dstar_args)
            first = 0
        self.generator.writeln(")")
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitSubscript(self, node):
        self.generator.write("<span class='subscript"); self._usage_targets(node)
        self.generator.indent()
        self.generator.writeln("<span class='subscript-expr'>")
        self.generator.indent()
        self.dispatch(node.expr)
        self._targets(node)
        self.generator.writeln("[")
        first = 1
        for sub in node.subs:
            if not first:
                self.generator.write(", ")
            self.dispatch(sub)
            first = 0
        self.generator.writeln("]")
        self.generator.dedent()
        self.generator.writeln("</span>")
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitSlice(self, node):
        self.generator.write("<span class='slice"); self._usage_targets(node)
        self.generator.indent()
        self.generator.writeln("<span class='slice-expr'>")
        self.generator.indent()
        self.dispatch(node.expr)
        self._targets(node)
        self.generator.writeln("[")
        if node.lower is not None:
            self.dispatch(node.lower)
        self.generator.write(":")
        if node.upper is not None:
            self.dispatch(node.upper)
        self.generator.writeln("]")
        self.generator.dedent()
        self.generator.writeln("</span>")
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitCompare(self, node):
        self.generator.writeln("<span class='compare'>")
        self.generator.indent()
        self.dispatch(node.expr)
        for op in node._ops:
            self._op(op.op, op)
            self.dispatch(op.right)
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitAnd(self, node):
        self.generator.writeln("<span class='and'>")
        self.generator.indent()
        self.generator.write("(")
        first = 1
        for n in node._nodes:
            if not first:
                self.generator.write(" and ")
            self.generator.writeln("<span class='and-expr'>")
            self.generator.indent()
            self.dispatch(n.expr)
            self._targets(n, "logical-targets")
            self.generator.dedent()
            self.generator.writeln("</span>")
            first = 0
        self.generator.write(")")
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitOr(self, node):
        self.generator.writeln("<span class='or'>")
        self.generator.indent()
        first = 1
        for n in node._nodes:
            if not first:
                self.generator.write(" or ")
            self.generator.writeln("<span class='or-expr'>")
            self.generator.indent()
            self.dispatch(n.expr)
            self._targets(n, "logical-targets")
            self.generator.dedent()
            self.generator.writeln("</span>")
            first = 0
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitNot(self, node):
        self.generator.writeln("<span class='not'>")
        self.generator.indent()
        self.generator.write("not ")
        self.dispatch(node.expr)
        self.generator.dedent()
        self.generator.writeln("</span>")

    def _visitArithmeticOp(self, node, name, symbol):
        self.generator.writeln("<span class='%s'>" % name)
        self.generator.indent()
        self.dispatch(node.left)
        self._op(self._text(symbol), node)
        self.dispatch(node.right)
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitAdd(self, node):
        self._visitArithmeticOp(node, "add", "+")

    def visitSub(self, node):
        self._visitArithmeticOp(node, "sub", "-")

    def visitMul(self, node):
        self._visitArithmeticOp(node, "mul", "*")

    def visitDiv(self, node):
        self._visitArithmeticOp(node, "div", "/")

    def visitLeftShift(self, node):
        self._visitArithmeticOp(node, "leftshift", "<<")

    def visitRightShift(self, node):
        self._visitArithmeticOp(node, "rightshift", ">>")

    def visitMod(self, node):
        self._visitArithmeticOp(node, "mod", "%")

    def visitPower(self, node):
        self._visitArithmeticOp(node, "power", "**")

    def _visitUnaryOp(self, node, name, symbol):
        self.generator.writeln("<span class='%s'>" % name)
        self.generator.indent()
        self._op(self._text(symbol), node)
        self.dispatch(node.expr)
        self.generator.dedent()
        self.generator.writeln("</span>")

    def visitUnaryAdd(self, node):
        self._visitUnaryOp(node, "unaryadd", "+")

    def visitUnarySub(self, node):
        self._visitUnaryOp(node, "unarysub", "-")

# vim: tabstop=4 expandtab shiftwidth=4
