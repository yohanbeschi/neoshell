#!/usr/local/bin/neoshell.py
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, buildPaths, getScriptDir, sudo, ensureFile, cd, cp
from neoshell import cmd, createPackage, ensureDir, getPyFile, useForPack, unpack, serviceStart, ensureServiceStarted

def execute():
  appName('sonarqube')
  version('4.4')
  buildPaths()

  useForPack('%ssonar.properties' % getScriptDir(), '/opt/sonar/conf/')
  
  createPackage()
  
def install():
  sudo('wget http://downloads.sourceforge.net/project/sonar-pkg/rpm/noarch/sonar-4.4-1.noarch.rpm -O /var/www/html/centos-6/6.5/contrib/x86_64/sonar-4.4-1.noarch.rpm')
  
  ensureServiceStarted('httpd')
  sudo('createrepo --update /var/www/html/centos-6/6.5/contrib/x86_64/')
  sudo('yum update -y')
  sudo('yum -v clean expire-cache')
  sudo('yum install -y sonar >> yum_install.log')
  
  unpack()
  
  ensureDir('/opt', 'root', 'root', 755)
  ensureDir('/opt/sonar', 'root', 'root', 755)
  ensureDir('/opt/sonar/conf', 'root', 'root', 755)
  ensureDir('/opt/sonar/conf/sonar.properties', 'sonar', 'sonar', 644)
  
  serviceStart('sonar')