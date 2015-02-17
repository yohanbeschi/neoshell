#!/usr/local/bin/neoshell.py
# -*- coding: utf-8 -*-
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, buildPaths, getScriptDir, addSlash, workspace, cleanAll, executeScript
from neoshell import cd, cmd, rcmd, createPackage, ensureDir, useForPack, unpack, ensureFile, lns, chown, cp, ensureGroup, ensureUser, sudo, chmod

# Packaging pour Mule 3.4.0 pour Tomcat d'après les instructions qui se trouvent ici :
# http://www.mulesoft.org/documentation/display/current/Deploying+Mule+as+a+Service+to+Tomcat
# Ce script est compatible avec la 3.5.0, il suffit de modifier la variable muleVersion
def execute():
  cd(getScriptDir())
  cd('../..') # devops/middleware/apps => devops
  targetDir = '%starget/' % addSlash(neoShell.currentDir)
  cmd('rm -rf %s*' % targetDir)
  ensureDir(targetDir)
  workspace(targetDir)
  
  muleVersion = '3.4.0'
  appName('mule')
  version(muleVersion)
  buildPaths()
  
  distDir = 'mule-standalone-%s' % muleVersion
  distArch = '%s.tar.gz' % distDir
  mirror = 'http://dist.codehaus.org/mule/distributions'
  
  ensureDir(neoShell.appWorkspaceTmp)
  cd(neoShell.appWorkspaceTmp)
  rcmd('wget %s/%s' % (mirror, distArch))
  cmd('tar -xvzf %s' % distArch)
  cd(distDir)

  tomcatHomeNoFirstSlash = 'usr/share/tomcat7'
  muleLibsDir = 'mule-libs'
  
  muleLibsDestDir = tomcatHomeNoFirstSlash + '/' + muleLibsDir
  useForPack('lib/endorsed', muleLibsDestDir)
  useForPack('lib/mule', muleLibsDestDir)
  useForPack('lib/opt', muleLibsDestDir)
  useForPack('lib/shared', muleLibsDestDir)
  useForPack('lib/user', muleLibsDestDir)	
  useForPack('lib/boot/commons-cli-1.2.jar', muleLibsDestDir + '/opt')
  useForPack('lib/boot/log4j-1.2.16.jar', muleLibsDestDir + '/opt')  
  useForPack('lib/boot/mule-module-logging-' + muleVersion + '.jar', muleLibsDestDir + '/opt')  
  useForPack('lib/boot/wrapper-3.2.3.jar', muleLibsDestDir + '/opt')  
  
  createPackage()
 
  # Publish the binary
  cd(neoShell.workspace)
  cd('../../forge/scripts') # devops/target => forge/scripts
  forgeScriptsDir = addSlash(neoShell.currentDir)
  packagePath = '%s%s' % (neoShell.appWorkspace, neoShell.compressedFile)
  executeScript('%spublishBinary.py' % forgeScriptsDir, executeArgs=[packagePath])
 
  cleanAll()

def install():
  unpack()
  
  ensureDir('/usr/share/tomcat7/mule-libs/', 'root', 'tomcat', recursive=True)
