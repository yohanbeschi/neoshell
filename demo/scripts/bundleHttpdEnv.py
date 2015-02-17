#!/usr/local/bin/neoshell.py
# -*- coding: utf-8 -*-
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, env, version, workspace, buildPaths, createPackage, executeScript, addSlash, cleanAll, ensureParams, ensureDir, getScriptDir
from neoshell import cd, cmd, unpack, replaceVariables, useForPack, callback, ensureServiceStarted, addSudoer, ensureUsers, useFile, binaryRepo, installPackage, echo, ensureFile, lns

def execute():
  kissutils = __import__('kissutils')
  
  ensureParams(neoShell.executeArgs, 1, 'Usage: bundleBackOfficeEnv.py execute -e <env>')
  environment = neoShell.executeArgs[0]
  
  cd(getScriptDir())
  cd('..') # devops/scripts => devops
  devopsDir = addSlash(neoShell.currentDir)
  targetDir = '%starget/' % devopsDir
  cmd('rm -rf %s*' % targetDir)
  ensureDir(targetDir)
  workspace(targetDir)
  
  # ---- In devops - Get the current build version
  buildVersion = callback(kissutils.callbackGetFileContent('%sBUILDVERSION' % addSlash(neoShell.currentDir)))
  
  appName('bus.httpd')
  version(buildVersion)
  env(environment)
  buildPaths()
  ensureDir(neoShell.appWorkspaceTmp)
  cd(neoShell.appWorkspaceTmp)
  
  pathToTemplates = devopsDir + 'middleware/templates'
  pathToMergedTemplates = neoShell.appWorkspaceTmp + 'mergedTemplates'
  templates = {
                pathToTemplates + '/apache/vhosts.d/bus-external.conf.tpl':		pathToMergedTemplates + '/apache/vhosts.d/bus-external.conf',
                pathToTemplates + '/apache/vhosts.d/map.hosts-cibles.tpl':		pathToMergedTemplates + '/apache/vhosts.d/map.hosts-cibles',
                pathToTemplates + '/apache/vhosts.d/bus-internal.conf.tpl':		pathToMergedTemplates + '/apache/vhosts.d/bus-internal.conf',
                pathToTemplates + '/apache/conf/httpd.conf.tpl': 				      pathToMergedTemplates + '/apache/conf/httpd.conf'
  }
  dictionary = devopsDir + 'configuration/' + environment + '.json'
  replaceVariables(templates, dictionary)
  
  useForPack(pathToMergedTemplates + '/apache/vhosts.d', 'etc/httpd')
  useForPack(pathToMergedTemplates + '/apache/conf', 'etc/httpd')
  useFile('%sconfiguration/sudoers-%s' % (devopsDir, environment))
  useFile('%sconfiguration/users-%s.xml' % (devopsDir, environment))
  
  createPackage()
 
  # Publish the binary
  cd(neoShell.workspace)
  cd('../../forge/scripts') # devops/target => forge/scripts
  forgeScriptsDir = addSlash(neoShell.currentDir)
  packagePath = '%s%s' % (neoShell.appWorkspace, neoShell.compressedFile)
  executeScript('%spublishBinary.py' % forgeScriptsDir, executeArgs=[packagePath])
 
  cleanAll()
  
def install():
  ensureParams(neoShell.installArgs, 3, 'Usage: bundleHttpdEnv.py install -i <binary Host> <bus version> <environment>')
  host = addSlash(neoShell.installArgs[0])
  version = neoShell.installArgs[1]
  environment = neoShell.installArgs[2]

  binaryRepo(host + 'bus.httpd/')
  echo('binaryRepo: %s' % neoShell.binaryRepo)
  installPackage('bus.httpd-%s-common' % version)
  
  unpack()
  
  apacheUser = 'apache'
  apacheGroup = 'apache'
  ensureDir('/etc/httpd/vhosts.d', apacheUser, apacheGroup, 644, recursive=True)
  ensureDir('/etc/httpd/vhosts.d', apacheUser, apacheGroup, 755)
  ensureDir('/etc/httpd/conf.d', apacheUser, apacheGroup, 644, recursive=True)
  ensureDir('/etc/httpd/conf.d', apacheUser, apacheGroup, 755)  
  ensureDir('/var/log/httpd', apacheUser, apacheGroup, 755)
  ensureDir('/var/www', apacheUser, apacheGroup, 755, recursive=True)
  ensureDir('/var/www', apacheUser, apacheGroup, 755)
  
  ensureFile('/etc/httpd/conf/httpd.conf', 'root', 'root', 644)  
  
  lns('/var/log/httpd', '/var/www/logs')
  lns('/etc/httpd/vhosts.d', '/var/www/conf')
  
  addSudoer('%ssudoers-%s' % (neoShell.appWorkspaceFiles, environment))
  
  usersXml = '%susers-%s.xml' % (neoShell.appWorkspaceFiles, environment)
  ensureUsers(usersXml)

  ensureServiceStarted('httpd')