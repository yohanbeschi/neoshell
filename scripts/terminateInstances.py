#!/usr/local/bin/neoshell.py
# -*- coding: utf-8 -*-
import imp, os
import ec2instance as ec2
import xml.etree.ElementTree as ET
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import ensureParams, ensureEnvVar, getScriptDir, addSlash, ensureDir, workspace, buildPaths
from neoshell import cd

def execute():
  ensureParams(neoShell.executeArgs, 1, 'Usage: terminateInstances.py execute -e <removed instances xml file>')
  removedInstancesFile = neoShell.executeArgs[0]

  ensureEnvVar('KISS_awsRegion')
  ensureEnvVar('KISS_awsKey')
  ensureEnvVar('KISS_awsPassword')
  
  region = os.environ['KISS_awsRegion'] 
  awsKey = os.environ['KISS_awsKey'] 
  awsPassword = os.environ['KISS_awsPassword']  
  
  # ---- In devops
  cd(getScriptDir())
  cd('../../devops') # forge/scripts => devops
  devopsDir = addSlash(neoShell.currentDir)
  targetDir = '%starget/' % devopsDir
  
  filePath = '%s%s' % (targetDir, removedInstancesFile)
  tree = ET.parse(filePath)
  root = tree.getroot()
  instanceIds = root.findall('./instanceId')
  
  if len(instanceIds) > 0:
    toTerminate = []
    for instanceId in instanceIds:
      toTerminate.append(instanceId.text)

    ec2.terminateInstances(region, awsKey, awsPassword, toTerminate)
