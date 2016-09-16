#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import django_performance_testing

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = django_performance_testing.__version__

if sys.argv[-1] == 'publish':
    os.system('make release')
    sys.exit()

readme = open('README.rst').read()

description = "Performance testing tools for Django"

setup(
    name='django-performance-testing',
    version=version,
    description=description,
    long_description=readme,
    author='Paessler AG BIS Team',
    author_email='bis@paessler.com',
    url='https://github.com/PaesslerAG/django-performance-testing',
    packages=[
        'django_performance_testing',
    ],
    include_package_data=True,
    install_requires=[
        'Django>=1.8',
    ],
    license="BSD",
    zip_safe=False,
    keywords='django-performance-testing',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.5',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
    ],
)
