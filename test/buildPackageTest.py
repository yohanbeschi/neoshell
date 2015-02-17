#!/usr/local/bin/neoshell.py
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, buildPaths, buildPackage, createPackage, getScriptDir, cp, installPackage

def execute():
  appName('GlobalPackage')
  version('1.0')
  buildPaths()

  buildPackage('%smyfooapp.py' % getScriptDir(), moveTo=neoShell.appWorkspaceFiles, executeArgs=['10', '100']) # MyFooApp-2.0.tar.gz
  createPackage()
  cp('%s%s' % (neoShell.appWorkspace, neoShell.compressedFile), neoShell.home)
  
def install():
  installPackage('%sMyFooApp-2.0.tar.gz' % neoShell.appWorkspaceFiles, installArgs=['0', '1', '2'])
  