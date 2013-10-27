#!/usr/bin/env python
#encoding=utf8

from distutils.core import setup

with open('README') as file:
    long_description = file.read()

setup(
    name='billogram_api',
    version='1.0',
    author='Billogram AB',
    author_email='support@billogram.com',
    description='Library for connecting to the Billogram v2 API',
    long_description=long_description,
    url='https://billogram.com/api/documentation',
    license='MIT',
    py_modules=['billogram_api'],
)
