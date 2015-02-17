import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import cd, cp, cmd, createPackage, ensureDir, getPyFile, useForPack, unpack, sudo

def execute():
  neoShell.buildPaths()
  ensureDir(neoShell.appWorkspaceTmp)
  cd(neoShell.appWorkspaceTmp)
  cmd('touch foo.txt')
  useForPack('%sfoo.txt' % neoShell.appWorkspaceTmp, '/test/')
  
  createPackage()
  
def install():
  unpack()
  sudo('ls -l /test/foo.txt')
  sudo('rm -rf /test/')