#!/usr/bin/env python

import antlr3
from OpenAirLexer import OpenAirLexer
from OpenAirParser import OpenAirParser
import sys

fin = file(sys.argv[1])

s = ""
for i in fin.xreadlines():
    s += i

char_stream = antlr3.ANTLRStringStream(s)
# or to parse a file:
# char_stream = antlr3.ANTLRFileStream(path_to_input)
# or to parse an opened file or any other file-like object:
# char_stream = antlr3.ANTLRInputStream(file)

lexer = OpenAirLexer(char_stream)
tokens = antlr3.CommonTokenStream(lexer)
parser = OpenAirParser(tokens)
parser.file()
