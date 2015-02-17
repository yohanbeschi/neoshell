#!/usr/local/bin/neoshell.py
import imp, os
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, env, buildPaths, getScriptDir, useFile, cd, ensureFile, addSudoer, sudo, createPackage, addSlash, ensureEnvVar
from neoshell import cmd, rcmd, ensureDir, getPyFile, useForPack, unpack, ensureServiceStopped, ensureServiceStarted, cp, serviceStart, executeScript
from neoshell import cleanAll, workspace, rm, buildPackage, echo, installPackage

def execute():
  ensureEnvVar('KISS_passwordGithub')
  ensureEnvVar('KISS_passwordEC2')
  ensureEnvVar('KISS_passwordMvn')
  passwordGithub = os.environ['KISS_passwordGithub'] 
  passwordEC2 = os.environ['KISS_passwordEC2'] 
  passwordMvn = os.environ['KISS_passwordMvn'] 
  
  appName('goagent')
  version('14.2.0')
  env('noenv')
  
  cd(getScriptDir())
  goagentDir = addSlash(neoShell.currentDir)
  cd('../..') # forge/apps/goagent => forge
  forgeDir = addSlash(neoShell.currentDir)
  targetDir = '%starget/' % forgeDir
  cmd('rm -rf %s*' % targetDir)
  ensureDir(targetDir)
  workspace(targetDir)
  
  buildPaths()

  cd(forgeDir)
  cd('apps/system')
  systemDir = addSlash(neoShell.currentDir)
  cd('../ssh')
  sshDir = addSlash(neoShell.currentDir)
  
  useFile('%ssudoers' % systemDir)
  useFile('%sgo-sudoer' % goagentDir)
  useFile('%sprivate.repo' % goagentDir)
  useForPack('%sgo-agent' % goagentDir, '/etc/default/')
  useForPack('%s.gitconfig' % goagentDir, '/var/go/')
  
  # SSH files
  cd(sshDir)
  cmd('github_key=%s;export github_key;openssl enc -d -aes-256-cbc -a -in forge.enc -pass env:github_key > forge;unset github_key' % passwordGithub, hide=True)
  cmd('ec2_key=%s;export ec2_key;openssl enc -d -aes-256-cbc -a -in awskey.enc -pass env:ec2_key > awskey.pem;unset ec2_key' % passwordEC2, hide=True)
  useForPack('awskey.pem', '/var/go/.ssh')
  useForPack('forge', '/var/go/.ssh')
  useForPack('config', '/var/go/.ssh') 
  rm('awskey.pem')
  rm('forge')
  
  # Libs
  cd(forgeDir)
  cd('libs')
  useFile('kissutils')
  
  buildPackage('%sapps/maven/maven.py' % forgeDir, moveTo=neoShell.appWorkspaceFiles, executeArgs=[passwordMvn])
  
  # create Package
  createPackage()
  
  # Publish the binary
  cd(forgeDir)
  cd('scripts')
  forgeScriptsDir = addSlash(neoShell.currentDir)
  packagePath = '%s%s' % (neoShell.appWorkspace, neoShell.compressedFile)
  executeScript('%spublishBinary.py' % forgeScriptsDir, executeArgs=[packagePath])
 
  cleanAll()
  
def install():
  sudo('cp %s /etc/yum.repos.d' % '%sprivate.repo' % neoShell.appWorkspaceFiles)
  ensureDir('/etc/yum.repos.d', 'root', 'root')
  ensureFile('/etc/yum.repos.d/private.repo', 'root', 'root')
  
  sudo('yum update -y > yum_update.log')
  sudo('ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime')
  sudo('yum install -y wget java-1.7.0-openjdk java-1.7.0-openjdk-devel git')
  sudo('yum install -y go-agent --nogpgcheck')

  unpack()
  
  installPackage('%sapache.maven-3.2.2-noenv.tar.gz' % neoShell.appWorkspaceFiles)
  
  ensureDir('/etc', 'root', 'root', 755)
  ensureDir('/etc/default', 'root', 'root', 755)
  ensureFile('/etc/default/go-agent', 'go', 'go', 644)
  
  ensureDir('/var', 'root', 'root', 755)
  ensureDir('/var/go', 'go', 'go', 755)
  ensureDir('/var/go/.ssh', 'go', 'go', 700)
  ensureFile('/var/go/.ssh/config', 'go', 'go', 600)
  ensureFile('/var/go/.ssh/awskey.pem', 'go', 'go', 600)
  ensureFile('/var/go/.ssh/forge', 'go', 'go', 600)
  ensureFile('/var/go/.gitconfig', 'go', 'go', 664)
  
  # Replace sudoers
  sudoers = '%ssudoers' % neoShell.appWorkspaceFiles
  sudo('visudo -c -f %s' % sudoers)
  sudo('cp %s /etc' % sudoers)
  
  # Add new sudoer
  addSudoer('%sgo-sudoer' % neoShell.appWorkspaceFiles)
  
  # Git
  # Add github to known_hosts
  sudo("runuser -s /bin/bash go -c 'ssh -T -oStrictHostKeyChecking=no git@github'", acceptedReturncodes=range(0,255))
  
  # Update libs kissutils + boto (Dirty)
  installBoto()
  installKissUtils()
  
  # Everything is ready, start the agent
  serviceStart('go-agent')
  
def installBoto():
  # Boto
  echo('---- Get and install Boto ----')
  
  cd(neoShell.home)
  cmd('git clone https://github.com/boto/boto.git boto')

  cd('boto')
  sudo('python27 setup.py install')
  sudo('python27 setup.py clean')

def installKissUtils():
  echo('---- Install KissUtils ----')
  cd('%skissutils' % addSlash(neoShell.appWorkspaceFiles))
  sudo('python27 setup.py install')
  cmd('python27 setup.py clean')
  
  