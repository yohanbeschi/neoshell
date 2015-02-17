#!/usr/local/bin/neoshell.py
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, buildPaths, sudo, ensureServiceStarted
from neoshell import cmd, createPackage, ensureDir, getPyFile, useForPack, unpack, ensureServiceStopped, installPackage, ensureFile

def execute():
  appName('sonatype.nexus')
  version('2.8.1')
  buildPaths()

  useFile('%ssecurity.xml' % getScriptDir())
  
  createPackage()
  
def install():
  _, _, ret =  sudo('yum install tomcat7', acceptedReturncodes=range(0, 255))
  if ret == 0:
    ensureServiceStopped('tomcat7')  
    
    sudo('rm -rf /usr/share/tomcat7/sonatype-work/*')
    ensureDir('/usr/share/tomcat7/sonatype-work/nexus/conf', 'tomcat', 'tomcat', 755)
    cp('%ssecurity.xml' % neoShell.appWorkspaceFiles, '/usr/share/tomcat7/sonatype-work/nexus/conf')
    ensureFile('/usr/share/tomcat7/sonatype-work/nexus/conf/security.xml', 'tomcat', 'tomcat', 644)
    
    sudo('chkconfig --add tomcat7')
    sudo('chkconfig tomcat7 on')
  else:
    if len(neoShell.installArgs) > 0:
      dir = neoShell.installArgs[0]
    else:
      dir = neoShell.appWorkspaceFiles

    installPackage('%stomcat-7.0.tar.gz' % dir)
    sudo('rm -rf /opt/tomcat7/sonatype-work/*')
    ensureDir('/opt/tomcat7/sonatype-work/nexus/conf', 'tomcat', 'tomcat', 755)
    cp('%ssecurity.xml' % neoShell.appWorkspaceFiles, '/opt/tomcat7/sonatype-work/nexus/conf')
    ensureFile('/opt/tomcat7/sonatype-work/nexus/conf/security.xml', 'tomcat', 'tomcat', 644)
  
  sudo('wget -O /var/lib/tomcat7/webapps/nexus.war http://www.sonatype.org/downloads/nexus-2.8.1.war')
  ensureFile('/var/lib/tomcat7/webapps/nexus.war', 'tomcat', 'tomcat')
  ensureServiceStarted('tomcat7')
  