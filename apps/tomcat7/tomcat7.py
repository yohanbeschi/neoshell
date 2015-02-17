#!/usr/local/bin/neoshell.py
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, buildPaths, getScriptDir
from neoshell import cd, cmd, createPackage, ensureDir, useForPack, unpack, ensureFile, lns, chown, cp, ensureGroup, ensureUser, sudo, chmod

def execute():
  appName('tomcat')
  version('7.0')
  buildPaths()
  
  ensureDir(neoShell.appWorkspaceTmp)
  cd(neoShell.appWorkspaceTmp)
  cmd('wget http://wwwftp.ciril.fr/pub/apache/tomcat/tomcat-7/v7.0.55/bin/apache-tomcat-7.0.55.tar.gz')
  #cp('%sapache-tomcat-7.0.55.tar.gz' % neoShell.home, neoShell.appWorkspaceTmp)
  #cd(neoShell.appWorkspaceTmp)
  cmd('tar -xvzf apache-tomcat-7.0.55.tar.gz')
  cd('apache-tomcat-7.0.55')
  useForPack('bin/', 'opt/tomcat7')
  useForPack('conf/*', 'etc/tomcat7')
  useForPack('lib/*', 'usr/share/java/tomcat7')
  useForPack('%stomcat7.sysconfig' % getScriptDir(), 'etc/sysconfig', filename='tomcat7')
  useForPack('%stomcat7.logrotate' % getScriptDir(), 'etc/logrotate.d', filename='tomcat7')
  useForPack('%stomcat7.init' % getScriptDir(), 'etc/init.d', filename='tomcat7')

  createPackage()
  
def install():
  unpack()
  
  ensureGroup('tomcat')
  ensureUser('tomcat', group='tomcat', fullname='Tomcat Service Account', home='/opt/tomcat7')
  
  ensureDir('/opt/tomcat7', 'root', 'root', recursive=True)
  ensureDir('/usr/share/java/tomcat7', 'root', 'root', recursive=True)

  ensureDir('/etc/tomcat7', 'root', 'root', 664, recursive=True)
  ensureDir('/etc/tomcat7', 'root', 'tomcat', 775)
  ensureDir('/etc/tomcat7/Catalina', 'tomcat', 'tomcat', 774, recursive=True)
  ensureDir('/etc/tomcat7/Catalina', 'tomcat', 'tomcat', 775)
  ensureFile('/etc/tomcat7/tomcat-users.xml', 'root', 'tomcat')
  
  ensureDir('/etc/sysconfig', 'root', 'root')
  ensureFile('/etc/sysconfig/tomcat7', 'root', 'root')
  
  ensureDir('/etc/logrotate.d', 'root', 'root')
  ensureFile('/etc/logrotate.d/tomcat7', 'root', 'root', 644)
  
  ensureDir('/etc/init.d/', 'root', 'root')
  ensureFile('/etc/init.d/tomcat7', 'root', 'root', 755)

  ensureDir('/var/log/tomcat7/', 'tomcat', 'tomcat')
  ensureDir('/var/lib/tomcat7/webapps/', 'root', 'tomcat', 775)
  ensureDir('/var/cache/tomcat7/temp/', 'root', 'tomcat', 775)
  ensureDir('/var/cache/tomcat7/work/', 'root', 'tomcat', 775)
  
  lns('/etc/tomcat7', '/opt/tomcat7/conf')
  lns('/usr/share/java/tomcat7', '/opt/tomcat7/lib')
  lns('/var/log/tomcat7', '/opt/tomcat7/logs')
  lns('/var/cache/tomcat7/temp', '/opt/tomcat7/temp')
  lns('/var/lib/tomcat7/webapps', '/opt/tomcat7/webapps')
  lns('/var/cache/tomcat7/work', '/opt/tomcat7/work')
  
  sudo('chkconfig --add tomcat7')
  sudo('chkconfig tomcat7 on')