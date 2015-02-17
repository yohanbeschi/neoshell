#!/usr/bin/python
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import __builtin__, NeoShell, echo
__builtin__.neoShell = NeoShell()

#--------------------- Your code ---------------------
echo('Hello World')