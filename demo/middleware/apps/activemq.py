#!/usr/local/bin/neoshell.py
# -*- coding: utf-8 -*-
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, buildPaths, getScriptDir, workspace, addSlash, cleanAll, executeScript
from neoshell import cd, cmd, rcmd, createPackage, ensureDir, useForPack, unpack, ensureFile, lns, chown, cp, ensureGroup, ensureUser, sudo, chmod, cleanAll

activemqVersion = '5.9.1'
distDir = 'apache-activemq-%s' % activemqVersion
distArch = '%s-bin.tar.gz' % distDir
mirror = 'http://apache.crihan.fr/dist/activemq'

# Packaging pour ActiveMQ 5.9.1 d'après les instructions qui se trouvent ici :
# http://activemq.apache.org/getting-started.html#GettingStarted-InstallationProcedureforUnix
# et ici : http://activemq.apache.org/unix-service.html
def execute():
  cd(getScriptDir())
  cd('../..') # devops/middleware/apps => devops
  targetDir = '%starget/' % addSlash(neoShell.currentDir)
  cmd('rm -rf %s*' % targetDir)
  ensureDir(targetDir)
  workspace(targetDir)

  appName('activemq')
  version(activemqVersion)
  buildPaths()

  ensureDir(neoShell.appWorkspaceTmp)
  cd(neoShell.appWorkspaceTmp)
  rcmd('wget {mirror}/{version}/{archive}'.format(mirror = mirror, version = activemqVersion, archive = distArch)) # Comment to test
  cmd('tar -xvzf %s' % distArch)

  activemqHomeNoFirstSlash = 'opt/activemq'

  useForPack('%s/bin' % (distDir), activemqHomeNoFirstSlash)
  useForPack('%s/conf' % (distDir), activemqHomeNoFirstSlash)
  useForPack('%s/data' % (distDir), activemqHomeNoFirstSlash)
  useForPack('%s/lib' % (distDir), activemqHomeNoFirstSlash)
  useForPack('%s/webapps' % (distDir), activemqHomeNoFirstSlash)
  useForPack('%s/activemq-all-5.9.1.jar' % (distDir), activemqHomeNoFirstSlash)

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

  ensureUser('activemq', group='activemq', fullname='ActiveMQ Service Account', createHome=True)
  ensureDir('/opt/activemq', 'activemq', 'activemq', recursive=True)