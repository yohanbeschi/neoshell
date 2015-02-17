#!/usr/local/bin/neoshell.py
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, buildPaths, getScriptDir, useFile, cd, ensureFile, addSudoer, sudo, createPackage
from neoshell import cmd, rcmd, ensureDir, getPyFile, useForPack, unpack, ensureServiceStopped, ensureServiceStarted, cp, serviceStart

def execute():
  appName('thoughtworks.go')
  version('14.2.0')
  buildPaths()
  
  ensureDir(neoShell.appWorkspaceTmp)
  cd(neoShell.appWorkspaceTmp)

  useForPack('%sgo-server' % getScriptDir(), '/etc/default/')
  useForPack('%sgo-agent' % getScriptDir(), '/etc/default/')
  useFile('%sgo-sudoer' % getScriptDir())
  
  createPackage()
  
def install():
  sudo('wget http://download.go.cd/gocd-rpm/go-server-14.2.0-377.noarch.rpm -O /var/www/html/centos-6/6.5/contrib/x86_64/go-server-14.2.0-377.noarch.rpm')
  sudo('wget http://download.go.cd/gocd-rpm/go-agent-14.2.0-377.noarch.rpm -O /var/www/html/centos-6/6.5/contrib/x86_64/go-agent-14.2.0-377.noarch.rpm')
  
  ensureServiceStarted('httpd')
  sudo('createrepo --update /var/www/html/centos-6/6.5/contrib/x86_64/')
  sudo('yum update -y')
  sudo('yum -v clean expire-cache')
  
  sudo('yum install -y go-server --nogpgcheck >> yum_install.log')
  sudo('yum install -y go-agent --nogpgcheck >> yum_install.log')

  unpack()
  ensureDir('/etc', 'root', 'root', 755)
  ensureDir('/etc/default', 'root', 'root', 755)
  ensureFile('/etc/default/go-server', 'go', 'go', 644)
  ensureFile('/etc/default/go-agent', 'go', 'go', 644)
  ensureDir('/var', 'root', 'root', 755)
  ensureDir('/var/go', 'go', 'go', 755)
  
  addSudoer('%sgo-sudoer' % neoShell.appWorkspaceFiles)
  
  serviceStart('go-server')
  serviceStart('go-agent')