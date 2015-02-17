#!/usr/local/bin/neoshell.py
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, buildPaths, getScriptDir
from neoshell import ensureEnvVar, ensureInputs, ensureParams
from neoshell import addSudoer, callback, cd, cp, cmd, echo, ensureDir, ensureFile, mkdir, sudo, useFile, useForPack, rm
from neoshell import ensureServiceStarted, serviceStart, deploy, buildPackage, createPackage, installPackage, unpack, chown
import os
import json

def prepareBoto():
  # Boto
  echo('---- Get and install Boto ----')
  
  botoPath = '%sboto/' % neoShell.home
  fromSource = True
  if os.path.exists(botoPath):
    cd(botoPath)
    cmd('git pull')
  else:
    try:
      __import__('boto')
      fromSource = False
      echo('Nothing to do. Boto is already present on the system.')
    except:
      cd(neoShell.home)
      cmd('git clone https://github.com/boto/boto.git %s' % botoPath)

  if fromSource:
    cd(botoPath)
    sudo('python27 setup.py install')
    sudo('python27 setup.py clean')

def prepareKissUtils(path):
  echo('---- Install KissUtils ----')
  cd('%skissutils' % path)
  sudo('python27 setup.py install')
  cmd('python27 setup.py clean')
  sudo('rm -rf build')
  sudo('rm -rf dist')
  sudo('rm -rf *.egg-info')  
  
def prepareSSH(forgePath, passwordGithub, passwordEC2):
  # SSH
  # Encrypt: openssl enc -aes-256-cbc -a -salt -in file.txt -out file.enc
  # Decrypt: \/
  cd('%sapps/ssh' % getScriptDir())
  cmd('github_key=%s;export github_key;openssl enc -d -aes-256-cbc -a -in forge.enc -pass env:github_key > forge;unset github_key' % passwordGithub, hide=True)
  cmd('ec2_key=%s;export ec2_key;openssl enc -d -aes-256-cbc -a -in awskey.enc -pass env:ec2_key > awskey.pem;unset ec2_key' % passwordEC2, hide=True)
  cp('awskey.pem', '%s.ssh' % neoShell.home)
  ensureFile('%s.ssh/awskey.pem' % neoShell.home, neoShell.user, neoShell.user, 600)
  useForPack('awskey.pem', '/var/go/.ssh')
  useForPack('forge', '/var/go/.ssh')
  useForPack('config', '/var/go/.ssh')
  rm('awskey.pem')
  rm('forge')

def initForge(config):
  def createEC2instance():
    with open(config, 'r') as file:
      instanceConfiguration = json.load(file)

    file.close()
    ec2 = __import__('ec2instance')
    return ec2.createInstance_Dict(instanceConfiguration)
    
  return createEC2instance
  
def execute():
  appName('kiss.forge')
  version('0.1')
  buildPaths()
  
  cmd('rm -f %s.ssh/known_hosts' % neoShell.home)
  
  ensureEnvVar('USER')
  ensureParams(neoShell.executeArgs, 4, 'Missing arguments: ./createforge.sh -e <ec2 template> <github key password> <aws key password> <mvn settings password>')
  ec2Template = neoShell.executeArgs[0]
  passwordGithub = neoShell.executeArgs[1]
  passwordEC2 = neoShell.executeArgs[2]
  passwordMvn = neoShell.executeArgs[3]
  
  forgePath = getScriptDir()
  echo('Forge path: %s' % forgePath)

  prepareBoto()
  cmd('sudo yum install -y python27')
  prepareKissUtils('%slibs/' % forgePath)
  prepareSSH(forgePath, passwordGithub, passwordEC2)
  
  cd('%sapps' % forgePath)
  useForPack('private.repo', '/etc/yum.repos.d/')
  cd('%slibs' % getScriptDir())
  useFile('kissutils')
  useFile('%sapps/system/sudoers' % getScriptDir())
  
  buildPackage('%sapps/ant/ant.py' % getScriptDir(), moveTo=neoShell.appWorkspaceFiles)
  buildPackage('%sapps/go/go.py' % getScriptDir(), moveTo=neoShell.appWorkspaceFiles)
  buildPackage('%sapps/maven/maven.py' % getScriptDir(), moveTo=neoShell.appWorkspaceFiles, executeArgs=[passwordMvn])
  buildPackage('%sapps/nexus/nexus.py' % getScriptDir(), moveTo=neoShell.appWorkspaceFiles)
  buildPackage('%sapps/sonar/sonar.py' % getScriptDir(), moveTo=neoShell.appWorkspaceFiles)
  buildPackage('%sapps/tomcat7/tomcat7.py' % getScriptDir(), moveTo=neoShell.appWorkspaceFiles)
  
  createPackage()
  
  #privateIP = '172.23.1.148'
  #deploy('ec2-user', privateIP, '%s.ssh/awskey.pem' % neoShell.home, '%skiss.forge-0.1.tar.gz' \
  #        % neoShell.appWorkspace, '/home/ec2-user/myworkspace')

  if neoShell.dryRun:
    callback(initForge(ec2Template))
  else:
    instanceId, privateIP = callback(initForge(ec2Template))
    echo('New ec2 instance %s/%s' % (instanceId, privateIP))
    
    deploy('ec2-user', privateIP, '%s.ssh/awskey.pem' % neoShell.home, '%skiss.forge-0.1.tar.gz' \
          % neoShell.appWorkspace, '/home/ec2-user/myworkspace')
    
    echo('Apache %s' % privateIP)
    echo('Nexus %s:8080/nexus' % privateIP)
    echo('Go %s:8081/go' % privateIP)
    echo('Sonar %s:8082' % privateIP)

def install():
  buildPaths()
  
  forgePath = getScriptDir()
  echo('Forge path: %s' % forgePath)

  sudo('yum update -y > yum_update.log')
  sudo('ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime')
  sudo('yum install -y wget httpd java-1.7.0-openjdk java-1.7.0-openjdk-devel tomcat7 git createrepo > yum_install.log')
  sudo('chkconfig --add httpd')
  sudo('chkconfig httpd on')
    
  unpack()
  
  # Apache
  ensureDir('/var/www/html/centos-6/6.5/contrib/x86_64/', 'root', 'root')
  ensureDir('/var/www/html/packages/', 'root', 'root')
  chown('/var/www/', 'root', 'root', args='-R')
  ensureDir('/etc/yum.repos.d', 'root', 'root')
  ensureFile('/etc/yum.repos.d/private.repo', 'root', 'root')
  sudo('createrepo /var/www/html/centos-6/6.5/contrib/x86_64/')
  
  # Other packages
  installPackage('%sapache.ant-1.9.4.tar.gz' % neoShell.appWorkspaceFiles)
  installPackage('%sapache.maven-3.2.2.tar.gz' % neoShell.appWorkspaceFiles)
  installPackage('%sthoughtworks.go-14.2.0.tar.gz' % neoShell.appWorkspaceFiles)
  installPackage('%ssonatype.nexus-2.8.1.tar.gz' % neoShell.appWorkspaceFiles, installArgs=[neoShell.appWorkspaceFiles])
  installPackage('%ssonarqube-4.4.tar.gz' % neoShell.appWorkspaceFiles)

  # Misc
  prepareBoto()
  prepareKissUtils(neoShell.appWorkspaceFiles)
 
  # SSH
  sshDir = '/var/go/.ssh/'
  ensureDir('/var', 'root', 'root', 755)
  ensureDir('/var/go', 'go', 'go', 755)
  ensureDir(sshDir, 'go', 'go', 700)
  ensureFile('%sconfig' % sshDir, 'go', 'go', 600)
  ensureFile('%sforge' % sshDir, 'go', 'go', 600)
  ensureFile('%sawskey.pem' % sshDir, 'go', 'go', 600)
  
  # Git
  # Copier le fichier .gitconfig présent apps/goagent
  #cmd('git config --global user.name "%s"' % 'Kiss-forge')
  #cmd('git config --global user.email %s' % 'kiss.forge@canalplus.com')
  # Add github to known_hosts
  sudo("runuser -s /bin/bash go -c 'ssh -T -oStrictHostKeyChecking=no git@github'", acceptedReturncodes=range(0,255))
  
  # Modify sudoers
  sudoers = '%ssudoers' % neoShell.appWorkspaceFiles
  ensureFile(sudoers, 'root', 'root', 440)
  sudo('visudo -c -f %s' % sudoers)
  sudo('cp %s /etc' % sudoers)
