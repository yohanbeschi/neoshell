import imp, kissutils
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import cmd, addSlash, buildPaths, getScriptDir, echo, cd, ensureParams

def execute():
  ensureParams(neoShell.executeArgs, 1, 'Usage: switchBranch.py execute -e <branch start name>')
  
  buildPaths()
  cd(getScriptDir()) # forge/scripts
  
  branchStartName = neoShell.executeArgs[0] #'forge_'

  # ---- In devops - Get the current build version
  cd('../../devops')
  buildVersion = kissutils.getFileContent('%sBUILDVERSION' % addSlash(neoShell.currentDir))
  branchName = '%s%s' % (branchStartName, buildVersion)
  
  # Checkout the branch linked to the current build version
  switchBranch(branchName)
  
  # ---- In app
  cd('../app')
  switchBranch(branchName)
  
def switchBranch(branchName):
  cmd('git checkout %s' % branchName)