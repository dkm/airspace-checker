#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   airspace checker
#   Copyright (C) 2010  Marc Poulhiès
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


import antlr3
import sys

from OpenAirLexer import OpenAirLexer
from OpenAirParser import OpenAirParser

finput = open(sys.argv[1])
input = finput.read().decode('latin-1')
char_stream = antlr3.ANTLRStringStream(input)
# or to parse a file:
# char_stream = antlr3.ANTLRFileStream(path_to_input)
# or to parse an opened file or any other file-like object:
# char_stream = antlr3.ANTLRInputStream(file)

lexer = OpenAirLexer(char_stream)
tokens = antlr3.CommonTokenStream(lexer)
parser = OpenAirParser(tokens)
parser.oair_file()
