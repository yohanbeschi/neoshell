#!/usr/bin/python27
import imp
import io
import json
import sys
import os
import platform
import time
import traceback
import subprocess
import __builtin__
import xml.etree.ElementTree as ET

OPERATIONS = ['deploy', 'dryrun', 'execute', 'install']
dryRun = ('Dry run', '', 0)

#----------------------------------------------------------------------------------------------------------------------
# Utility classes
#----------------------------------------------------------------------------------------------------------------------
    
class NeoShellError(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)

class CliParams:
  def __init__(self, script, operation, sshUserHost='', sshPrivateKey='', appTarGz='', workspace='', configArgs=[], executeArgs=[], installArgs=[]):
    self.script = script
    self.operation = operation
    self.sshUserHost = sshUserHost
    self.sshPrivateKey = sshPrivateKey
    self.appTarGz = appTarGz
    self.workspace = workspace
    self.configArgs = configArgs
    self.executeArgs = executeArgs
    self.installArgs = installArgs
    
class MsgType:
  INFO, EXT_CMD, CMD, DRY_RUN, SUCCESS, FAILURE = range(1, 7)
  
class Template:
  def __init__(self, template, target, encoding):
    self.template = template
    self.target = target
    self.encoding = encoding

class Metadata:
  def __init__(self, permissions, user, group, modificationDate):
    self.permissions = permissions
    self.user = user
    self.group = group
    self.modificationDate = modificationDate

class AppData:
  def __init__(self, path, name, filename, version='0', env=None, local=True):
    self.path = path
    self.name = name
    self.filename = filename
    self.version = version
    self.env = env
    self.local = local

class User:
  def __init__(self, name, uid, gid, fullname, home, shell):    
    self.name = name
    self.uid = uid
    self.gid = gid
    self.fullname = fullname
    self.home = home
    self.shell = shell
 
class Group:
  def __init__(self, name, gid, members):
    self.name = name
    self.gid = gid
    self.members = members

# -------------- NeoShell
class NeoShell:
  contexts = []
  dontRebuildWorkspace = False
  modulePyFile = None
  
  dryRun = False
  currentDir = os.getcwd()
  originalStdOut = sys.stdout
  
  appName = 'MyApp'
  version = '0'
  env = None
  binaryRepo = ''
  
  home = os.environ.get('HOME')
  workspace = None
  appWorkspace = None
  workspaceName = 'ns.workspace'
  
  executeArgs = []
  installArgs = []
    
  def buildPaths(self):
    self.user = getCurrentUser(nsCall=True)
    
    if self.env:
      self.compressedFile = '%s-%s-%s.tar.gz' % (self.appName, self.version, self.env)
    else:  
      self.compressedFile = '%s-%s.tar.gz' % (self.appName, self.version)
    
    self.home = addSlash(self.home)
        
    if not self.workspace:
      self.workspace = '%s%s/' % (self.home, self.workspaceName)
      
    self.workspace = addSlash(self.workspace)
    
    self.appWorkspace = '%s%s/%s/' % (self.workspace, self.appName, self.version)
    
    if self.env:
      self.appWorkspace = '%s%s/' % (self.appWorkspace, self.env)
    
    self.appWorkspaceFiles = '%sfiles/' % self.appWorkspace
    self.appWorkspaceTmp = '%stmp/' % self.appWorkspace
    self.appWorkspacePackage = '%spackage/' % self.appWorkspace
    
    info('\/------ after NeoShell.buildPaths() ------\/')
    self.show()
  
  def saveContext(self):
    ns = NeoShell()
    self.contexts.append(ns)
    
    ns.modulePyFile = self.modulePyFile
    ns.dryRun = self.dryRun
    ns.currentDir = self.currentDir
    ns.appName = self.appName
    ns.version = self.version
    ns.env = self.env
    ns.binaryRepo = self.binaryRepo
    ns.user = self.user
    ns.compressedFile = self.compressedFile
    ns.home = self.home
    ns.workspace = self.workspace
    ns.appWorkspace = self.appWorkspace
    ns.appWorkspaceFiles = self.appWorkspaceFiles
    ns.appWorkspaceTmp = self.appWorkspaceTmp
    ns.appWorkspacePackage = self.appWorkspacePackage
    ns.executeArgs = self.executeArgs
    ns.installArgs = self.installArgs
  
  def restoreContext(self):
    ns = self.contexts.pop()
    
    self.modulePyFile = ns.modulePyFile
    self.dryRun = ns.dryRun
    self.currentDir = ns.currentDir
    self.appName = ns.appName
    self.version = ns.version
    self.env = ns.env
    self.binaryRepo = ns.binaryRepo
    self.user = ns.user
    self.compressedFile = ns.compressedFile
    self.home = ns.home
    self.workspace = ns.workspace
    self.appWorkspace = ns.appWorkspace
    self.appWorkspaceFiles = ns.appWorkspaceFiles
    self.appWorkspaceTmp = ns.appWorkspaceTmp
    self.appWorkspacePackage = ns.appWorkspacePackage
    self.executeArgs = ns.executeArgs
    self.installArgs = ns.installArgs
    
    info('\/------ after NeoShell.restoreContext() ------\/')
    self.show()
    
  def show(self):
    info('dryRun: %s' % self.dryRun)
    info('appName: %s' % self.appName)
    info('version: %s' % self.version)
    info('env: %s' % self.env)
    info('binaryRepo: %s' % self.binaryRepo)
    info('user: %s' % self.user)
    info('compressedFile: %s' % self.compressedFile)
    info('home: %s' % self.home)
    info('workspace: %s' % self.workspace)
    info('appWorkspace: %s' % self.appWorkspace)
    info('appWorkspaceFiles: %s' % self.appWorkspaceFiles)
    info('appWorkspaceTmp: %s' % self.appWorkspaceTmp)
    info('appWorkspacePackage: %s' % self.appWorkspacePackage)
    info('executeArgs: [%s]' % ','.join(self.executeArgs))
    info('installArgs: [%s]' % ','.join(self.installArgs))
    info('/\--------------------------------------------/\\')
  
#----------------------------------------------------------------------------------------------------------------------
# Functions
#----------------------------------------------------------------------------------------------------------------------
def stripNewline(text):
  if text and text.endswith('\n'):
    text = text[:len(text) - 1]
    
  return text
  
#---------------------------------------------------------
# ---- Output
#---------------------------------------------------------
class DevNull:
  def write(self, ojb):
    return None

class Writer:
  def __init__(self, *stdouts):
    self.stdouts = stdouts
      
  def write(self, obj):
    for s in self.stdouts:
      s.write(obj)

def stdout(msg):
  msg = stripNewline(msg)

  if len(msg) > 0:
    sys.stdout.write('%s\n' % msg)

def formattedOutput(text, out='', err='', returncode=0, acceptedReturncodes=[0], nsCall=False, msgType=MsgType.CMD): 
  stdout(formatOutput(text, out, err, returncode, acceptedReturncodes, nsCall, msgType))
    
def formatOutput(text, out='', err='', returncode=0, acceptedReturncodes=[0], nsCall=False, msgType=MsgType.CMD): 
  msg = []

  if nsCall:
    msg.append('[Internal]')
  else:
    msg.append('[External]')
  
  if msgType == MsgType.INFO:
    msg.append('[INFO___]')
  elif msgType == MsgType.EXT_CMD:
    msg.append('[__\/___]')
  elif msgType == MsgType.DRY_RUN:
    msg.append('[DRYRUN_]')
  elif msgType == MsgType.SUCCESS:
    msg.append('[SUCCESS]')
  elif msgType == MsgType.FAILURE:
    msg.append('[FAILURE]')  
  elif returncode in acceptedReturncodes:
    msg.append('[OK_____]')
  else:
    msg.append('[ERROR__]')
  
  msg.append('[%s] %s' % (platform.node(), text))
  
  if msgType == MsgType.CMD:
    msg.append('\n  >>> Output:\n%s%s' % (out, err))
  
  return ''.join(msg)

def info(msg):
  formattedOutput(msg, nsCall=True, msgType=MsgType.INFO)

def intListToString(list):
  return ', '.join("'{0}'".format(n) for n in list)
  
#---------------------------------------------------------
# ---- Helpers
#---------------------------------------------------------
def addSlash(path):
  if not path.endswith('/'):
    path += '/'

  return path

def getFileDir(file):
  return addSlash(os.path.abspath(os.path.dirname(file)))

def getScriptDir():
  return getFileDir(neoShell.modulePyFile)
  
def getPyFile(file):
  pyFile = os.path.abspath(file)
  
  if pyFile.endswith('c'):
    pyFile = pyFile[:len(pyFile) - 1]
   
  info('pyFile: ' + pyFile)
   
  return pyFile
  
def getAppData(packagePath):

  if not packagePath.endswith('.tar.gz'):
    raise NeoShellError('A package MUST be a tar.gz (for %s)' % packagePath)
  
  wPackagePath = packagePath.replace('.tar.gz', '')
  
  local = True
  env = None
  
  if '://' in wPackagePath:
    local = False
  
  appIndex = wPackagePath.rfind('/')
  if appIndex != -1:
    wPackagePath = wPackagePath[appIndex + 1:len(wPackagePath)]
  
  filename = '%s.tar.gz' % wPackagePath
  elements = wPackagePath.split('-')
  length = len(elements)
  
  if length < 2:
    raise NeoShellError('A package name MUST, at least, contain a name and a version - ie. <Foo>-<version> (for %s)' % packagePath)
    
  if length >= 2:
    name = elements[0]
    version = elements[1]
  if length >= 3:
    env = elements[2]
  
  return AppData(packagePath, name, filename, version, env, local)

def getSinglePyFile(directory):
  if not os.path.exists(directory):
    raise NeoShellError('Can\'t find a file in a directory that doesn\'t exist: %s' % directory)

  files = ['%s%s' % (directory, f) for f in os.listdir(directory) if f.endswith('.py') and os.path.isfile('%s%s' % (directory, f))]

  if len(files) == 0:
    raise NeoShellError('No py file found in directory: %s' % directory)
  elif len(files) > 1:
    raise NeoShellError('Too many py files found in directory: %s' % directory)
  
  return files[0]
  
def importScript(script):
  if os.path.exists(script) and script.endswith('.py'):
    scriptModuleName = script[script.rfind('/') + 1:len(script) - 3]
    scriptModule = imp.load_source(scriptModuleName, script)
    neoShell.modulePyFile = getPyFile(scriptModule.__file__)
    return scriptModuleName, scriptModule
  else:
    raise NeoShellError('Invalid or not found python script named: %s' % script)

def permissionsToInt(permissions):
  assert isinstance(permissions, basestring)

  if len(permissions) == 10:
    start = 1
  else:
    start = 0
  
  end = start+3
  owner = permissionsBlockToInt(permissions[start:end])
  start = end
  end += 3
  group = permissionsBlockToInt(permissions[start:end])
  start = end
  end += 3
  other = permissionsBlockToInt(permissions[start:end])
  
  return owner * 100 + group * 10 + other

def permissionsBlockToInt(permissions):  
  execute = 1 if permissions[2] != '-' else 0
  write = 2 if permissions[1] == 'w' else 0
  read = 4 if permissions[0] == 'r' else 0
  
  return execute + write + read

def getParams():
  script = ''
  operation = ''
  sshUserHost = ''
  sshPrivateKey = ''
  appTarGz = ''
  workspace = ''
  configArgs = ''
  executeArgs = ''
  installArgs = ''
  index = 1
  
  printUsageOnCondition(2, 'Wrong parameters (at least two are needed)')
    
  tmp = sys.argv[index]

  if tmp.endswith('.py'): # dryrun or execute
    script = tmp
    index += 1
    operation = sys.argv[index]
  else:
    operation = tmp
  
  index += 1

  if operation not in OPERATIONS:
    printUsageOnCondition(100, 'Unknown operation %s should be one of these [%s]' % (operation, ', '.join(OPERATIONS)))
  
  if operation == 'deploy':
    printUsageOnCondition(4, 'Wrong parameters (missing sshUserHost and/or sshPrivateKey)')
    sshUserHost = sys.argv[index]
    index += 1
    sshPrivateKey = sys.argv[index]
    index += 1
    
  if operation == 'deploy' or operation == 'install':
    printUsageOnCondition(index + 1, 'Wrong parameters (missing appTarGz and/or workspace)')
    appTarGz = sys.argv[index]
    index += 1
    workspace = sys.argv[index]
    index += 1

  config = []
  execute = []
  install = []
  
  current = ''
  for val in sys.argv[index:]:
    if val == '-c':
      current = 'c'
    elif val == '-e':
      current = 'e'
    elif val == '-i':
      current = 'i'
    elif current == 'c':
      config.append(val)
    elif current == 'e':
      execute.append(val)
    elif current == 'i':
      install.append(val)
    else:
      info('Unexpected argument: %s' % val)
  
  info('script: %s' % script)
  info('operation: %s' % operation)
  info('config: %s' % ', '.join(config))
  info('execute: %s' % ', '.join(execute))
  info('install: %s' % ', '.join(install))

  return CliParams(script, operation, sshUserHost, sshPrivateKey, appTarGz, workspace, config, execute, install)

def printUsageOnCondition(value, msg):
  if len(sys.argv) < (value + 1):
    usage()
    raise NeoShellError(msg)
    
def usage():
  stdout('NeoShell Usage:')
  stdout('<script>.py dryrun <options>')
  stdout('<script>.py execute <options>')
  stdout('neoshell.py deploy <user@host> <privateKey> <url_to_app or path_to_app>.tar.gz <workspace>')
  stdout('neoshell.py install <url_to_app or path_to_app>.tar.gz <workspace>')
  
#---------------------------------------------------------
# ---- Configuration
#---------------------------------------------------------

def appName(appName):
  neoShell.appName = appName

def version(version):
  neoShell.version = version

def env(env):
  neoShell.env = env
  
def workspace(workspace):
  if not neoShell.dontRebuildWorkspace:
    neoShell.workspace = workspace
  
def workspaceName(workspaceName):
  neoShell.workspaceName = workspaceName

def buildPaths():
  neoShell.buildPaths()
 
def binaryRepo(binaryRepo):
  neoShell.binaryRepo = binaryRepo
 
def decorate(decorate):  
  neoShell.decorate = decorate

#---------------------------------------------------------
# ---- Inputs and params
#---------------------------------------------------------
  
def ensureInputs(number, msg):
  if len(sys.argv) - 1 < number:
    raise NeoShellError(msg)

def ensureParams(params, number, msg):
  if len(params) < number:
    raise NeoShellError(msg)

def ensureEnvVar(varName, notBlank=True):
  var = os.environ.get(varName)
  
  if var == None or notBlank and var == '':
    raise NeoShellError('Missing environment variable: ' + varName)

#---------------------------------------------------------
# ---- Commands
#--------------------------------------------------------- 
def directCommand(command, readStdout=False):
  if readStdout:
    p = subprocess.Popen(command,
                       shell=True,
                       cwd=neoShell.currentDir)
    p.communicate()
    return '', '', p.returncode
  else:
    p = subprocess.Popen(command, 
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       shell=True,
                       cwd=neoShell.currentDir)

    out, err = p.communicate()
    return out, err, p.returncode

def __indirectCommand__(function, commandDetail, nsCall=False, hide=False):
  if neoShell.dryRun:
    if not hide:
      formattedOutput(commandDetail, nsCall=nsCall, msgType=MsgType.DRY_RUN)
    else:
      formattedOutput('** hidden command **', nsCall=nsCall, msgType=MsgType.DRY_RUN)
    return dryRun
  else:
    return function()
    
def cmd(command, nsCall=False, acceptedReturncodes=[0], hide=False):
  def callback():
    out, err, ret = directCommand(command)
    
    if not hide:
      formattedOutput(command, out, err, ret, acceptedReturncodes, nsCall)
    else:
      formattedOutput('** hidden command **', out, err, ret, acceptedReturncodes, nsCall)
      
    if ret not in acceptedReturncodes:
      raise NeoShellError(err)

    return out, err, ret
    
  return __indirectCommand__(callback, command, nsCall, hide)

def rcmd(command, nsCall=False, acceptedReturncodes=[0], hide=False):
  def callback():
    if not hide:
      formattedOutput(command, msgType=MsgType.EXT_CMD)
      
    out, err, ret = directCommand(command, True)

    if ret not in acceptedReturncodes:
      raise NeoShellError(err)
      
    return out, err, ret 
  
  return __indirectCommand__(callback, command, nsCall, hide)
    
def cd(directory, nsCall=False, acceptedReturncodes=[0]): 
  command = 'cd %s' % directory
  cmd(command, nsCall=nsCall, acceptedReturncodes=acceptedReturncodes)
  cmdInternal = '%s;pwd' % command
  outInternal, _, _ = cmd(cmdInternal, nsCall=True, acceptedReturncodes=acceptedReturncodes)
  
  if not neoShell.dryRun:
    neoShell.currentDir = stripNewline(outInternal)

  return neoShell.currentDir  
    
def pwd(nsCall=False):
  formattedOutput('pwd', neoShell.currentDir, msgType=MsgType.DRY_RUN if neoShell.dryRun else MsgType.CMD)
  return neoShell.currentDir

def cmdWithArgsOne(command, one, args=None, nsCall=False, acceptedReturncodes=[0]):
  commands = [command]
  
  if args:
    commands.append(args)

  commands.append(one)
  return cmd(' '.join(commands), nsCall, acceptedReturncodes)  

def cmdWithArgsTwo(command, one, two, args=None, nsCall=False, acceptedReturncodes=[0]):
  commands = [command]
  
  if args:
    commands.append(args)

  commands.append(one)
  commands.append(two)
  return cmd(' '.join(commands), nsCall, acceptedReturncodes)

def sudo(command, nsCall=False, acceptedReturncodes=[0]):
  return cmdWithArgsOne('sudo', command, None, nsCall, acceptedReturncodes)

def rsudo(command, nsCall=False, acceptedReturncodes=[0]):
  return rcmd('sudo %s' % command, nsCall, acceptedReturncodes)   
  
def lns(fileOrDir, link, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'lns(fileOrDir=%s, link=%s, nsCall=%s, acceptedReturncodes=%s)' % (fileOrDir, link, nsCall, intListToString(acceptedReturncodes))
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
  
    metadata = getFileOrDirMetadata(link, nsCall=nsCall)
    
    if not metadata:
      return sudo('ln -s %s %s' % (fileOrDir, link))
    elif metadata.permissions[0] != 'l':  
      raise NeoShellError('Impossible to set a symlink. A file or directory already exists')
  
  return __indirectCommand__(callback, commandDetail, nsCall)
  
def echo(msg, nsCall=False, acceptedReturncodes=[0]):
  if not msg:
    msg = 'NothingToEcho'

  return cmdWithArgsOne('echo', msg,  None, nsCall, acceptedReturncodes)
    
def mkdir(directory, args=None, nsCall=False, acceptedReturncodes=[0]):
  return cmdWithArgsOne('mkdir', directory, args, nsCall, acceptedReturncodes)

def rm(fileOrDir, args=None, nsCall=False, acceptedReturncodes=[0]):
  return cmdWithArgsOne('rm', fileOrDir, args, nsCall, acceptedReturncodes)

def cp(fileOrDir, to, args=None, nsCall=False, acceptedReturncodes=[0]):
  return cmdWithArgsTwo('cp', fileOrDir, to, args, nsCall, acceptedReturncodes)
    
def callback(function, nsCall=False):
  functionName = '%s()' % function.__name__
  
  def callback():
    formattedOutput(functionName)
    out, err, ret = '', '', 0
    
    try:
      returnedValue = function()
      out = 'Function called: ' + functionName
    except:
      err = traceback.format_exc()
      ret = 1
      
    formattedOutput(functionName, out, err, ret, acceptedReturncodes=[0], nsCall=nsCall)
    
    if ret != 0:
      raise NeoShellError(err)
    
    return returnedValue
  
  return __indirectCommand__(callback, functionName, nsCall)
  
def replaceVariables(templates, dictionary, encoding='utf-8', nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'Replacing variables inside templates'
  
  def callback():
    try:
      with io.open(dictionary, 'r', encoding=encoding) as values:
        variablesAsDict = json.load(values)
        values.close()

      out = 'Dictionary loaded: ' + dictionary + '\n'
         
      for template, output in templates.iteritems():
        
        with io.open(template, 'r', encoding=encoding) as openedTemplate:
          fileAsString = openedTemplate.read()
          openedTemplate.close()
          out += 'Template read: ' + template + '\n'

        for key, value in variablesAsDict.iteritems():
          if isinstance(value, list):
            value = '\n'.join(value)
          elif isinstance(value, dict):
            value = value['separator'].join(value['values'])
            
          fileAsString = fileAsString.replace('@{' + key + '}', value) 
      
        directory = os.path.dirname(output)
        if not os.path.exists(directory):
          mkdir(directory, '-pv', True)
          out += 'Directory created: ' + directory + '\n'

        with io.open(output, 'w', encoding=encoding) as newFile:
          newFile.write(fileAsString)
          newFile.close()

        out += 'File written: ' + output + '\n'

      err = ''
      ret = 0
      
    except ValueError as e:
      out = ''
      err = 'JSON parsing error - ' + str(e)
      ret = 1
    except Exception as e:
      out = ''
      err = str(e)
      ret = 1
    
    formattedOutput(commandDetail, out, err, ret, acceptedReturncodes, nsCall)
    
    if ret not in acceptedReturncodes:
      raise NeoShellError(err)
      
    return out, err, ret
  
  return __indirectCommand__(callback, commandDetail, nsCall)
  
def commandCheck(command, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'Is command installed? %s' % command
  
  def callback():
    formattedOutput(commandDetail, nsCall=nsCall)
    _, _, ret = cmd("which '%s'" % command, nsCall=True, acceptedReturncodes=acceptedReturncodes)
    return ret == 0
  
  return __indirectCommand__(callback, commandDetail, nsCall)
  
#---------------------------------------------------------
# ---- Permissions
#--------------------------------------------------------- 

def chown(file, user='', group='', args='', nsCall=False, acceptedReturncodes=[0]):
  assert file and (user or group)
  
  if group:
    group = ':%s' % group
  
  command = 'chown %s %s%s %s' % (args, user, group, file)

  return sudo(command, nsCall, acceptedReturncodes)

def chgrp(file, group, args='', nsCall=False, acceptedReturncodes=[0]):
  assert file and group
  
  command = 'chgrp %s %s %s' % (args, group, file)

  return sudo(command, nsCall, acceptedReturncodes)

def chmod(file, mode, args='', nsCall=False, acceptedReturncodes=[0]):
  assert file and mode
  
  command = 'chmod %s %s %s' % (args, mode, file)

  return sudo(command, nsCall, acceptedReturncodes)
  
#---------------------------------------------------------
# ---- Files and directories
#---------------------------------------------------------

def getFirstNoneExistingDir(dir):
  prev = None

  while True:
    if os.path.exists(dir):
      return prev
    else:
      prev = dir
      lastIndex = dir.rfind('/')
      
      if lastIndex > 0:
        dir = dir[0:lastIndex]
      else:
        return prev

def getFileOrDirMetadata(fileOrDir, nsCall=False):
  out, _, ret = sudo('ls -ld %s' % fileOrDir, nsCall=nsCall, acceptedReturncodes=range(0, 255))
  
  if ret == 0:
    elements = out.split(' ')
    return Metadata(elements[0], elements[2], elements[3], elements[5])  
  else:
    None
  
def ensureFile(file, user=None, group=None, permissions=None, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'ensureFile(%s, %s, %s, %s, %s)' % (file, user, group, permissions, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    out, _, ret = sudo('ls -l %s' % file, True, range(0, 255))
    
    if ret != 0:
      raise NeoShellError('File does not exist: %s' % file)

    ensureFileOrDir(file, out, user, group, permissions, recursive=False, nsCall=nsCall, acceptedReturncodes=acceptedReturncodes)

  return __indirectCommand__(callback, commandDetail, nsCall)
    
def ensureDir(directory, user=None, group=None, permissions=None, recursive=False, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'ensureDir(%s, %s, %s, %s, %s)' % (directory, user, group, permissions, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    out, _, ret = sudo('ls -ld %s' % directory, True, range(0, 255))
    
    if ret != 0:
      dir = getFirstNoneExistingDir(directory)

      sudo('mkdir -pv %s' % directory, True)
      
      if user is None and group is None:
        userTmp = getCurrentUser(nsCall=True)
        chown(dir, user if user else userTmp, group if group else userTmp, args='-R')
      
      out, _, ret = sudo('ls -ld %s' % directory, True, range(0, 255))

    ensureFileOrDir(directory, out, user, group, permissions, recursive, nsCall=nsCall, acceptedReturncodes=acceptedReturncodes)
  
  return __indirectCommand__(callback, commandDetail, nsCall)
  
def ensureFileOrDir(fileOrDir, lsResult, user=None, group=None, permissions=None, recursive=False, nsCall=False, acceptedReturncodes=[0]):  
  elements = lsResult.split(' ')
  foundPerm = elements[0]
  foundUser = elements[2]
  foundGroup = elements[3]

  args = '-R' if recursive else ''
  
  if user and foundUser != user and group and foundGroup != group:
    chown(fileOrDir, user, group, args=args, nsCall=True, acceptedReturncodes=acceptedReturncodes)
  elif user and foundUser != user:
    chown(fileOrDir, user, args=args, nsCall=True, acceptedReturncodes=acceptedReturncodes)
  elif group and foundGroup != group:
    chgrp(fileOrDir, group, args=args, nsCall=True, acceptedReturncodes=acceptedReturncodes)

  if permissions:
    permissionsAsInt = permissionsToInt(foundPerm)
    if permissions != permissionsAsInt:
      chmod(fileOrDir, permissions, args=args, nsCall=True, acceptedReturncodes=acceptedReturncodes)

def useFile(fileOrDir, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'useFile(fileOrDir=%s, nsCall=%s, acceptedReturncodes=%s)' % (fileOrDir, nsCall, intListToString(acceptedReturncodes))
  
  def callback():
    use(fileOrDir, neoShell.appWorkspaceFiles, nsCall=True, acceptedReturncodes=acceptedReturncodes)
    
  return __indirectCommand__(callback, commandDetail, nsCall)  

def useTmp(file, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'useTmp(file=%s, nsCall=%s, acceptedReturncodes=%s)' % (file, nsCall, intListToString(acceptedReturncodes))
  
  def callback():
    use(file, neoShell.appWorkspaceTmp, nsCall=True, acceptedReturncodes=acceptedReturncodes)
    
  return __indirectCommand__(callback, commandDetail, nsCall)

def use(fileOrDir, targetDir, nsCall=False, acceptedReturncodes=[0]): 
  ensureDir(targetDir, nsCall=True, acceptedReturncodes=acceptedReturncodes)
  cp(fileOrDir, targetDir, '-pr', nsCall=True)
    
def useForPack(fileOrDir, targetDir, filename=None, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'useForPack(fileOrDir=%s, targetDir=%s, nsCall=%s, acceptedReturncodes=%s)' \
                    % (fileOrDir, targetDir, nsCall, intListToString(acceptedReturncodes) )
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    
    if not targetDir:
      dir = ''
    else:
      dir = targetDir if targetDir[0] != '/' else targetDir[1:len(targetDir)]
    
    dest = '%s%s' % (neoShell.appWorkspacePackage, dir)
    
    ensureDir(dest, nsCall=True, acceptedReturncodes=acceptedReturncodes)
    
    if filename:
      dest = addSlash(dest)
      dest = '%s%s' % (dest, filename)
    
    cp(fileOrDir, dest, '-pr', nsCall=nsCall, acceptedReturncodes=acceptedReturncodes)
    
    
  return __indirectCommand__(callback, commandDetail, nsCall)

def createPackage(nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'createPackage(nsCall=%s, acceptedReturncodes=%s)' % (nsCall, intListToString(acceptedReturncodes) )
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    
    innerPack = 'pack.tar.gz'
    outerPack = neoShell.compressedFile
    savedDir = neoShell.currentDir

    setupScript = neoShell.modulePyFile
    setupScriptFile = setupScript[setupScript.rfind('/') + 1:len(setupScript)]
    
    # Building inner package
    if os.path.exists(neoShell.appWorkspacePackage):
      cd(neoShell.appWorkspacePackage, nsCall=True, acceptedReturncodes=acceptedReturncodes)
      cmd('tar -zcvf %s *' % innerPack, nsCall=True, acceptedReturncodes=acceptedReturncodes)
      cp(innerPack, '..', nsCall=True, acceptedReturncodes=acceptedReturncodes)
    else:
      innerPack = ''
    
    files = ''
    if os.path.exists(neoShell.appWorkspaceFiles):
      files = 'files'
      
    # Building bundle
    ensureDir(neoShell.appWorkspace)
    cd(neoShell.appWorkspace, nsCall=True, acceptedReturncodes=acceptedReturncodes)
    cp(setupScript, '.')
    cmd('tar -zcvf %s %s %s %s' % (outerPack, innerPack, setupScriptFile, files), nsCall=True, acceptedReturncodes=acceptedReturncodes)
    
    cd(savedDir, nsCall=True, acceptedReturncodes=acceptedReturncodes)

  return __indirectCommand__(callback, commandDetail, nsCall)
  
def unpack(nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'unpack(nsCall=%s, acceptedReturncodes=%s)' % (nsCall, intListToString(acceptedReturncodes) )
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    
    savedDir = neoShell.currentDir
    cd(neoShell.appWorkspace)
    ensureDir(neoShell.appWorkspacePackage)
    sudo('tar -zxvf pack.tar.gz -C %s' % neoShell.appWorkspacePackage, nsCall=True, acceptedReturncodes=acceptedReturncodes)

    try:
      outs = []
      listFiles = []
      for root, dirs, files in os.walk(neoShell.appWorkspacePackage):
        for file in files:
          path = '%s%s' % (addSlash(root), file)
          listFiles.append(path)
          to = '/%s' % path.replace(neoShell.appWorkspacePackage, '')
          toDir = os.path.dirname(to)

          ensureDir(toDir)
          sudo("cp '%s' '%s'" % (path, to))

      out = ''.join(outs)      
      err = ''
      ret = 0
      
    except ValueError as e:
      out = ''
      err = 'JSON parsing error - ' + str(e)
      ret = 1
    except Exception as e:
      out = ''
      err = str(e)
      ret = 1 
      
    formattedOutput(commandDetail, out, err, ret, acceptedReturncodes, nsCall)    
        
    cd(savedDir, nsCall=True, acceptedReturncodes=acceptedReturncodes)
    
  return __indirectCommand__(callback, commandDetail, nsCall)

def cleanAll():
  if os.path.exists(neoShell.workspace):
    if neoShell.workspace in neoShell.currentDir:
      cd(neoShell.home, nsCall=True)
    
    rm(neoShell.workspace, '-rf', nsCall=True)
      
#---------------------------------------------------------
# ---- Groups
#---------------------------------------------------------
def getGroup(name, nsCall=False):
  commandDetail = 'getGroup(%s, %s)' % (name, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    
    out, _, ret = cmd("getent group | egrep '^%s:'" % name, True, range(0, 255))
    
    if ret != 0:
      return None
    
    groupName, _, gid, members = stripNewline(out).split(":", 4)
    return Group(groupName, gid, [] if len(members) == 0 else members.split(','))

  return __indirectCommand__(callback, commandDetail, nsCall)

def groupExists(name, nsCall=False):
  commandDetail = 'groupExists(%s, %s)' % (name, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    group = getGroup(name, nsCall)
    
    if group:
      return True
    else:
      return False
  
  return __indirectCommand__(callback, commandDetail, nsCall)
  
def createGroup(name, nsCall=False, acceptedReturncodes=[0]):
  return sudo("groupadd %s" % name, nsCall=nsCall, acceptedReturncodes=acceptedReturncodes)  
  
def ensureGroup(name, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'ensureGroup(%s, %s)' % (name, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    
    group = getGroup(name)
    if not group:
      createGroup(name, nsCall=nsCall, acceptedReturncodes=acceptedReturncodes)

  return __indirectCommand__(callback, commandDetail, nsCall)    
      
def removeGroup(name, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'removeGroup(%s, %s)' % (name, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    
    group = getGroup(name, nsCall=True)
    
    if group:
      userGroup = getUser(name, nsCall=True) # primaryGroup
      
      if not userGroup:
        if len(group.members) > 0:
          for user in group.members:
            removeUserFromGroup(group.name, user, nsCall=True, acceptedReturncodes=acceptedReturncodes)
          
        sudo("groupdel %s" % group.name, nsCall=True, acceptedReturncodes=acceptedReturncodes) 
  
  return __indirectCommand__(callback, commandDetail, nsCall)
  
#---------------------------------------------------------
# ---- Group/User
#---------------------------------------------------------
def addSudoer(newSudoer, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'addSudoer(%s)' % newSudoer
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    out, err, ret = sudo('visudo -c -f %s' % newSudoer, True, range(0, 255))
    
    if ret == 0:
      ensureFile(newSudoer, 'root', 'root', 440)
      out, err, ret = sudo('cp %s /etc/sudoers.d' % newSudoer, nsCall=True, acceptedReturncodes=acceptedReturncodes)
    
    if ret != 0:
      raise NeoShellError(err)
      
  return __indirectCommand__(callback, commandDetail)

def getUserFromGroup(group, user, nsCall=False):
  commandDetail = 'getUserFromGroup(%s, %s, %s)' % (group, user, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    
    groupObj = getGroup(group, nsCall=True)
    
    if not groupObj:
      return None
    else:
      return user in groupObj.members

  return __indirectCommand__(callback, commandDetail, nsCall)    
      
def addUserToGroup(group, user, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'addUserToGroup(%s, %s, %s)' % (group, user, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    
    assert getGroup(group, nsCall=True), "Group does not exist: %s" % (group)

    if not getUserFromGroup(group, user, nsCall=True):
      sudo("usermod -a -G '%s' '%s'" % (group, user), nsCall=True, acceptedReturncodes=acceptedReturncodes)

  return __indirectCommand__(callback, commandDetail, nsCall)
      
def ensureUserInGroup(groupName, user, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'ensureUserInGroup(%s, %s, %s)' % (groupName, user, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    group = getGroup(groupName, nsCall=true)
    
    if group and user not in group.members:
      addUserToGroup(group, user, nsCall=True, acceptedReturncodes=acceptedReturncodes)

  return __indirectCommand__(callback, commandDetail, nsCall)    
      
def removeUserFromGroup(group, user, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'removeUserFromGroup(%s, %s, %s)' % (group, user, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
     
    userFound = getUserFromGroup(group, user, nsCall=True)
    if userFound:
      sudo('gpasswd -d %s %s' % (user, group), nsCall=True)
  
  return __indirectCommand__(callback, commandDetail)
  
#---------------------------------------------------------
# ---- Users
#---------------------------------------------------------
def getCurrentUser(nsCall=False):
  name, _, _ = cmd('id -u -n', nsCall=nsCall)
  return stripNewline(name)

def getUser(name, nsCall=False):
  commandDetail = 'getUser(name=%s, nsCall=%s)' % (name, nsCall)

  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    out, _, ret = cmd("getent passwd | egrep '^%s:'" % name, nsCall=True, acceptedReturncodes=range(0,255))
    
    if ret != 0:
      return None
    else:
      elements = out.split(":")
      return User(elements[0], elements[2], elements[3], elements[4], elements[5], elements[6])

  return __indirectCommand__(callback, commandDetail, nsCall)    
      
def userExists(name=None, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'userExists(%s, %s)' % (name, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    user = getUser(name, nsCall=nsCall)
    
    if user:
      return True
    else:
      return False

  return __indirectCommand__(callback, commandDetail, nsCall)    
      
def createUser(user, fullname=None, home=None, group=None, createHome=False, publicKey=None, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'createUser(user=%s, home=%s, group=%s, createHome=%s, publicKey=%s, nsCall=%s)' % (user, home, group, createHome, publicKey, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    
    command = ['useradd']
    
    if fullname:
      command.append("-c '%s'" % fullname)
    if home:
      command.append("-d '%s'" % home)
    if createHome:
      command.append("-m")
    
    command.append(user)
    
    sudo(' '.join(command), nsCall=True, acceptedReturncodes=acceptedReturncodes)
    
    if publicKey:
      addAuthorizedKey(user, publicKey, nsCall=True, acceptedReturncodes=acceptedReturncodes)

    if group:
      addUserToGroup(group, user, nsCall=True)

  return __indirectCommand__(callback, commandDetail, nsCall)
  
def addAuthorizedKey(username, publicKey, nsCall=True, acceptedReturncodes=[0]):
  commandDetail = 'addAuthorizedKey(username=%s, publicKey=%s, nsCall=%s)' % (username, publicKey, nsCall)
  
  def callback():
    user = getUser(username, nsCall=False)
    home = addSlash(user.home)
    ssh = '%s.ssh' % home
    authorized_keys = '%s/authorized_keys' % ssh
    
    ensureDir(ssh, username, username, 700, nsCall=True, acceptedReturncodes=acceptedReturncodes)
    sudo("sh -c \"echo '%s' >> %s\"" % (publicKey, authorized_keys))
    ensureFile(authorized_keys, username, username, 600, nsCall=True, acceptedReturncodes=acceptedReturncodes)
  
  return __indirectCommand__(callback, commandDetail, nsCall)
    
def ensureUser(username, fullname=None, home=None, group=None, createHome=False, publicKey=None, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'ensureUser(username=%s, home=%s, group=%s, createHome=%s, publicKey=%s, nsCall=%s)' % (username, home, group, createHome, publicKey, nsCall)
  
  def callback():
    user = getUser(username, True)

    if not user:
      createUser(username, fullname, home, group, createHome, publicKey, nsCall, acceptedReturncodes)
      user = getUser(username, True)
  
    if publicKey:
      homeTmp = addSlash(user.home)
      authorized_keys = '%s.ssh/authorized_keys' % homeTmp
      
      ensureDir(os.path.dirname(authorized_keys))
      
      if not os.path.exists(authorized_keys):
        sudo('touch %s' % authorized_keys, nsCall=True)
      
      data, _, _ = sudo('cat %s' % authorized_keys)
      #with open(authorized_keys, 'r') as file:
      #  data = file.read()
         
      if publicKey not in data:
        addAuthorizedKey(user.name, publicKey, nsCall=True, acceptedReturncodes=acceptedReturncodes)
  
  return __indirectCommand__(callback, commandDetail, nsCall)

def ensureUsers(usersConfigPath, nsCall=False, acceptedReturncodes=[0]): 
  commandDetail = 'ensureUsers(usersConfigPath=%s, nsCall=%s)' % (usersConfigPath, nsCall)
  
  def callback():
    tree = ET.parse(usersConfigPath)
  
    root = tree.getroot()
    usersObj = root.findall('./user')
    
    for userObj in usersObj:
      username = userObj.find('username').text
      fullname = userObj.find('fullname').text
      publicKey = userObj.find('publickey').text
      
      ensureUser(username, fullname=fullname, group=username, createHome=True, publicKey=publicKey)

  return __indirectCommand__(callback, commandDetail, nsCall)
  
def removeUser(user, rmHome=None, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'removeUser(%s, %s, %s)' % (user, rmHome, nsCall)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    command = ['userdel -f']

    if rmHome:
      command.append("-r")
    
    command.append(user)
    
    sudo(' '.join(command), nsCall=nsCall, acceptedReturncodes=acceptedReturncodes)
  
  return __indirectCommand__(callback, commandDetail, nsCall)

#---------------------------------------------------------
# ---- Service
#---------------------------------------------------------
class ServiceStatus:
  RUNNING, UNRECOGNIZED, STOPPED, UNKNOWN = range(0, 4)

def getServiceStatus(name, nsCall=False):  
  commandDetail = 'getServiceStatus(%s)' % name
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    
    _, _, ret = rsudo('service %s status' % name, nsCall=True, acceptedReturncodes=range(0, 255))
    
    if ret == 0:
      return ServiceStatus.RUNNING
    elif ret == 1:  
      return ServiceStatus.UNRECOGNIZED
    elif ret == 3:  
      return ServiceStatus.STOPPED
    else:  
      return ServiceStatus.UNKNOWN
      
  return __indirectCommand__(callback, commandDetail, nsCall)
  
def ensureServiceStarted(name, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'ensureServiceStarted(%s)' % name
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    serviceStatus = getServiceStatus(name, nsCall=nsCall)
    
    if serviceStatus == ServiceStatus.UNRECOGNIZED:
      raise("This service doesn't exist: %s" % name)
    elif serviceStatus == ServiceStatus.STOPPED:
      rsudo('service %s start' % name, nsCall=True, acceptedReturncodes=acceptedReturncodes)
      waitingService(name, ServiceStatus.RUNNING)
    elif serviceStatus != ServiceStatus.RUNNING:
      raise("This service is in an unstable state: %s" % name)

  return __indirectCommand__(callback, commandDetail, nsCall)

def ensureServiceStopped(name, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'ensureServiceStopped(%s)' % name
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    serviceStatus = getServiceStatus(name, nsCall=nsCall)
    
    if serviceStatus == ServiceStatus.UNRECOGNIZED:
      raise("This service doesn't exist: %s" % name)
    elif serviceStatus == ServiceStatus.RUNNING:
      rsudo('service %s stop' % name, nsCall=True, acceptedReturncodes=acceptedReturncodes)
      waitingService(name, ServiceStatus.STOPPED)
    elif serviceStatus != ServiceStatus.STOPPED:
      raise("This service is in an unstable state: %s" % name)

  return __indirectCommand__(callback, commandDetail, nsCall)

def serviceStart(name, nsCall=False, acceptedReturncodes=[0]):
  commandDetail = 'serviceStart(%s)' % name
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    serviceStatus = getServiceStatus(name)
    
    if serviceStatus == ServiceStatus.UNRECOGNIZED:
      raise("This service doesn't exist: %s" % name)
    elif serviceStatus == ServiceStatus.RUNNING:
      rsudo('service %s restart' % name, nsCall=True, acceptedReturncodes=acceptedReturncodes)
      waitingService(name, ServiceStatus.RUNNING)
    elif serviceStatus == ServiceStatus.STOPPED:
      rsudo('service %s start' % name, nsCall=True, acceptedReturncodes=acceptedReturncodes)
      waitingService(name, ServiceStatus.RUNNING)
    else:
      raise("This service is in an unstable state: %s" % name)

  return __indirectCommand__(callback, commandDetail, nsCall)

def waitingService(name, status, nsCall=False, acceptedReturncodes=[0]):
  ok = False
  for i in range(0, 15):
    if status == getServiceStatus(name, nsCall=True):
      ok = True
      break
    else:
      time.sleep(1)
  
  if not ok:
    raise NeoShellError('Wrong status %s for service %s' % (name, status))
    
#---------------------------------------------------------
# ---- Remote
#---------------------------------------------------------
def deploy(user, host, privateKey, appTarGz, workspace, installArgs=[], nsCall=False): # to call after execute (for forge for example)
  commandDetail = 'deploy(%s, %s, %s, %s, %s)' % (user, host, privateKey, appTarGz, workspace)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    
    sshUserHost = '%s@%s' % (user, host)
    values = (privateKey, appTarGz, sshUserHost)
    cmd('scp -i %s -oStrictHostKeyChecking=no %s %s:.' % values, nsCall=True)
    
    shortAppTarGz = appTarGz[appTarGz.rfind('/') + 1:len(appTarGz)]
    cliParams = CliParams('', 'deploy', sshUserHost=sshUserHost, sshPrivateKey=privateKey, appTarGz=shortAppTarGz, workspace=workspace, installArgs=installArgs)
    doDeploy(cliParams)
  
  return __indirectCommand__(callback, commandDetail, nsCall)
  
def install(appData, installArgs=[], script=''):
  appName(appData.name)
  version(appData.version)
  env(appData.env)
  neoShell.installArgs = installArgs
  
  neoShell.buildPaths()

  savedDir = neoShell.currentDir
  cd(neoShell.home, nsCall=True)
  
  if not appData.local:
    cmd('wget %s' % appData.path, nsCall=True)
    file = appData.filename
  else:
    file = appData.path
  
  ensureDir(neoShell.appWorkspace, nsCall=True)
  cmd('tar -zxvf %s -C %s' % (file, neoShell.appWorkspace), nsCall=True)
  
  if not neoShell.dryRun:
    pyFile = getSinglePyFile(neoShell.appWorkspace)
  else:
    pyFile = script

  scriptModuleName, scriptModule = importScript(pyFile)
  cd(savedDir, nsCall=True)
  scriptModule.install()

def executeScript(script, executeArgs=[], nsCall=False):
  return buildPackage(script, executeArgs=executeArgs, nsCall=nsCall)
  
def buildPackage(script, moveTo=None, executeArgs=[], nsCall=False):
  commandDetail = 'buildPackage(script=%s, moveTo=%s)' % (script, moveTo)
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)
    
    neoShell.saveContext()
    neoShell.executeArgs = executeArgs
    neoShell.dontRebuildWorkspace = True
    
    doExecute(script)
    
    if moveTo:
      ensureDir(moveTo)
      cp('%s%s' % (neoShell.appWorkspace, neoShell.compressedFile), moveTo)
    
    neoShell.dontRebuildWorkspace = False
    neoShell.restoreContext() 
  
  return __indirectCommand__(callback, commandDetail, nsCall)
  
# appname = 'myapp.10-int'
def installPackage(appname, installArgs=[], nsCall=False):
  commandDetail = 'installPackage(%s)' % appname
  
  def callback():
    formattedOutput(commandDetail, msgType=MsgType.EXT_CMD)

    if appname.count('/') == 0 and not neoShell.binaryRepo:
      raise NeoShellError('The package %s can\'t be installed, no repo has been set.' % appname)

    if appname.count('/') > 0:
      appData = getAppData(appname)
    else:  
      appData = getAppData('%s.tar.gz' % appname)
      appData.local = False
      appData.path = '%s%s' % (addSlash(neoShell.binaryRepo), appData.path)

    neoShell.saveContext()
    install(appData, installArgs)
    neoShell.restoreContext()  
  
  return __indirectCommand__(callback, commandDetail, nsCall)

def installNeoShellToRemote(privateKey, sshUserHost):
  thisPyFile = getPyFile(__file__)
  values = (privateKey, thisPyFile, sshUserHost)
  rcmd('scp -i %s -oStrictHostKeyChecking=no %s %s:.' % values, nsCall=True)
  
  values = (privateKey, sshUserHost)
  command = "ssh -t -t -i %s -oStrictHostKeyChecking=no %s 'sudo yum install -y python27;sudo mv neoshell.py /usr/local/bin;sudo chmod +x /usr/local/bin/neoshell.py'" % values
  rcmd(command, True)

def executeNeoShellOnRemote(privateKey, sshUserHost, path, workspace, installArgs): # neoshell.py install http://forge/raw/myapp.10-int.tar.gz <workspace>
  if len(installArgs) > 0:
    values = (privateKey, sshUserHost, path, workspace, ' '.join(installArgs))
    command = "ssh -t -t -i %s -oStrictHostKeyChecking=no %s 'neoshell.py install %s %s -i %s'" % values
  else:
    values = (privateKey, sshUserHost, path, workspace)
    command = "ssh -t -t -i %s -oStrictHostKeyChecking=no %s 'neoshell.py install %s %s'" % values
    
  rcmd(command, True)

#----------------------------------------------------------------------------------------------------------------------
# Work
#----------------------------------------------------------------------------------------------------------------------
  
def doDryRun(cliParams):
  neoShell.dryRun = True
  scriptModuleName, scriptModule = importScript(cliParams.script)

  if hasattr(scriptModule, 'execute'):
    stdout('------------------- execute() -------------------')
    scriptModule.execute()
    
  if hasattr(scriptModule, 'install'):
    stdout('------------------- install() -------------------')
    cliParams.appTarGz = 'dryRun-999.tar.gz'
    cliParams.workspace = '/ns.dryrun/'
    neoShell.saveContext()
    doInstall(cliParams)
    neoShell.restoreContext()
    
def doExecute(script):
  scriptModuleName, scriptModule = importScript(script)
  
  if hasattr(scriptModule, 'execute'):
    ensureEnvVar('HOME', notBlank=True)
    scriptModule.execute()

def doInstall(cliParams):
  appData = getAppData(cliParams.appTarGz)
  workspace(cliParams.workspace)
  install(appData, installArgs=cliParams.installArgs, script=cliParams.script)

def doDeploy(cliParams):
  installNeoShellToRemote(cliParams.sshPrivateKey, cliParams.sshUserHost)
  executeNeoShellOnRemote(cliParams.sshPrivateKey, cliParams.sshUserHost, cliParams.appTarGz, cliParams.workspace, cliParams.installArgs)

def start():
  startTime = time.time()
  
  cliParams = None
  returncode = 0
  finalMessage = ''
  operation = ''
  
  try:
    cliParams = getParams()
    
    neoShell.executeArgs = cliParams.executeArgs
    neoShell.installArgs = cliParams.installArgs
    
    if cliParams.operation == 'execute' or cliParams.operation == 'dryrun':
      decorateStart()
    
    if cliParams.operation == 'execute':
      doExecute(cliParams.script)  
    elif cliParams.operation == 'deploy':
      doDeploy(cliParams)
    elif cliParams.operation == 'install':
      doInstall(cliParams)
    elif cliParams.operation == 'dryrun':
      doDryRun(cliParams)
  except NeoShellError as e:
    returncode = 1
    finalMessage = str(e.value)
  except Exception as e:
    returncode = 1
    finalMessage = 'Don\'t panic but this is serious!\n%s' % traceback.format_exc()

  msgType = MsgType.SUCCESS if returncode == 0  else MsgType.FAILURE
  formattedOutput('DONE %s' % finalMessage, msgType=msgType)
  
  elapsedTime = time.time() - startTime
  
  if cliParams and (cliParams.operation == 'execute' or cliParams.operation == 'dryrun'):
    decorateEnd(elapsedTime)
  
  return returncode
    
def decorateStart():
  values = (neoShell.appName, neoShell.version)
  stdout('+===================================================================================+')
  stdout('|                                                                                   |')
  stdout('| Starting execution of script with Name: %s in Version: %s' % values)
  stdout('|                                                                                   |')
  stdout('+===================================================================================+')
    
def decorateEnd(elapsedTime): 
  values = (neoShell.appName, neoShell.version, elapsedTime)
  stdout('+===================================================================================+')
  stdout('|                                                                                   |')
  stdout('| Script execution with Name: %s for Version: %s ended in %.2f seconds' % values)
  stdout('|                                                                                   |')
  stdout('+===================================================================================+')

def changeWriter(writer):
  sys.stdout = writer

def restoreStdOut():
  sys.stdout = neoShell.originalStdOut

if __name__ == "__main__":
  __builtin__.neoShell = NeoShell()
  sys.stdout = Writer(sys.stdout)     
  returncode = start()
  sys.exit(returncode) 