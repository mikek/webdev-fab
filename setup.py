from webdev_fab import __version__
from setuptools import setup, find_packages


setup(
    name='webdev-fab',
    version=__version__,
    packages=find_packages(),
    install_requires=[
        'fabric>=1.6.1,<1.7',
    ],
    url='https://github.com/mikek/webdev-fab',
    author='Mykhailo Kolesnyk',
    author_email='mike@openbunker.org'
)
