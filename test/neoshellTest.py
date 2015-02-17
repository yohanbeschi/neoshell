import imp, os, unittest, subprocess, sys, time, __builtin__
imp.load_source('neoshell', '../src/neoshell.py')
import neoshell
from neoshell import NeoShell, NeoShellError
from neoshell import DevNull, changeWriter, restoreStdOut, directCommand
from neoshell import stripNewline, getPyFile, getAppData, getSinglePyFile, permissionsBlockToInt, permissionsToInt, getParams, addSlash
from neoshell import callback, cd, cmd, commandCheck, mkdir, pwd, rcmd, rm, sudo
from neoshell import chgrp, chmod, chown
from neoshell import ensureDir, ensureFile, getFileOrDirMetadata, getFirstNoneExistingDir, useFile, useTmp, cleanAll
from neoshell import createPackage, useForPack
from neoshell import createGroup, ensureGroup, groupExists, removeGroup
from neoshell import createUser, ensureUser, getCurrentUser, removeUser, userExists
from neoshell import ensureServiceStarted, ensureServiceStopped, getServiceStatus, serviceStart, ServiceStatus
from neoshell import CliParams, doExecute, doInstall, doDryRun, start
from neoshell import installNeoShellToRemote, executeNeoShellOnRemote, deploy, buildPackage

def getHome():
  return addSlash(os.environ.get('HOME'))
 
class SimpleFunctions(unittest.TestCase):

  def setUp(self):
    __builtin__.neoShell = NeoShell()
    changeWriter(DevNull())
    #restoreStdOut()
    
  def testStripNewline(self):
    test_result = 'Hello\nWorld'
    assert test_result == stripNewline('Hello\nWorld')
    assert test_result == stripNewline('Hello\nWorld\n')
  
  def testGetPyFile(self):
    test_result = '/home/root/python/files/myfile.py'
    assert test_result == getPyFile('/home/root/python/files/myfile.py')
    assert test_result == getPyFile('/home/root/python/files/myfile.pyc')  

  def testGetAppData_appVersion(self):
    appData = getAppData('Foo-10.2.tar.gz')
    assert appData.path == 'Foo-10.2.tar.gz'
    assert appData.name == 'Foo'
    assert appData.version == '10.2'
    assert appData.env == ''
    assert appData.local == True

  def testGetAppData_appVersionEnv(self):
    appData = getAppData('Foo-10.2-int.tar.gz')
    assert appData.path == 'Foo-10.2-int.tar.gz'
    assert appData.name == 'Foo'
    assert appData.version == '10.2'
    assert appData.env == 'int'
    assert appData.local == True
  
  def testGetAppData_notLocal(self):
    appData = getAppData('http://bar/Foo-10.2-int.tar.gz')
    assert appData.path == 'http://bar/Foo-10.2-int.tar.gz'
    assert appData.name == 'Foo'
    assert appData.version == '10.2'
    assert appData.env == 'int'
    assert appData.local == False

  def testGetAppData_wrongExt(self):
    try:
      getAppData('Foo-10.2.bar')
    except Exception as e:
      assert str(e) == "'A package MUST be a tar.gz (for Foo-10.2.bar)'"
      pass
    else:
      self.fail()

  def testGetSinglePyFile_zero(self):
    home = getHome()
    
    try:
      getSinglePyFile(home)
      self.fail()
    except Exception as e:
      assert str(e) == "'No py file found in directory: %s'" % home
  
  def testGetSinglePyFile_unknown(self):
    try:
      getSinglePyFile('foo')
      self.fail()
    except Exception as e:
      assert str(e) == '"Can\'t find a file in a directory that doesn\'t exist: foo"'
      pass
    else:
      self.fail()
      
  def testGetSinglePyFile_toomany(self):
    neoShell.buildPaths()
    ensureDir(neoShell.appWorkspaceFiles)
    cd(neoShell.appWorkspaceFiles)
    cmd('touch bar.py')
    cmd('touch foo.py')
    
    try:
      getSinglePyFile(neoShell.appWorkspaceFiles)
      self.fail()
    except Exception as e:
      assert str(e) == "'Too many py files found in directory: %s'" % neoShell.appWorkspaceFiles
      pass
    else:
      self.fail()
      
    cd(neoShell.home)
    rm(neoShell.workspace, '-rf')

  def testGetSinglePyFile_ok(self):
    neoShell.buildPaths()
    ensureDir(neoShell.appWorkspaceFiles)
    cd(neoShell.appWorkspaceFiles)
    cmd('touch foo.py')
    
    foo = getSinglePyFile(neoShell.appWorkspaceFiles)
    assert foo == '%sfoo.py' % neoShell.appWorkspaceFiles
    
    cd(neoShell.home)
    rm(neoShell.workspace, '-rf')

  def testPermissionsBlockToInt(self):
    assert 0 == permissionsBlockToInt('---')
    assert 1 == permissionsBlockToInt('--x')
    assert 2 == permissionsBlockToInt('-w-')
    assert 3 == permissionsBlockToInt('-wx')
    assert 4 == permissionsBlockToInt('r--')
    assert 5 == permissionsBlockToInt('r-x')
    assert 6 == permissionsBlockToInt('rw-')
    assert 7 == permissionsBlockToInt('rwx')  
    
  def testPermissionsToInt(self):
    assert 0 == permissionsToInt('----------')
    assert 421 == permissionsToInt('-r---w---x')
    assert 777 == permissionsToInt('-rwxrwxrwx')  
  
  def testGetParams_noarg(self):
    sys.argv = ['./neoshell.py']
    try:
      getParams()
      self.fail()
    except Exception as e:
      assert str(e) == "'Wrong parameters (at least two are needed)'"
  
  def testGetParams_onearg(self):
    sys.argv = ['./neoshell.py', 'module.py']
    try:
      getParams()
      self.fail()
    except Exception as e:
      assert str(e) == "'Wrong parameters (at least two are needed)'"
  
  def testGetParams_dryrun_1(self):
    sys.argv = ['./neoshell.py', 'module.py', 'dryrun']
    cliParams = getParams()
    assert 'module.py' == cliParams.script
    assert 'dryrun' == cliParams.operation
    assert '' == cliParams.sshUserHost
    assert '' == cliParams.sshPrivateKey
    assert '' == cliParams.appTarGz
    assert [] == cliParams.configArgs
    assert [] == cliParams.executeArgs
    assert [] == cliParams.installArgs
  
  def testGetParams_execute(self):
    sys.argv = ['./neoshell.py', 'module.py', 'execute']
    cliParams = getParams()
    assert 'module.py' == cliParams.script
    assert 'execute' == cliParams.operation
    assert '' == cliParams.sshUserHost
    assert '' == cliParams.sshPrivateKey
    assert '' == cliParams.appTarGz
    assert [] == cliParams.configArgs
    assert [] == cliParams.executeArgs
    assert [] == cliParams.installArgs
    
  # script.py dryrun <options>
  # script.py execute <options>
  def testGetParams_dryrun_2(self):
    sys.argv = ['./neoshell.py', 'module.py', 'dryrun', '-c', 'config1', 'config2', '-i', 'remote', '-e', 'local']
    cliParams = getParams()
    assert 'module.py' == cliParams.script
    assert 'dryrun' == cliParams.operation
    assert 'config1' == cliParams.configArgs[0]
    assert 'config2' == cliParams.configArgs[1]
    assert 'local' == cliParams.executeArgs[0]
    assert 'remote' == cliParams.installArgs[0]
  
  # neoshell.py install http://forge/raw/myapp.10-int.tar.gz <workspace>
  def testGetParams_install_1(self):
    sys.argv = ['./neoshell.py', 'install', 'http://forge/raw/myapp.10-int.tar.gz', 'workspace']
    cliParams = getParams()
    assert 'install' == cliParams.operation
    assert 'http://forge/raw/myapp.10-int.tar.gz' == cliParams.appTarGz
    assert 'workspace' == cliParams.workspace
    assert '' == cliParams.script
    assert '' == cliParams.sshUserHost
    assert '' == cliParams.sshPrivateKey
    assert [] == cliParams.configArgs
    assert [] == cliParams.executeArgs
    assert [] == cliParams.installArgs

  def testGetParams_install_2(self):
    sys.argv = ['./neoshell.py', 'install', 'http://forge/raw/myapp.10-int.tar.gz',
                'workspace', '-c', 'config1', 'config2', '-i', 'remote', '-e', 'local']
    cliParams = getParams()
    assert '' == cliParams.script
    assert 'install' == cliParams.operation
    assert '' == cliParams.sshUserHost
    assert '' == cliParams.sshPrivateKey
    assert 'http://forge/raw/myapp.10-int.tar.gz' == cliParams.appTarGz
    assert 'workspace' == cliParams.workspace
    assert 'config1' == cliParams.configArgs[0]
    assert 'config2' == cliParams.configArgs[1]
    assert 'local' == cliParams.executeArgs[0]
    assert 'remote' == cliParams.installArgs[0]  
    
  # neoshell.py deploy user@host privateKey http://forge/raw/myapp.10-int.tar.gz <workspace>
  def testGetParams_deploy_1(self):
    sys.argv = ['./neoshell.py', 'deploy', 'user@host', 'privateKey', 'http://forge/raw/myapp.10-int.tar.gz', 'workspace']
    cliParams = getParams()
    assert '' == cliParams.script
    assert 'deploy' == cliParams.operation
    assert 'user@host' == cliParams.sshUserHost
    assert 'privateKey' == cliParams.sshPrivateKey
    assert 'http://forge/raw/myapp.10-int.tar.gz' == cliParams.appTarGz
    assert 'workspace' == cliParams.workspace
    assert [] == cliParams.configArgs
    assert [] == cliParams.executeArgs
    assert [] == cliParams.installArgs
    
  def testGetParams_deploy_2(self):
    sys.argv = ['./neoshell.py', 'deploy', 'user@host', 'privateKey', 'http://forge/raw/myapp.10-int.tar.gz',
                'workspace', '-c', 'config1', 'config2', '-i', 'remote', '-e', 'local']
    cliParams = getParams()
    assert '' == cliParams.script
    assert 'deploy' == cliParams.operation
    assert 'user@host' == cliParams.sshUserHost
    assert 'privateKey' == cliParams.sshPrivateKey
    assert 'http://forge/raw/myapp.10-int.tar.gz' == cliParams.appTarGz
    assert 'workspace' == cliParams.workspace
    assert 'config1' == cliParams.configArgs[0]
    assert 'config2' == cliParams.configArgs[1]
    assert 'local' == cliParams.executeArgs[0]
    assert 'remote' == cliParams.installArgs[0]

class Commands(unittest.TestCase):
  
  def setUp(self):
    __builtin__.neoShell = NeoShell()
    changeWriter(DevNull())
    #restoreStdOut()
    cd(getHome())

  def testCmd_echo(self):
    out, err, ret = cmd('echo Foo')
    assert 'Foo\n' == out
    assert '' == err
    assert 0 == ret
  
  def testCmd_unknown(self):
    out, err, ret = cmd('foo bar', acceptedReturncodes=range(0,255))
    assert '' == out
    assert 0 != ret
  
  def testCommandCheck_tar(self):
    if not commandCheck('tar'):
      self.fail()

  def testCommandCheck_unknown(self):
    if commandCheck('foo', acceptedReturncodes=range(0,255)):
      self.fail()

  def testCdAndPwd(self):
    home = getHome()
    cd(home)
    currentDir = pwd()
    assert home == '%s/' % currentDir
  
  def testCallback(self):
    t1, t2 = callback(self.myFooMethodCallback(10, 5))
    assert t1 == 10
    assert t2 == 5
  
  def myFooMethodCallback(self, i1, i2):
    def myFooMethod():
      return (i1, i2)
     
    return myFooMethod
    
  """  
  def testSudo(self):
    limited = 'ls -l /etc/sudoers.d'
    out, err, ret = cmd(limited, acceptedReturncodes=range(0,255))
    assert ret != 0
    out, err, ret = sudo(limited)
    assert ret == 0
  """
  
  def testMkdirAndRm(self):
    home = getHome()
    newDir = '%snsTest' % home
    out, err, ret = mkdir(newDir)
    assert ret == 0
    out, err, ret = cmd('ls -l %s' % newDir)
    assert ret == 0
    out, err, ret = rm(newDir, '-r')
    assert ret == 0
    out, err, ret = cmd('ls -l %s' % newDir, acceptedReturncodes=range(0,255))
    assert ret != 0
  
  # ---- Permissions
  """
  def testChown(self):
    mkdir(neoShell.appWorkspaceFiles, '-pv')
    cd(neoShell.appWorkspace)
    cmd('touch myfile.txt')
    metadata = getFileOrDirMetadata('myfile.txt')
  """
  
  # ---- File and Directory
  def testGetFirstNoneExistingDir(self):
    dir = getFirstNoneExistingDir('/etc/foo')
    assert dir == '/etc/foo'
    
    dir = getFirstNoneExistingDir('/etc/bar/')
    assert dir == '/etc/bar'
    
    dir = getFirstNoneExistingDir('/etc/foo/bar/')
    assert dir == '/etc/foo'

  def testGetFileOrDirMetadata(self):
    neoShell.buildPaths()
    ensureDir(neoShell.appWorkspaceFiles)
    cd(neoShell.appWorkspaceFiles)
    cmd('touch myfile.txt')
    
    metadata = getFileOrDirMetadata('myfile.txt')
    
    user = getCurrentUser()

    assert metadata.user == user
    assert metadata.group == user
    
    cd(neoShell.home)
    rm(neoShell.workspace, '-rf')

  def testGetFileOrDirMetadata(self):
    neoShell.buildPaths()
    ensureDir(neoShell.appWorkspaceFiles)
    metadata = getFileOrDirMetadata(neoShell.appWorkspaceFiles)
    
    user = getCurrentUser()
    assert metadata.user == user
    assert metadata.group == user
    
    rm(neoShell.workspace, '-rf')

  
  def testEnsureFile(self):
    neoShell.buildPaths()
    ensureDir(neoShell.appWorkspaceFiles)
    cd(neoShell.appWorkspaceFiles)
    cmd('touch myfile.txt')
    
    createUser('bar')
    ensureFile('myfile.txt', 'bar', 'bar', 600)
    
    metadata = getFileOrDirMetadata('myfile.txt')
    print metadata.permissions
    assert metadata.user == 'bar'
    assert metadata.group == 'bar'
    assert metadata.permissions.startswith('-rw-------')
    
    removeUser('bar', rmHome=True)
    cd(neoShell.home)
    rm(neoShell.workspace, '-rf')

  def testEnsureDir(self):
    neoShell.buildPaths()
    
    createUser('bar')
    ensureDir(neoShell.appWorkspaceFiles, 'bar', 'bar', 777)
    
    metadata = getFileOrDirMetadata(neoShell.appWorkspaceFiles)
    assert metadata.user == 'bar'
    assert metadata.group == 'bar'
    assert metadata.permissions.startswith('drwxrwxrwx')
    
    removeUser('bar', rmHome=True)
    sudo('rm -rf %s' % neoShell.workspace)
   
  def testUseFile(self):
    neoShell.buildPaths()
    
    cmd('touch myfile.txt')
    useFile('myfile.txt')
    
    metadata = getFileOrDirMetadata('%smyfile.txt' % neoShell.appWorkspaceFiles)
    user = getCurrentUser()
    assert metadata.user == user
    assert metadata.group == user
    
    rm('myfile.txt')
    rm(neoShell.workspace, '-rf')

  def testUseTmp(self):
    neoShell.buildPaths()
    
    cmd('touch myfile.txt')
    useTmp('myfile.txt')
    
    metadata = getFileOrDirMetadata('%smyfile.txt' % neoShell.appWorkspaceTmp)
    user = getCurrentUser()
    assert metadata.user == user
    assert metadata.group == user
  
    rm('myfile.txt')
    rm(neoShell.workspace, '-rf')
    
  def testUseForPack(self):
    neoShell.buildPaths()
    ensureDir(neoShell.appWorkspaceFiles)
    cd(neoShell.appWorkspaceFiles)
    cmd('touch myfile.txt')
    cmd('touch myfile2.txt')
    
    useForPack('%smyfile.txt' % neoShell.appWorkspaceFiles, 'var/test/')
    useForPack('%smyfile2.txt' % neoShell.appWorkspaceFiles, '/var/test/')
    
    metadata = getFileOrDirMetadata('%svar/test/myfile.txt' % neoShell.appWorkspacePackage)
    user = getCurrentUser()
    assert metadata.user == user
    assert metadata.group == user
    
    metadata = getFileOrDirMetadata('%svar/test/myfile2.txt' % neoShell.appWorkspacePackage)
    assert metadata.user == user
    assert metadata.group == user
    
    cd(neoShell.home)
    rm(neoShell.workspace, '-rf')
    
  def testCreatePackage_withapp(self):
    neoShell.buildPaths()
    ensureDir(neoShell.appWorkspaceFiles)
    cd(neoShell.appWorkspaceFiles)
    cmd('touch myfile.txt')
    
    useForPack('%smyfile.txt' % neoShell.appWorkspaceFiles, 'var/test/')
    
    neoShell.modulePyFile = getPyFile(__file__)
    createPackage()

    cd(neoShell.appWorkspace)
    _, _, ret = cmd('tar -ztvf MyApp-0.tar.gz -o pack.tar.gz')
    assert ret == 0

    _, _, ret = cmd('tar -ztvf MyApp-0.tar.gz -o neoshellTest.py')
    assert ret == 0
    
    _, _, ret = cmd('tar -ztvf pack.tar.gz -o var/test/myfile.txt')
    assert ret == 0
    
    cd(neoShell.home)
    rm(neoShell.workspace, '-rf')
   
  def testCreatePackage_withoutapp(self):
    neoShell.buildPaths()
    ensureDir(neoShell.appWorkspaceFiles)
    cd(neoShell.appWorkspaceFiles)
    
    neoShell.modulePyFile = getPyFile(__file__)
    createPackage()

    cd(neoShell.appWorkspace)
    _, _, ret = cmd('tar -ztvf MyApp-0.tar.gz -o pack.tar.gz', acceptedReturncodes=range(0,255))
    assert ret != 0

    _, _, ret = cmd('tar -ztvf MyApp-0.tar.gz -o neoshellTest.py')
    assert ret == 0
    
    cd(neoShell.home)
    rm(neoShell.workspace, '-rf')
    
  # ---- Group
  
  def testGroupExists_unknown(self):
    if groupExists('foo'):
      self.fail()
  
  def testCreateAndRemoveGroup_new(self):
    out, err, ret = createGroup('foo')
    assert ret == 0
    
    if not groupExists('foo'):
      self.fail()

    removeGroup('foo')
    
    if groupExists('foo'):
      self.fail()
  
  def testCreateAndRemoveGroup_existing(self):
    createGroup('foo', acceptedReturncodes=range(0,255))
    out, err, ret = createGroup('foo', acceptedReturncodes=range(0,255))
    assert ret != 0
    removeGroup('foo')

  def testEnsureGroup_new(self):
    if groupExists('foo'):
      self.fail()
      
    ensureGroup('foo')
    
    if not groupExists('foo'):
      self.fail()
      
    removeGroup('foo')  
  
  def testEnsureGroup_existing(self):
    createGroup('foo')
    if not groupExists('foo'):
      self.fail()
      
    ensureGroup('foo')
    
    if not groupExists('foo'):
      self.fail()
      
    removeGroup('foo')
    
    if groupExists('foo'):
      self.fail()
  
  # ---- User
  
  def testUserExists_known(self):
    user = getCurrentUser()

    if not userExists(user):
      self.fail()
      
  def testUserExists_unknown(self):
    if userExists('bar'):
      self.fail()    
      
  def testCreateAndRemoveUser(self):
    createUser('bar', createHome=True)
    
    if not userExists('bar'):
      self.fail()    
    
    removeUser('bar', rmHome=True)
    
    if userExists('bar'):
      self.fail()
      
  def testEnsureUser_new(self):    
    if userExists('bar'):
      self.fail()
      
    ensureUser('bar')
    
    if not userExists('bar'):
      self.fail()
      
    removeUser('bar', rmHome=True)

  def testEnsureUser_existing(self):
    createUser('bar')
    if not userExists('bar'):
      self.fail()
      
    ensureUser('bar')
    
    if not userExists('bar'):
      self.fail()
      
    removeUser('bar', rmHome=True)
    
    if userExists('bar'):
      self.fail()
  
  # ---- Service
  """
  def testGetServiceStatus_unknown(self):
    serviceStatus = getServiceStatus('foo')
    assert serviceStatus == ServiceStatus.UNRECOGNIZED
    
  def testGetServiceStatus_known(self):
    serviceStatus = getServiceStatus('ntpd')
    assert serviceStatus == ServiceStatus.RUNNING
  
  def testEnsureServiceStarted_started(self):
    ensureServiceStarted('ntpd')
    serviceStatus = getServiceStatus('ntpd')
    assert serviceStatus == ServiceStatus.RUNNING
    
  def testEnsureServiceStarted_stopped(self):
    ensureServiceStopped('httpd')

    ensureServiceStarted('httpd')
    serviceStatus = getServiceStatus('httpd')
    assert serviceStatus == ServiceStatus.RUNNING  
    
    ensureServiceStopped('httpd')
    serviceStatus = getServiceStatus('httpd')
    assert serviceStatus == ServiceStatus.STOPPED  

  def testServiceStart_started(self):
    ensureServiceStarted('httpd')

    serviceStart('httpd')

    serviceStatus = getServiceStatus('httpd')
    assert serviceStatus == ServiceStatus.RUNNING  
    
  def testServiceStart_stopped(self):
    ensureServiceStopped('httpd')
    
    serviceStart('httpd')
    serviceStatus = getServiceStatus('httpd')
    assert serviceStatus == ServiceStatus.RUNNING

  def testGetServiceStatus(self):
    _, _, ret = sudo('yum search tomcat7', acceptedReturncodes=range(0, 255))
    print '@@', ret
  """
"""
class NeoShellRemoteTest(unittest.TestCase):
  sshUser = 'ec2-user'
  sshHost = '172.23.1.148'
  sshUserHost = '%s@%s' % (sshUser, sshHost)

  def setUp(self):
    __builtin__.neoShell = NeoShell()
    changeWriter(DevNull())
    restoreStdOut()
    
  def testInstallNeoShellToRemote(self):
    installNeoShellToRemote('%s.ssh/awskey.pem' % getHome(), self.sshUserHost)
    _, _, ret = directCommand('ssh -t -i %s.ssh/awskey.pem -oStrictHostKeyChecking=no %s ls /usr/local/bin/neoshell.py' % (getHome(), self.sshUserHost), readStdout=True)
    assert ret == 0
    
    rcmd("ssh -t -i %s.ssh/awskey.pem -oStrictHostKeyChecking=no %s 'sudo rm /usr/local/bin/neoshell.py'" % (getHome(), self.sshUserHost))
    rcmd("ssh -t -i %s.ssh/awskey.pem -oStrictHostKeyChecking=no %s 'rm MyApp-0.tar.gz;rm -rf /home/ec2-user/myworkspace'" % (getHome(), self.sshUserHost))
  
  def testExecuteNeoShellOnRemote(self):
    # create package
    doExecute('installOnRemoteTest.py')
    
    # send package to remote
    values = ('%s.ssh/awskey.pem' % getHome(), '%sMyApp-0.tar.gz' % neoShell.appWorkspace, self.sshUserHost)
    cmd('scp -i %s -oStrictHostKeyChecking=no %s %s:.' % values, nsCall=True)
    
    # install package on remote
    installNeoShellToRemote('%s.ssh/awskey.pem' % getHome(), self.sshUserHost)
    executeNeoShellOnRemote('%s.ssh/awskey.pem' % getHome(), self.sshUserHost, 'MyApp-0.tar.gz', '/home/ec2-user/myworkspace')
    
    rcmd("ssh -t -i %s.ssh/awskey.pem -oStrictHostKeyChecking=no %s 'sudo rm /usr/local/bin/neoshell.py'" % (getHome(), self.sshUserHost))
    rcmd("ssh -t -i %s.ssh/awskey.pem -oStrictHostKeyChecking=no %s 'rm MyApp-0.tar.gz;rm -rf /home/ec2-user/myworkspace'" % (getHome(), self.sshUserHost))
    cleanAll()
  
  def testDeploy(self): 
    # Call doExecute to prepare a tar.gz
    doExecute('doInstallTest.py')
    
    deploy(self.sshUser, self.sshHost, '%s.ssh/awskey.pem' % getHome(), '%sMyApp-0.tar.gz' % neoShell.appWorkspace, '/home/ec2-user/myworkspace')
    
    rcmd("ssh -t -i %s.ssh/awskey.pem -oStrictHostKeyChecking=no %s 'sudo rm /usr/local/bin/neoshell.py'" % (getHome(), self.sshUserHost))
    rcmd("ssh -t -i %s.ssh/awskey.pem -oStrictHostKeyChecking=no %s 'rm MyApp-0.tar.gz;rm -rf /home/ec2-user/myworkspace'" % (getHome(), self.sshUserHost))
    cmd('rm -f MyApp-0.tar.gz')
    cleanAll()
"""
class NeoShellTest(unittest.TestCase):
  def setUp(self):
    __builtin__.neoShell = NeoShell()
    changeWriter(DevNull())
    #restoreStdOut()
    
  def testDoExecute(self):
    doExecute('doExecuteTest.py')
    
    metadata = getFileOrDirMetadata('%sfoo.txt' % neoShell.appWorkspaceFiles)
    user = getCurrentUser()
    assert metadata.user == user
    assert metadata.group == user
    
    cleanAll()
  
  def testDoInstall(self):
    oldWorkspace = '%s/ns.workspace' % neoShell.home
    newWorkspace = '%s/fakeWorkspace' % neoShell.home
    
    # Call doExecute to prepare a tar.gz
    doExecute('doInstallTest.py')
    
    # Call doInstall
    cliParams = CliParams('', 'install', appTarGz='MyApp-0.tar.gz', workspace=newWorkspace)
    doInstall(cliParams)
  
    metadata = getFileOrDirMetadata('%sdoInstallTest.py' % neoShell.appWorkspace)
    user = getCurrentUser()
    assert metadata.user == user
    assert metadata.group == user
    
    metadata = getFileOrDirMetadata('%spack.tar.gz' % neoShell.appWorkspace)
    assert metadata.user == user
    assert metadata.group == user

    cleanAll()
    cd(neoShell.home)
    rm('MyApp-0.tar.gz')
    cmd('rm -rf %s' % oldWorkspace)

  def testDoDryRun(self):
    cliParams = CliParams('doDryRunTest.py', 'dryrun')
    doDryRun(cliParams)
    
  def testStart(self):
    sys.argv = ['neoshell.py', 'doDryRunTest.py', 'dryrun']
    start()
  
  def testBuildPackage(self):
    oldWorkspace = '%s/ns.workspace' % neoShell.home
    newWorkspace = '%s/fakeWorkspace' % neoShell.home
    
    # Call start to prepare a mega tar.gz
    sys.argv = ['neoshell.py', 'buildPackageTest.py', 'execute']
    start()
    
    # Call doInstall
    cliParams = CliParams('', 'install', appTarGz='GlobalPackage-1.0.tar.gz', workspace=newWorkspace)
    doInstall(cliParams)
    cleanAll()
    cd(neoShell.home)
    rm('GlobalPackage-1.0.tar.gz')
    cmd('rm -rf %s' % oldWorkspace)
  
if __name__ == "__main__":
  __builtin__.neoShell = NeoShell()
  cmd('sudo cp %s /usr/local/bin;sudo chmod +x /usr/local/bin/neoshell.py' % getPyFile(neoshell.__file__))
  unittest.main()