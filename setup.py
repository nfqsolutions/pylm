#!/usr/bin/env python

from setuptools import setup

setup(name='pylm',
      version='0.6.3',
      description='New Python prototype of PALM pipelines',
      author='Guillem Borrell',
      author_email='guillemborrell@gmail.com',
      packages=['pylm',
                'pylm.components',
                'pylm.persistence',
                'pylm.standalone',
                'pylm.chained',
                'pylm.pipelined'],
      install_requires=['protobuf>=3.0.0', 'requests', 'pyzmq', 'requests']
      )
