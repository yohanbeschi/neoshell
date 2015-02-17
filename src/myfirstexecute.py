#!/usr/local/bin/neoshell.py
# -*- coding: utf-8 -*-
import imp
imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
from neoshell import appName, version, env, buildPaths, getScriptDir, addSlash, workspace, cleanAll
from neoshell import cd, cmd, createPackage, ensureDir, useForPack, useFile, unpack, ensureFile

def execute():
  # Récupère le répertoire d'exécution du script
  scriptDir = getScriptDir()
  
  # Va dans ce répetoire
  cd(scriptDir)

  # En partant du répertoire 'neoShell.currentDir' faisant suite au 'cd' précédent
  # nous créer un chemin vers un répertoire target.
  # Si notre script est dans le répertoire /home/yohan, nous obtenons le chemin /home/yohan/target
  # Attention à ne pas confondre 'neoshell' le nom du module et 'neoShell' l'objet de type NeoShell
  targetDir = '%starget/' % addSlash(neoShell.currentDir)
  
  # Nous créeons le répertoire 'target' s'il n'existe pas
  # Notons que la fonction 'ensureDir()' permet de créer l'ensemble des répertoires du chemin passé en paramètre s'ils n'existent pas.
  # Le répertoire créer ont pour 'user' et 'group', l'utilisateur courant et son groupe
  ensureDir(targetDir)
  
  # Nous définissons le répertoire target comme notre espace de travail
  workspace(targetDir)
  
  # Information sur le package à créer
  appName('demo')
  version('1.0')
  env('noenv')
  
  # Valorisation de variables :
  # neoShell.home = <variable d'environnement HOME>
  # neoShell.compressedFile = <appName>-<version>-<env>.tar.gz
  # neoShell.workspace = définit avec workspace, sinon <neoShell.home>/<workspaceName>
  #                      'workspaceName' peut être définit à l'aide la fonction workspaceName()
  #                      sinon par défaut : 'ns.workspace'
  # neoShell.appWorkspace = <neoShell.workspace>/<appName>/<version>/<env>
  # neoShell.appWorkspaceFiles = <neoShell.appWorkspace>/files
  # neoShell.appWorkspaceTmp = <neoShell.appWorkspace>/tmp
  # neoShell.appWorkspacePackage = <neoShell.appWorkspace>/package
  buildPaths()
  
  # Crée le répertoire 'tmp' dans s'il n'existe pas
  ensureDir(neoShell.appWorkspaceTmp)
  # Va dans ce répertoire
  cd(neoShell.appWorkspaceTmp)
  # Crée un fichier nommé 'hello'
  # La fonction 'cmd' permet d'exécuter n'importe quelle commande, comme si nous étions dans un shell
  cmd('echo "Hello World" > hello')

  # Déplace ce fichier dans le répertoire 'package'.
  #   Nous indiquons uniquement le nom du fichier puisque nous nous trouvons dans le répertoire dans
  #   lequel il se trouve. Dans le cas contraire il aurait fallu indiquer son chemin absolu
  # Le second paramètre est le chemin du fichier sur le serveur cible, dans le cas présent '/tmp/demo'
  #   Attention il ne faut pas mettre de slash ('/') devant 'tmp'
  useForPack('hello', 'tmp/demo')
  
  # Déplace le fichier 'hello' dans le répertoire 'files'
  useFile('hello')
  
  # La méthode suivante effectue plusieurs actions:
  #   Crée une archive nommé 'pack.tar.gz' et contenant le contenu du répertoire 'package'
  #     De fait, la commande 'tar -zxvf pack.tar.gz -C /' dézippe l'ensemble des fichiers et répertoire de l'archive à partir du noeud root ('/')
  #   Crée une archive ayant pour nom 'neoShell.compressedFile' contenant : 
  #     - l'archive 'pack.tag.gz' précédemment créée
  #     - le répertoire 'files' s'il est présent
  #     - ce script qui indique comment doit être installé le package à l'aide la fonction 'install()'
  createPackage()
 
  # Suppression du workspace
  # cleanAll()
  
def install():
  # Dézippe l'archive 'pack.tar.gz'
  #  Notons que si les répertoires existent aucune action est effectuée sinon ils sont créés, en revanche les fichiers existants sont écrasés.
  #  Si un fichier est présent dans un répertoire mais pas présent dans l'archive, il est conservé
  unpack()
  
  # Change les droits du répertoire '/tmp/demo'
  ensureDir('/tmp/demo', 'root', 'root', 755) # pour changer les droits récusivement il y a un paramètre optionnel : 'recursive=True'
  
  # Change les droits du fichier 'hello'
  ensureFile('/tmp/demo/hello', 'root', 'root', 600)