import imp, kissutils, sys, unittest, __builtin__
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import DevNull, changeWriter, restoreStdOut
from neoshell import NeoShell, addSlash, cd, cmd, cp, ensureDir, getFileDir, mkdir, start, rm

class ScriptsTest(unittest.TestCase):
  targetDir = ''
  
  def setUp(self):
    __builtin__.neoShell = NeoShell()
    changeWriter(DevNull())
    #restoreStdOut()
    
    self.thisDir = getFileDir(__file__)
    cd(self.thisDir)
    cd('..')
    self.scriptsDir = addSlash(neoShell.currentDir)
    cd('../..') # go outside kiss-forge folder, otherwise git commands will be mixed up
    
    # ---- Create a bunch of folders
    self.rootDir = addSlash(neoShell.currentDir) 
    self.targetDir = '%sforgeTest/' % self.rootDir
    ensureDir(self.targetDir, 'root', 'root', 777)

    self.reposDir = '%srepos/' % self.targetDir
    ensureDir(self.reposDir, 'root', 'root', 777)
    
    self.reposAppDir = '%sapp/' % self.reposDir
    ensureDir(self.reposAppDir, 'root', 'root', 777)
    
    self.reposDevopsDir = '%sdevops/' % self.reposDir
    ensureDir(self.reposDevopsDir, 'root', 'root', 777)
    
    self.appDir = '%sapp/' % self.targetDir
    self.devopsDir = '%sdevops/' % self.targetDir
    
    self.forgeDir = '%sforge/' % self.targetDir
    ensureDir(self.forgeDir, 'root', 'root', 777)
    
    self.forgeScriptsDir = '%sscripts/' % self.forgeDir
    ensureDir(self.forgeScriptsDir, 'root', 'root', 777)

    # ---- Create 2 git repos
    cd(self.reposAppDir)
    cmd('git init --bare')
    
    cd(self.reposDevopsDir)
    cmd('git init --bare')
    
    # ---- Clone the 2 repos and add things inside
    cd(self.targetDir)
    cmd('git clone %s app' % self.reposAppDir)
    cd(self.appDir)
    cp('%stest/demoapp/*' % self.scriptsDir, self.appDir, args='-r') # demo application in java
    cmd('git add -A')
    cmd('git commit -m "Test"')
    cmd('git push origin master')
    
    cd(self.targetDir)
    cmd('git clone %s devops' % self.reposDevopsDir)
    cd(self.devopsDir)
    cmd("echo '0' > VERSION")
    cmd("echo '0' > LATESTBUILD")
    cmd('git add -A')
    cmd('git commit -m "Test"')
    cmd('git push origin master')
   
  def tearDown(self):
    rm(self.targetDir, args='-rf')
    
  def testCreateBranch(self):
    cp('%screateBranch.py' % self.scriptsDir, self.forgeScriptsDir)
    sys.argv = ['neoshell.py', '%screateBranch.py' % self.forgeScriptsDir, 'execute', '-e', 'forge_', 'master', 'pom.xml']
    start()
    
    assert '1.0' == kissutils.getFileContent('%sVERSION' % self.devopsDir)
    assert '1' == kissutils.getFileContent('%sLATESTBUILD' % self.devopsDir)
    assert '1.0.1' == kissutils.getFileContent('%sBUILDVERSION' % self.devopsDir)
    
    # ----- In devops
    cd(self.devopsDir)
    _, err, _ = cmd('git checkout master')
    assert "Already on 'master'" in err
    
    _, _, ret = cmd('git checkout forge_1.0.1')
    assert ret == 0
    
    out, _, _ = cmd('git branch -r')
    assert 'origin/forge_1.0.1' in out
    
    # ----- In app
    cd(self.appDir)
    _, err, _ = cmd('git checkout master')
    assert "Already on 'master'" in err
    
    _, _, ret = cmd('git checkout forge_1.0.1')
    assert ret == 0
    
    out, _, _ = cmd('git branch -r')
    assert 'origin/forge_1.0.1' in out


  def testSwitchBranch(self):
    cp('%screateBranch.py' % self.scriptsDir, self.forgeScriptsDir)
    sys.argv = ['neoshell.py', '%screateBranch.py' % self.forgeScriptsDir, 'execute', '-e', 'forge_', 'master', 'pom.xml']
    start()
    
    cp('%sswitchBranch.py' % self.scriptsDir, self.forgeScriptsDir)
    sys.argv = ['neoshell.py', '%sswitchBranch.py' % self.forgeScriptsDir, 'execute', '-e', 'forge_']
    start()

    # ----- In devops
    cd(self.devopsDir)
    _, err, _ = cmd('git checkout forge_1.0.1')
    assert "Already on 'forge_1.0.1'" in err
    
    # ----- In app
    cd(self.appDir)
    _, err, _ = cmd('git checkout forge_1.0.1')
    assert "Already on 'forge_1.0.1'" in err
    
  def testCreateTag(self):
    cp('%screateBranch.py' % self.scriptsDir, self.forgeScriptsDir)
    sys.argv = ['neoshell.py', '%screateBranch.py' % self.forgeScriptsDir, 'execute', '-e', 'forge_', 'master', 'pom.xml']
    start()
    
    cp('%screateTag.py' % self.scriptsDir, self.forgeScriptsDir)
    sys.argv = ['neoshell.py', '%screateTag.py' % self.forgeScriptsDir, 'execute', '-e', 'forge_', 'tag_forge_']
    start()

    # ----- In devops
    cd(self.devopsDir)
    _, err, _ = cmd('git checkout forge_1.0.1')
    assert "Already on 'forge_1.0.1'" in err
    
    out, _, _ = cmd('git ls-remote --tags origin')
    assert 'refs/tags/tag_forge_1.0.1' in out
    
    # ----- In app
    cd(self.appDir)
    _, err, _ = cmd('git checkout forge_1.0.1')
    assert "Already on 'forge_1.0.1'" in err  
    
    out, _, _ = cmd('git ls-remote --tags origin')
    assert 'refs/tags/tag_forge_1.0.1' in out

  def testRemoveBranch(self):
    cp('%screateBranch.py' % self.scriptsDir, self.forgeScriptsDir)
    sys.argv = ['neoshell.py', '%screateBranch.py' % self.forgeScriptsDir, 'execute', '-e', 'forge_', 'master', 'pom.xml']
    start()
    
    cp('%sremoveBranch.py' % self.scriptsDir, self.forgeScriptsDir)
    sys.argv = ['neoshell.py', '%sremoveBranch.py' % self.forgeScriptsDir, 'execute', '-e', 'forge_', 'master']
    start()

    # ----- In devops
    cd(self.devopsDir)
    out, _, _ = cmd('git branch -r')
    assert "origin/forge_1.0.1" not in out
    
    # ----- In app
    cd(self.appDir)
    out, _, _ = cmd('git branch -r')
    assert "origin/forge_1.0.1" not in out
   
if __name__ == "__main__":
  __builtin__.neoShell = NeoShell()
  unittest.main()