#!/usr/bin/env python

"""
Utilities for handling arguments, calls, parameters and functions.

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
import analysis.node

class Parameters:

    "A class providing convenience methods giving information about parameters."

    def __init__(self, function):

        "Initialise the object with a 'function' node."

        self.function = function

        if function.flags & 4 != 0:
            self.has_star = 1
        else:
            self.has_star = 0

        if function.flags & 8 != 0:
            self.has_dstar = 1
        else:
            self.has_dstar = 0

        self.number_of_defaults = len(self.function.defaults)
        self.number_of_normal_parameters = len(self.function.argnames) - self.has_star - self.has_dstar

    def get_defaults(self):

        """
        Return a list of default values for each of the normal positional
        parameters.
        """

        return [None] * (self.number_of_normal_parameters - self.number_of_defaults) + list(self.function.defaults)

    def get_parameter_mapping(self):

        """
        Return a mapping of positional parameter names to default values, where
        None is specified for those parameters without default values.
        """

        return map(None, self.function.argnames[:self.number_of_normal_parameters], self.get_defaults())

    def get_star_parameter(self):

        """
        Return the name of the variable arguments parameter, or None if no such
        parameter is defined.
        """

        if self.has_star:
            return self.function.argnames[-1 - self.has_dstar]
        else:
            return None

    def get_dstar_parameter(self):

        """
        Return the name of the keyword arguments parameter, or None if no such
        parameter is defined.
        """

        if self.has_dstar:
            return self.function.argnames[-1]
        else:
            return None

def unify_arguments(args, star_args, dstar_args, function):

    """
    Unify the given 'args', 'star_args' and 'dstar_args' with the parameters
    from the given 'function' node. Return a tuple consisting of a namespace
    dictionary (containing a mapping from parameter names to argument
    expressions), a defaults list (containing nodes providing default values), a
    star values list (containing nodes providing star argument values), a dstar
    values list (containing nodes providing dstar/keyword argument values).

    NOTE: *args and **args are not properly supported yet.
    """

    argument_dict = {}
    argument_list = []
    using_keywords = 0

    # Preprocess the arguments to identify keyword arguments.

    for argument in args:
        if isinstance(argument, compiler.ast.Keyword):
            argument_dict[argument.name] = argument
        elif not using_keywords:
            argument_list.append(argument)
        else:
            raise TypeError, "Argument found after keyword arguments."

    # Traverse the parameters, either finding positional arguments or keyword arguments
    # for each one.

    argument_list_index = 0
    parameters = Parameters(function)
    namespace = {}
    defaults = []

    # Process all but * and ** parameters.

    for parameter, default in parameters.get_parameter_mapping():

        # Where keyword arguments exist, switch to keyword mode.

        if argument_dict.has_key(parameter):
            namespace[parameter] = [argument_dict[parameter]]
            using_keywords = 1
            del argument_dict[parameter]

        # Otherwise, if keyword mode is not active, attempt to find a positional argument.

        elif not using_keywords and argument_list_index < len(argument_list):
            namespace[parameter] = [argument_list[argument_list_index]]
            argument_list_index += 1

        # Where no such arguments remain, attempt to find default values.

        elif default is not None:
            namespace[parameter] = [default]
            defaults.append(default)

        # If no suitable keyword argument exists, yet keyword mode is active, raise an
        # exception.

        else:
            raise TypeError, "Parameter %s in %s is missing: %s vs. %s" % (
                parameter, function._qualified_name, args, function.argnames)

    # If *parameter is present, soak up excess arguments.

    star = parameters.get_star_parameter()
    if star is not None:
        namespace[star] = []

        # Keyword arguments end the argument list, apart from *argument and
        # **argument.

        if not using_keywords:
            star_arg_values = []
            while argument_list_index < len(argument_list):
                argument = argument_list[argument_list_index]
                if isinstance(argument, compiler.ast.Keyword):
                    break
                star_arg_values.append(argument)
                argument_list_index += 1

            if star_arg_values:
                namespace[star].append(compiler.ast.List(star_arg_values))

        # If *argument is present, connect it to *parameter.

        if star_args:
            namespace[star].append(star_args)

    # If **parameter is present, soak up excess keyword arguments.

    dstar = parameters.get_dstar_parameter()
    if dstar is not None:
        namespace[dstar] = []
        for value in argument_dict.values():
            namespace[dstar].append(value)

        # If **argument is present, connect it to **parameter.

        if dstar_args:
            namespace[dstar].append(dstar_args)

    return namespace, defaults, namespace.get(star, []), namespace.get(dstar, [])

# vim: tabstop=4 expandtab shiftwidth=4
