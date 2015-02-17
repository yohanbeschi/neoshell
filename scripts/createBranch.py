import imp, maven, kissutils
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import cmd, addSlash, buildPaths, getScriptDir, echo, cd, callback, ensureParams

def execute():
  ensureParams(neoShell.executeArgs, 3, 'Usage: createBranch.py execute -e <branch start name> <master branch> <pom file in app>')
  
  buildPaths()
  cd(getScriptDir()) # forge/scripts
  
  branchStartName = neoShell.executeArgs[0] #'forge_'
  masterBranchName = neoShell.executeArgs[1] #'yohan'
  pomXml = neoShell.executeArgs[2]
  
  devops = 'devops' #'kiss-bus-devops'
  app = 'app' #'kiss-bus'

  # ---- In devops repository get the files VERSION and LATESTBUILD and get there content
  cd('../../devops')
  
  version = callback(kissutils.callbackGetFileContent('%sVERSION' % addSlash(neoShell.currentDir)))
  latestBuild = callback(kissutils.callbackGetFileContent('%sLATESTBUILD' % addSlash(neoShell.currentDir)))

  # ---- In app repository get the version inside a pom.xml
  cd('../%s' % app)
  absolutePomXml = '%s%s' % (addSlash(neoShell.currentDir), pomXml)

  if neoShell.dryRun:
    callback(callbackUpdateVersionAndLatestBuild(absolutePomXml, version, latestBuild))
    version, latestBuild = '1', '1'
  else:
    version, latestBuild = callback(callbackUpdateVersionAndLatestBuild(absolutePomXml, version, latestBuild))
  
  finalVersion = '%s.%s' % (version, latestBuild)
  branchName = '%s%s' % (branchStartName, finalVersion)
  
  # ---- In app - Create a branch version and push it
  createBranch(branchName)
  
  # ---- In devops
  cd('../%s' % devops)
  # Write all version files 
  # Be aware that BUILDVERSION is in .gitignore. It is used as an artefact by Go to avoid any version collision
  # even if the CI pipeline should be in locked mode (no pipeline should start before the previous one ends successfully)
  # which means one and only one pipeline should use the devops repository of the current application
  # (the CI pipeline linked to the application and using this script)
  cmd('git pull')
  
  callback(kissutils.callbackOverwrite('%sVERSION' % addSlash(neoShell.currentDir), version))
  callback(kissutils.callbackOverwrite('%sLATESTBUILD' % addSlash(neoShell.currentDir), latestBuild))
  callback(kissutils.callbackOverwrite('%sBUILDVERSION' % addSlash(neoShell.currentDir), finalVersion))

  # Push current branch
  cmd('git commit -am "Preparing for new Tag"')
  cmd('git push origin %s' % masterBranchName)
  
  # Create a branch version and push it
  createBranch(branchName)

def createBranch(branchName):
  cmd('git checkout -b %s' % branchName)
  cmd('git push origin %s' % branchName)

def callbackUpdateVersionAndLatestBuild(absolutePomXml, version, latestBuildAsParam):
  def updateVersionAndLatestBuild():
    mavenPom = maven.MavenPom(absolutePomXml)
  
    # Remove -SNAPSHOT if any
    pomVersionCleaned = mavenPom.getVersion().replace('-SNAPSHOT', '')
    
    # Compute the version.build number (finalVersion)
    if pomVersionCleaned != version:
      version_ = pomVersionCleaned
      latestBuild = '1'
    else:
      version_ = version
      latestBuild = int(latestBuildAsParam) + 1  # Add 1 to latestBuild
      latestBuild = str(latestBuild)
      
    return version_, latestBuild
  
  return updateVersionAndLatestBuild