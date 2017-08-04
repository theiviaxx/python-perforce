#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

requirements = [
    'path.py==8.1.1',
    'six==1.10.0'
]

test_requirements = [
    'path.py==8.1.1',
    'six==1.10.0',
    'pytest==3.1.2',
]
version = ''
with open('perforce/__init__.py', 'r') as fh:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fh.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')


setup(
    name='python-perforce',
    version=version,
    description='Pure python Perforce API',
    long_description=readme + '\n\n' + history,
    author='Brett Dixon',
    author_email='theiviaxx@gmail.com',
    url='https://github.com/theiviaxx/python-perforce',
    packages=[
        'perforce',
    ],
    package_dir={'python-perforce':
                 'python-perforce'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='python-perforce',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
