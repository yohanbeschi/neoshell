import imp, kissutils
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import cmd, addSlash, buildPaths, getScriptDir, cd, ensureParams

def execute():
  ensureParams(neoShell.executeArgs, 2, 'Usage: createTag.py execute -e <branch start name> <tag start name>')
  
  buildPaths()
  cd(getScriptDir()) # forge/scripts
  
  branchStartName = neoShell.executeArgs[0] #'forge_'
  tagStartName = neoShell.executeArgs[1] #'tag_forge_'
  
  # ---- In devops - Get the current build version
  cd('../../devops')
  buildVersion = kissutils.getFileContent('%sBUILDVERSION' % addSlash(neoShell.currentDir))
  branchName = '%s%s' % (branchStartName, buildVersion)
  tagName = '%s%s' % (tagStartName , buildVersion)
  
  # Checkout the branch linked to the current build version
  createTag(branchName, tagName)
  
  # ---- In app
  cd('../app')
  createTag(branchName, tagName)
  
def createTag(branchName, tagName):
  cmd('git checkout %s' % branchName)
  cmd('git tag %s' % tagName)
  cmd('git push origin %s' % tagName)