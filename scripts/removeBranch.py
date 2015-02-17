import imp, kissutils
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import cmd, addSlash, buildPaths, getScriptDir, cd, ensureParams

def execute():
  ensureParams(neoShell.executeArgs, 2, 'Usage: removeBranch.py execute -e <branch start name> <master branch>')
  
  buildPaths()
  cd(getScriptDir()) # forge/scripts
  
  branchStartName = neoShell.executeArgs[0] #'forge_'
  masterBranchName = neoShell.executeArgs[1] #'yohan'

  # ---- In devops - Get the current build version
  cd('../../devops')
  cmd('git checkout %s' % masterBranchName)
  buildVersion = kissutils.getFileContent('%sBUILDVERSION' % addSlash(neoShell.currentDir))
  branchName = '%s%s' % (branchStartName, buildVersion)

  # Remove the branch
  removeBranch(branchName)
  
  # ---- In app
  cd('../app')
  
  # Remove the branch
  removeBranch(branchName)
  
def removeBranch(branchName):
  _, _, ret = cmd('git checkout master', acceptedReturncodes=range(0, 255))
  
  if ret == 0:
    cmd('git push origin :%s' % branchName, acceptedReturncodes=range(0, 255))
    