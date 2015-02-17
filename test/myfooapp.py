#!/usr/local/bin/neoshell.py
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, workspace, buildPaths
from neoshell import cd, cp, cmd, createPackage, ensureDir, getPyFile, useForPack, unpack, sudo

#getScriptDir()

def execute():
  appName('MyFooApp')
  version('2.0')
  workspace('foobar')
  buildPaths()
  
  ensureDir(neoShell.appWorkspaceTmp)
  cd(neoShell.appWorkspaceTmp)
  cmd('touch foo.txt')
  useForPack('%sfoo.txt' % neoShell.appWorkspaceTmp, '/test/')
  
  createPackage()
  
def install():
  print 'MyFooApp Installed'