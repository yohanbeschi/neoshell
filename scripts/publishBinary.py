import imp, kissutils, os
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import rcmd, sudo, ensureParams, getAppData, ensureDir, echo, ensureEnvVar

def execute():
  ensureParams(neoShell.executeArgs, 1, 'Usage: publishBinary.py execute -e <artifact absolute path>')
  artifactPath = neoShell.executeArgs[0]
  appData = getAppData(artifactPath)
  targetPath = '/var/www/html/packages/%s' % appData.name
  
  ensureEnvVar('FORGE_pemFile')
  ensureEnvVar('FORGE_user')
  ensureEnvVar('FORGE_host')

  privateKey = os.environ['FORGE_pemFile']
  user = os.environ['FORGE_user']
  host = os.environ['FORGE_host']
  
  sshUserHost = '%s@%s' % (user, host)
  values = (privateKey, artifactPath, sshUserHost)
  # Remote copy
  echo('Copying artifact to remote')
  rcmd('scp -i %s -oStrictHostKeyChecking=no %s %s:.' % values, nsCall=False)
  echo('Artifact copied to remote')
  # Move copied file to targetPath
  appTarGZ = artifactPath[artifactPath.rfind('/')+1:len(artifactPath)]
  values = (privateKey, sshUserHost, targetPath, appTarGZ, targetPath, targetPath)
  command = "ssh -t -t -i %s -oStrictHostKeyChecking=no %s 'sudo mkdir -pv %s;sudo mv %s %s;sudo chown -R go:go %s'" % values  
  echo('Moving artifact to binary repo')
  rcmd(command, False)
  echo('Artifact moved to binary repo')