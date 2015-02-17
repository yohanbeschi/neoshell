#!/usr/local/bin/neoshell.py
# -*- coding: utf-8 -*-
import imp, kissutils
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
import xml.etree.ElementTree as ET
from neoshell import appName, env, version, buildPaths, createPackage, executeScript, addSlash, cleanAll, ensureParams, CliParams
from neoshell import cd, cmd, getAppData, doDeploy

# Deploy on one environment
def execute():
  ensureParams(neoShell.executeArgs, 4, 'Usage: deployApplication.py execute -e <binary host> <application name> <environment> <instance infos xml file>')

  binaryHost = addSlash(neoShell.executeArgs[0]) #http://172.23.1.148/packages
  appName_ = neoShell.executeArgs[1]
  env_ = neoShell.executeArgs[2]
  xmlFileName = neoShell.executeArgs[3]
  
  # ---- In devops
  cd('../../devops') # forge/scripts => devops
  devopsDir = addSlash(neoShell.currentDir)
  instanceXmlPath = '%starget/%s' % (devopsDir, xmlFileName)

  if len(neoShell.executeArgs) == 5:
    buildVersion = neoShell.executeArgs[4]
  else:
    buildVersion = kissutils.getFileContent('%sBUILDVERSION' % addSlash(neoShell.currentDir))

  appName(appName_)
  version(buildVersion)
  env(env_)

  buildPaths()
  
  tree = ET.parse(instanceXmlPath)
  root = tree.getroot()
  privateIp = root.find('./instance/privateIp').text
  unixUser = root.find('./instance/unixUser').text
  privateKeyPath = root.find('./instance/privateKeyPath').text
  
  appData = getAppData(neoShell.compressedFile)
  appTarGz = '%s%s/%s' % (binaryHost, appData.name, neoShell.compressedFile)
  sshUserHost = '%s@%s' % (unixUser, privateIp)
  workspace='/home/%s/ns.workspace/' % unixUser
  
  # Deploy
  cliParams = CliParams('', 'deploy', 
                            sshUserHost=sshUserHost,
                            sshPrivateKey=privateKeyPath,
                            appTarGz=appTarGz,
                            workspace=workspace,
                            installArgs=[binaryHost, buildVersion, env_])  
                         
  doDeploy(cliParams)