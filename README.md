# Neoshell
Neoshell est une boîte à outils dédiée à la livraison continue.

Neoshell est :

- un shell like permettant d'exécuter  des commandes en offrant une gestion des logs (indiquant notamment l'host sur lequel est exécuté une commande) et des erreurs out of the box
- un chef/puppet/etc like grâce à des fonctions permettant de définir l'état du système cible
- un ansible/salt/rundeck/fabric/etc like avec la gestion des déploiements sur un hôte distant. 
- un yum/apt-get/etc like puisqu'il permet de créer des packages (appelés aussi bundles), de détailler leur installation et de les installer simplement 

Neoshell est constitué d'un seul fichier [neoshell.py](https://github.com/yohanbeschi/.../libs/neoshell/src/neoshell.py) à copier dans un répertoire présent dans le path (par exemple : `/usr/local/bin`)

### Hello world
Commençons par un exemple simple.

La première étape est d'installer Neoshell sur le poste de travail (Unix uniquement). Après avoir cloné le projet [???](https://github.com/yohanbeschi/neoshell) :

	$ sudo cp src/neoshell.py /usr/local/bin
	$ sudo chmod +x /usr/local/bin/neoshell.py
	
Voyons ensuite un script affichant 'Hello World'.

    #!/usr/bin/python
    import imp
    imp.load_source('neoshell', '/usr/local/bin/neoshell.py')
    from neoshell import __builtin__, NeoShell, echo
    __builtin__.neoShell = NeoShell()
    
    #--------------------- Your code ---------------------
    echo('Hello World')
    
[Source](https://github.com/yohanbeschi/.../gh-pages/src/helloworld.py)

Il suffit d'exécuter le script de la manière suivante :

	$ ./helloworld.py

### execute et install
Bien évidemment dans la réalité un script fait beaucoup plus de choses qu'afficher quelque chose dans la console, notamment pour la livraison continue.

Pour profiter pleinement de tous les avantages de Neoshell il est nécessaire de créer une fonction nommée `execute` et si l'on souhaite créer un bundle installable, une fonction nommée `install` :

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

[Source](https://github.com/yohanbeschi/.../gh-pages/src/myfirstexecute.py)

Notons que l'appel aux fonctions `workspace()`, `appName()`, `version()`, `env()` et `buildPaths()` est utile uniquement si l'on souhaite avoir un espace de travail. Dans certains cas ce n'est pas utile. 

Pour exécuter la méthode `execute` et dans le cas présent créer un bundle, il faut utiliser la commande suivante:

	$ neoshell.py myfirstexecute.py execute

Le bundle est créé dans le répertoire `neoShell.appWorkspace`.

Nous pouvons ensuite installer le bundle en local :

	# neoshell.py install <chemin absolu du bundle>/demo-1.0-noenv.tar.gz <chemin absolu d'un workspace (différent de 'target')>
	# Exemple:
	$ neoshell.py install /home/ec2-user/github/forge/src/target/ \    
      demo/1.0/noenv/demo-1.0-noenv.tar.gz /home/ec2-user/myws

### Notes 

1. Il est possible de passer des paramètres à chaque fonction avec l'argument `-e` pour la méthode `execute()` et `-i` pour la fonction `install()`, tous deux suivis des paramètres. Ces paramètres sont ensuite respectivement accessibles dans les listes `neoShell.executeArgs` et `neoShell.installArgs`.
1. Pour vérifier que l'ensemble des paramètres nécessaires au bon fonctionnement d'une des deux méthodes sont présents, la fonction `ensureParams()` peut être utilisée. Par exemple : `ensureParams(neoShell.executeArgs, 3, 'Usage: createBranch.py execute -e <branch start name> <master branch> <pom file in app>')`

### Quelques fonctions utiles

<table>
  <tr>
    <th>function</th>
    <th>description</th>
  </tr>
  <tr>
    <td><code>executeScript(script)</code></td>
    <td>Exécute la méthode <code>execute</code> du script passé en paramètre</td>
  </tr>
  <tr>
    <td><code>buildPackage(script, moveTo=None)</code></td>
    <td>Idem que <code>executeScript()</code> (à la différence que l'on s'attend à avoir un bundle de créé)
        tout en permettant d'indiquer où doit être déplacé ce bundle. Par exemple, dans le répertoire 'files'
        pour être packagé dans le bundle issu du script appelant cette fonction.</td>
  <tr>
  <tr>
    <td><code>installPackage(appname, installArgs=[])</code></td>
    <td>Permet d'installer un package dans un script d'installation (fonction <code>install()</code>). Exemple:
        <ul>
          <li><code>installPackage('%sapache.ant-1.9.4.tar.gz' % neoShell.appWorkspaceFiles)</code></li>
          <li><code>binaryRepo('http://forge.aws.cpdev.local/packages/apache')<br />installPackage('apache.ant-1.9.4')</code></li>
        </ul>          
    </td>
  </tr>
  <tr>
    <td><code>binaryRepo(url)</code></td>
    <td>Permet de définir le répertoire de binaires.<br />
        Attention, <code>binaryRepo()</code> et <code>installPackage()</code> ne s'appuient pas l'un sur l'autre. De fait, il est nécessaire
        d'indiquer le répertoire dans lequel est le tar.gz. Malheureusement, nous ne pouvons pas définir qu'une seule fois le repository
        de binaires en utilisant l'url <code>http://forge.aws.cpdev.local/packages/</code>
    </td>
  </tr>
  <tr>
    <td><code>ensureUsers(usersConfigPath)</code></td>
    <td>Permet de créer des utilisateurs avec une clé publique en partant d'un fichier XML.
        Exemple de <a href="https://github.com/yohanbeschi/.../blob/master/configuration/users-apibus.i1.xml">fichier XML</a>.
        Attention cette fonction a pour objectif de créer des utilisateurs réels qui souhaitent se connecter en SSH aux instances.
        Pour créer des utilisateurs applicatifs veuillez vous reporter à la fonction suivante <code>ensureUser()</code></td>
  </tr>
  <tr>
    <td><code>ensureUser(username, fullname=None, home=None,
                         group=None, createHome=False, 
                         publicKey=None)</code></td>
    <td>Permet de créer un utilisateur</td>
  </tr>
  <tr>
    <td><code>ensureServiceStarted(name)</code><br /><code>ensureServiceStopped(name)</code></td>
    <td>Démarre/stoppe le service en paramètre</td>
  </tr>
  <tr>
    <td><code>serviceStart(name)</code></td>
    <td>Démarre le service en paramètre s'il est arrêté sinon le restart</td>
  </tr>
  
</table>  


### Déployer un bundle sur un serveur distant

En plus des commandes `execute` et `install` Neoshell possède une commande deploy permettant de déployer un bundle précédemment créé.

	$ neoshell.py deploy <user@host> <chemin vers la clé privé> \
      <url vers le repository de binaires ou chemin absolu>.tar.gz <chemin du workspace>

Le `deploy` effectue deux opérations :

- installation (copie + attribution des droits) du fichier `neoshell.py` sur le serveur sur lequel nous allons déployer le bundle
- exécution de la commande `install` en SSH 

### Dry run
NeoShell possède une commande `dryrun` qu'il n'est pas conseillé d'utiliser.

Certains scripts déjà créés font référence à une variable `neoShell.dryRun` dans des conditions. Il est conseillé de supprimer ces conditions.  

## Les repos DevOps pour Go
Chaque projet doit avoir un repository devops (`project-devops`).

Ce repo est organisé de la manière suivante :

	|_configuration
	|   |_ <appli>.<env>.json  # dictionnaire clés/valeurs 
	|   |_ sudoers-<env>       # fichier sudoer standard
	|   |_ users-<env>.xml     # fichier contenant les utilisateurs à créer avec leur clé publique
	|_middleware
	|   |_ apps                # scripts permettant de créer des bundles pour les applications non disponibles en `yum`, comme `mule` ou `activemq`
	|   |_ static              # fichiers ne faisant pas parti de l'installation standard d'une application (ex: ilex) mais communs à tous les environnements
	|   |_ templates           # fichiers contenant des variables à remplacer avec des valeurs liées à un environnement
	|_scripts
	|  |_ prepare<Appli>.py    # Adapte les fichiers utilisés par l'outil de build (ex : pom.xml), `version` et `distributionManagement` 
	|  |_ bundle<Appli>.py     # Script permettant de créer un bundle commun à tous les environnements et d'indiquer les étapes de son installation
	|  |_ bundle<Appli>Env.py  # Script permettant de créer un bundle contenant les templates variabilisés
	|_ LATESTBUILD             # initialisé à 0 sans retour à la ligne en EOL unix puis manipulé par GO
	|_ VERSION                 # initialisé à 0 sans retour à la ligne en EOL unix puis manipulé par GO

Notes : 

- ATTENTION pour le dictionnaire, le nom de l'appli et l'environnement doivent être séparés par un point. Et le nom de l'application et de l'environnement ne doivent pas contenir de tiret ('-')
- Le script `bundle<Appli>Env.py` doit utiliser la fonction `installPackage() `avec en paramètre le nom du bundle créé par le script `bundle<Appli>.py` dans sa fonction `install()`

### Templates et dictionnaires
Dans un template les variables sont identifiées de la manière suivante : `@{var}` où `var` est la variable.

Les dictionnaires contiennent les valeurs des variables pour chaque environnement. Si la valeur d'une variable est commune à plusieurs environnements elle doit être dupliquée. 

La variabilisation des templates se fait à l'aide de la méthode `replaceVariables()` :

	templates = {
	  '%senvironmentConfig.js.tpl' % pathToTemplates: envConfJs,
	  '%shttpd.conf.tpl' % pathToTemplates: httpdConf,
	  '%ssngwebag.xml.tpl' % pathToTemplates: sngwebag
	}
	
	dictionary = '%sconfiguration/%s.json' % (devopsDir, environment)
	replaceVariables(templates, dictionary)

[Exemple](https://github.com/yohanbeschi/.../blob/master/scripts/bundleFaceEnv.py)

### Création de sudoers
Pour que les équipes puissent se connecter en SSH aux différentes instances il est nécessaire de créer deux fichiers pour chaque environnement :

- [sudoers-&lt;env>](https://github.com/yohanbeschi/.../blob/master/configuration/sudoers-apibus.i1)
- [users-&lt;env>.xml](https://github.com/yohanbeschi/.../blob/master/configuration/users-apibus.i1.xml)

Ensuite dans le script `bundle<Appli>Env.py` il est nécessaire d'ajouter le code suivant :

	def execute():
	  # ...
	  
	  useFile('%sconfiguration/sudoers-%s' % (devopsDir, environment))
	  useFile('%sconfiguration/users-%s.xml' % (devopsDir, environment))
	  
	  # ...
	  
	def install():
	  # ...
	  
	  addSudoer('%ssudoers-%s' % (neoShell.appWorkspaceFiles, environment))
	  
	  usersXml = '%susers-%s.xml' % (neoShell.appWorkspaceFiles, environment)
	  ensureUsers(usersXml)

	   # ...

[Exemple](https://github.com/ybe.../scripts/bundleHttpdEnv.py)