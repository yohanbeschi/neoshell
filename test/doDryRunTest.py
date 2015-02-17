import imp
imp.load_source('neoshell', '../src/neoshell.py')
from neoshell import cd, cp, cmd, createPackage, ensureDir, getPyFile, useForPack, decorate

def execute():
  decorate(True)
  neoShell.buildPaths()
  ensureDir(neoShell.appWorkspaceTmp)
  cd(neoShell.appWorkspaceTmp)
  cmd('touch foo.txt')
  useForPack('%sfoo.txt' % neoShell.appWorkspaceTmp, '')
  
  createPackage()
  cp('%s%s' % (neoShell.appWorkspace, neoShell.compressedFile), neoShell.home)
  
def install():
  cmd('echo hello')