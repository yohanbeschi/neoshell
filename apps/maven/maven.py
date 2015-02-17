#!/usr/local/bin/neoshell.py
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, buildPaths, getScriptDir, ensureParams
from neoshell import cd, cmd, createPackage, ensureDir, useForPack, unpack, ensureFile, lns, chown, cp, rm

def execute():
  ensureParams(neoShell.executeArgs, 1, 'Password missing to decrypt settings.xml')
  appName('apache.maven')
  version('3.2.2')
  buildPaths()
  
  ensureDir(neoShell.appWorkspaceTmp)
  cd(neoShell.appWorkspaceTmp)
  cmd('wget http://apache.websitebeheerjd.nl/maven/maven-3/3.2.2/binaries/apache-maven-3.2.2-bin.tar.gz')
  #cp('%sapache-maven-3.2.2-bin.tar.gz' % neoShell.home, neoShell.appWorkspaceTmp)
  #cd(neoShell.appWorkspaceTmp)
  cmd('tar -xvzf apache-maven-3.2.2-bin.tar.gz')
  useForPack('apache-maven-3.2.2/*', '/opt/maven')
  useForPack('%sapache-maven.sh' % getScriptDir(), '/etc/profile.d/')
  
  cd(getScriptDir())
  cmd('mvn_key=%s;export mvn_key;openssl enc -d -aes-256-cbc -a -in settings.enc -pass env:mvn_key > settings.xml;unset mvn_key' % neoShell.executeArgs[0], hide=True)
  useForPack('settings.xml', '/opt/maven/conf')
  rm('settings.xml')
  
  createPackage()
  
def install():
  unpack()
  chown('/opt/maven', 'root', 'root', args='-R')
  ensureDir('/etc', 'root', 'root', 755)
  ensureDir('/etc/profile.d', 'root', 'root', 755)
  ensureFile('/etc/profile.d/apache-maven.sh', 'root', 'root', 755)
  ensureFile('/opt/maven/conf/settings.xml', 'root', 'root', 755)
  lns('/opt/maven/bin/mvn', '/usr/bin/mvn', 664)