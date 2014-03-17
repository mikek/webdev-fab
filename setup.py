from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages


setup(
    name = 'webdev-fab',
    version = '0.4.8',
    packages = find_packages(),
    install_requires = ['fabric>=1.6.1,<1.7', ],
    url = 'https://github.com/mikek/webdev-fab',
    author = 'Mikhail Kolesnik',
    author_email = 'mike@openbunker.org'
)
