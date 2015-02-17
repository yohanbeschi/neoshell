#!/usr/local/bin/neoshell.py
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, buildPaths, getScriptDir
from neoshell import cd, cmd, createPackage, ensureDir, useForPack, unpack, ensureFile, lns, chown, cp

def execute():
  appName('apache.ant')
  version('1.9.4')
  buildPaths()
  
  ensureDir(neoShell.appWorkspaceTmp)
  cd(neoShell.appWorkspaceTmp)
  cmd('wget http://apache.tradebit.com/pub//ant/binaries/apache-ant-1.9.4-bin.tar.gz')
  #cp('%sapache-ant-1.9.4-bin.tar.gz' % neoShell.home, neoShell.appWorkspaceTmp)
  #cd(neoShell.appWorkspaceTmp)
  cmd('tar -xvzf apache-ant-1.9.4-bin.tar.gz')
  useForPack('apache-ant-1.9.4/*', '/opt/ant')
  useForPack('%sapache-ant.sh' % getScriptDir(), '/etc/profile.d/')
  
  createPackage()
  
def install():
  unpack()
  chown('/opt/ant', 'root', 'root', args='-R')
  ensureDir('/etc', 'root', 'root', 755)
  ensureDir('/etc/profile.d', 'root', 'root', 755)
  ensureFile('/etc/profile.d/apache-ant.sh', 'root', 'root', 755)
  lns('/opt/ant/bin/ant', '/usr/bin/ant')