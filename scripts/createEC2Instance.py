#!/usr/local/bin/neoshell.py
# -*- coding: utf-8 -*-
import imp, os
import ec2instance as ec2
import xml.etree.ElementTree as ET
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import ensureParams, ensureEnvVar, getScriptDir, addSlash, ensureDir, workspace, buildPaths
from neoshell import cd, cmd, echo

# TODO : should be able to deal with multiple KISS_securityGroupIds
# But be careful, create one and only one instance in this script and don't use multithreading. Instead use multiple jobs in Go
def execute():
  ensureParams(neoShell.executeArgs, 2, 'Usage: createEC2Instances.py execute -e <environment> <instance infos xml file>')
  xmlFileName = neoShell.executeArgs[1]

  ensureEnvVar('KISS_amiName')
  ensureEnvVar('KISS_awsRegion')
  ensureEnvVar('KISS_keyName')
  ensureEnvVar('KISS_subnetId')
  ensureEnvVar('KISS_securityGroupIds')
  ensureEnvVar('KISS_availabilityZone')
  ensureEnvVar('KISS_projet')
  ensureEnvVar('KISS_env')
  ensureEnvVar('KISS_responsable')
  ensureEnvVar('KISS_rebootnocturne')
  ensureEnvVar('KISS_sauvegardenocturne')
  ensureEnvVar('KISS_pemFile')
  ensureEnvVar('KISS_unixUser')
  ensureEnvVar('KISS_awsKey')
  ensureEnvVar('KISS_awsPassword')
  ensureEnvVar('KISS_instanceType')
  ensureEnvVar('KISS_instanceName')
  ensureEnvVar('KISS_applicationName')

  pemFile = os.environ['KISS_pemFile']
  if not os.path.exists(pemFile):
    raise NeoShellError('Private key not found: %s' % pemFile)

  region = os.environ['KISS_awsRegion'] 
  awsKey = os.environ['KISS_awsKey'] 
  awsPassword = os.environ['KISS_awsPassword'] 
  amiName = os.environ['KISS_amiName'] 
  instanceType = os.environ['KISS_instanceType'] 
  keyName = os.environ['KISS_keyName'] 
  subnetId = os.environ['KISS_subnetId'] 
  securityGroupIds = os.environ['KISS_securityGroupIds'] 
  availabilityZone = os.environ['KISS_availabilityZone'] 
  tags = {}
  tags['Name'] = os.environ['KISS_applicationName']
  tags['projet'] = os.environ['KISS_projet']
  tags['applicationName'] = os.environ['KISS_applicationName']
  tags['env'] = neoShell.executeArgs[0]
  tags['responsable'] = os.environ['KISS_responsable']
  tags['rebootnocturne'] = os.environ['KISS_rebootnocturne']
  tags['sauvegardenocturne'] = os.environ['KISS_sauvegardenocturne']

  if neoShell.dryRun:
    instanceId, privateIpAddress = '1', '2'
  else:
    instanceId, privateIpAddress = ec2.createInstance(region, awsKey, awsPassword, amiName, instanceType, keyName,
                                 subnetId, [securityGroupIds], availabilityZone, tags)
    msg = 'A new instance has been created - instanceId: %s - privateIpAddress: %s' % (instanceId, privateIpAddress)
    echo(msg)

  cd(getScriptDir())
  cd('..') # forge/scripts => forge
  targetDir = '%starget/' % addSlash(neoShell.currentDir)
  cmd('rm -rf %s*' % targetDir)
  ensureDir(targetDir)
  workspace(targetDir)
  buildPaths()

  unixUser = os.environ['KISS_unixUser'] 
  ec2Obj = ET.Element('ec2')
  instance = ET.SubElement(ec2Obj, 'instance')
  instanceIdObj = ET.SubElement(instance, 'instanceId')
  instanceIdObj.text = instanceId
  privateIpObj = ET.SubElement(instance, 'privateIp')
  privateIpObj.text = privateIpAddress
  unixUserObj = ET.SubElement(instance, 'unixUser')
  unixUserObj.text = unixUser
  privateKeyPathObj = ET.SubElement(instance, 'privateKeyPath')
  privateKeyPathObj.text = pemFile
  
  tree = ET.ElementTree(ec2Obj)
  filePath = '%s%s' % (targetDir, xmlFileName)
  tree.write(filePath)
