from distutils.core import setup, Extension

module1 = Extension('ossim',
                    sources = ['src/ossimmodule.cpp'],
                    libraries = ['ossim'],
                    )

setup (name = 'Ossim Height',
       version = '1.0',
       description = 'This is a demo package',
       ext_modules = [module1])
