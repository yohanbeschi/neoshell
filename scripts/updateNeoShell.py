#!/usr/bin/python
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import __builtin__, NeoShell, ensureFile, sudo, cd
__builtin__.neoShell = NeoShell()

sudo('cp ../libs/neoshell/src/neoshell.py /usr/local/bin')
ensureFile('/usr/local/bin/neoshell.py', 'root', 'root', 755)

cd('../libs/kissutils')
sudo('python27 setup.py install')