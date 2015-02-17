#!/usr/local/bin/neoshell.py
# -*- coding: utf-8 -*-
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, buildPaths, getScriptDir, addSlash, workspace, cleanAll, executeScript, env
from neoshell import cd, cmd, rcmd, createPackage, ensureDir, useForPack, unpack, ensureFile, lns, chown, cp
from neoshell import ensureGroup, ensureUser, sudo, chmod, callback, ensureServiceStopped

def execute():
  kissutils = __import__('kissutils')
  
  cd(getScriptDir())
  cd('..') # devops/scripts => devops
  rootDir = addSlash(neoShell.currentDir)
  targetDir = '%starget/' % rootDir
  cmd('rm -rf %s*' % targetDir)
  ensureDir(targetDir)
  workspace(targetDir)

  # ---- In devops - Get the current build version
  buildVersion = callback(kissutils.callbackGetFileContent('%sBUILDVERSION' % addSlash(neoShell.currentDir)))
  
  appName('bus.httpd')
  version(buildVersion)
  env('common')
  buildPaths()
  ensureDir(neoShell.appWorkspaceTmp)
  cd(neoShell.appWorkspaceTmp)  
  
  # Positionnement des fichiers statiques dans les bons répertoires
  # prêts à être déployés sur le serveur dans /
  staticDir = '%s/middleware/static' % rootDir # Pas sur du chemin
  useForPack(staticDir + '/apache/conf.d', 'etc/httpd')
  useForPack(staticDir + '/apache/vhosts.d', 'etc/httpd')
  useForPack(staticDir + '/apache/www', 'var')
  
  createPackage()
 
  # Publish the binary
  cd(neoShell.workspace)
  cd('../../forge/scripts') # devops/target => KISS-Forge/scripts
  forgeScriptsDir = addSlash(neoShell.currentDir)
  packagePath = '%s%s' % (neoShell.appWorkspace, neoShell.compressedFile)
  executeScript('%spublishBinary.py' % forgeScriptsDir, executeArgs=[packagePath])
 
  cleanAll()
  
def install():
  sudo('yum update -y')
  sudo('ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime');
  sudo('yum install -y httpd')
  ensureServiceStopped('httpd')  
  
  unpack()

  apacheUser = 'apache'
  apacheGroup = 'apache'
  ensureDir('/etc/httpd/vhosts.d', apacheUser, apacheGroup, 644, recursive=True)
  ensureDir('/etc/httpd/vhosts.d', apacheUser, apacheGroup, 755)
  ensureDir('/etc/httpd/conf.d', apacheUser, apacheGroup, 644, recursive=True)
  ensureDir('/etc/httpd/conf.d', apacheUser, apacheGroup, 755)  
  ensureDir('/var/www', apacheUser, apacheGroup, 755, recursive=True)
  ensureDir('/var/www', apacheUser, apacheGroup, 755)
  
  # Services
  sudo('chkconfig --add httpd')
  sudo('chkconfig httpd on')
