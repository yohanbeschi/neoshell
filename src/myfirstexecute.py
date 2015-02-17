#!/usr/local/bin/neoshell.py
# -*- coding: utf-8 -*-
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, env, buildPaths, getScriptDir, addSlash, workspace, cleanAll
from neoshell import cd, cmd, createPackage, ensureDir, useForPack, useFile, unpack, ensureFile

def execute():
  # R�cup�re le r�pertoire d'ex�cution du script
  scriptDir = getScriptDir()
  
  # Va dans ce r�petoire
  cd(scriptDir)

  # En partant du r�pertoire 'neoShell.currentDir' faisant suite au 'cd' pr�c�dent
  # nous cr�er un chemin vers un r�pertoire target.
  # Si notre script est dans le r�pertoire /home/yohan, nous obtenons le chemin /home/yohan/target
  # Attention � ne pas confondre 'neoshell' le nom du module et 'neoShell' l'objet de type NeoShell
  targetDir = '%starget/' % addSlash(neoShell.currentDir)
  
  # Nous cr�eons le r�pertoire 'target' s'il n'existe pas
  # Notons que la fonction 'ensureDir()' permet de cr�er l'ensemble des r�pertoires du chemin pass� en param�tre s'ils n'existent pas.
  # Le r�pertoire cr�er ont pour 'user' et 'group', l'utilisateur courant et son groupe
  ensureDir(targetDir)
  
  # Nous d�finissons le r�pertoire target comme notre espace de travail
  workspace(targetDir)
  
  # Information sur le package � cr�er
  appName('demo')
  version('1.0')
  env('noenv')
  
  # Valorisation de variables :
  # neoShell.home = <variable d'environnement HOME>
  # neoShell.compressedFile = <appName>-<version>-<env>.tar.gz
  # neoShell.workspace = d�finit avec workspace, sinon <neoShell.home>/<workspaceName>
  #                      'workspaceName' peut �tre d�finit � l'aide la fonction workspaceName()
  #                      sinon par d�faut : 'ns.workspace'
  # neoShell.appWorkspace = <neoShell.workspace>/<appName>/<version>/<env>
  # neoShell.appWorkspaceFiles = <neoShell.appWorkspace>/files
  # neoShell.appWorkspaceTmp = <neoShell.appWorkspace>/tmp
  # neoShell.appWorkspacePackage = <neoShell.appWorkspace>/package
  buildPaths()
  
  # Cr�e le r�pertoire 'tmp' dans s'il n'existe pas
  ensureDir(neoShell.appWorkspaceTmp)
  # Va dans ce r�pertoire
  cd(neoShell.appWorkspaceTmp)
  # Cr�e un fichier nomm� 'hello'
  # La fonction 'cmd' permet d'ex�cuter n'importe quelle commande, comme si nous �tions dans un shell
  cmd('echo "Hello World" > hello')

  # D�place ce fichier dans le r�pertoire 'package'.
  #   Nous indiquons uniquement le nom du fichier puisque nous nous trouvons dans le r�pertoire dans
  #   lequel il se trouve. Dans le cas contraire il aurait fallu indiquer son chemin absolu
  # Le second param�tre est le chemin du fichier sur le serveur cible, dans le cas pr�sent '/tmp/demo'
  #   Attention il ne faut pas mettre de slash ('/') devant 'tmp'
  useForPack('hello', 'tmp/demo')
  
  # D�place le fichier 'hello' dans le r�pertoire 'files'
  useFile('hello')
  
  # La m�thode suivante effectue plusieurs actions:
  #   Cr�e une archive nomm� 'pack.tar.gz' et contenant le contenu du r�pertoire 'package'
  #     De fait, la commande 'tar -zxvf pack.tar.gz -C /' d�zippe l'ensemble des fichiers et r�pertoire de l'archive � partir du noeud root ('/')
  #   Cr�e une archive ayant pour nom 'neoShell.compressedFile' contenant : 
  #     - l'archive 'pack.tag.gz' pr�c�demment cr��e
  #     - le r�pertoire 'files' s'il est pr�sent
  #     - ce script qui indique comment doit �tre install� le package � l'aide la fonction 'install()'
  createPackage()
 
  # Suppression du workspace
  # cleanAll()
  
def install():
  # D�zippe l'archive 'pack.tar.gz'
  #  Notons que si les r�pertoires existent aucune action est effectu�e sinon ils sont cr��s, en revanche les fichiers existants sont �cras�s.
  #  Si un fichier est pr�sent dans un r�pertoire mais pas pr�sent dans l'archive, il est conserv�
  unpack()
  
  # Change les droits du r�pertoire '/tmp/demo'
  ensureDir('/tmp/demo', 'root', 'root', 755) # pour changer les droits r�cusivement il y a un param�tre optionnel : 'recursive=True'
  
  # Change les droits du fichier 'hello'
  ensureFile('/tmp/demo/hello', 'root', 'root', 600)