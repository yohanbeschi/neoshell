try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    
setup(name         = 'NeoShell',
      version      = '0.1',
      author       = 'Yohan Beschi',
      author_email = 'yohan.beschi@gmail.com',
      license      = 'WTFPL',
      description  = 'NeoShell',
      package_dir  = {"":"src"},
      py_modules   = ['neoshell']
)