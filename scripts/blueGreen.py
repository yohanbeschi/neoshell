#!/usr/local/bin/neoshell.py
# -*- coding: utf-8 -*-
import imp, ec2elb, ec2instance, os
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
import xml.etree.ElementTree as ET
from neoshell import appName, env, version, buildPaths, createPackage, executeScript, addSlash, cleanAll, ensureEnvVar, ensureParams, getScriptDir
from neoshell import cd, cmd, unpack, ensureDir, echo

def execute():
  ensureParams(neoShell.executeArgs, 3, 'Usage: blueGreen.py execute -e <elbName> <instances infos xml files> <removed instances xml file>')
  elbName = neoShell.executeArgs[0]
  xmlFilesAsStr = neoShell.executeArgs[1]
  removedInstancesFile = neoShell.executeArgs[2]

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
  
  xmlFiles = xmlFilesAsStr.split(',')
  
  newInstanceIds = []
  for xmlFile in xmlFiles:
    instanceXmlPath = '%starget/%s' % (devopsDir, xmlFile)
    tree = ET.parse(instanceXmlPath)
    root = tree.getroot()
    instanceId = root.find('./instance/instanceId').text
    newInstanceIds.append(instanceId)
  
  removedInstanceIds = ec2elb.elbSwitch(region, awsKey, awsPassword, elbName, newInstanceIds)
  
  echo('Starting to create %s' % removedInstancesFile)
  ec2 = ET.Element('ec2-removed')
  
  if len(removedInstanceIds) > 0:
    # Stop removed instances
    ec2instance.stopInstances(region, awsKey, awsPassword, removedInstanceIds)
    
    # Add removed instance ID to a xml file
    for removed in removedInstanceIds:
      instanceId = ET.SubElement(ec2, 'instanceId')
      instanceId.text = removed
     
  tree = ET.ElementTree(ec2)
  ensureDir(targetDir)
  filePath = '%s%s' % (targetDir, removedInstancesFile)
  tree.write(filePath)  