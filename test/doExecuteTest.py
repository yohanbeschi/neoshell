import imp
imp.load_source('neoshell', '../src/neoshell.py')
from neoshell import cd, cmd, ensureDir, useFile

def execute():
  neoShell.buildPaths()
  ensureDir(neoShell.appWorkspaceTmp)
  cd(neoShell.appWorkspaceTmp)
  cmd('touch foo.txt')
  useFile('%sfoo.txt' % neoShell.appWorkspaceTmp)