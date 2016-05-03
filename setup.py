#!/usr/bin/env python

from setuptools import setup

setup(name='pylm',
      version='0.4',
      description='New Python prototype of PALM pipelines',
      author='Guillem Borrell',
      author_email='guillemborrell@gmail.com',
      packages=['pylm',
                'pylm.components',
                'pylm.persistence',
                'pylm.standalone',
                'pylm.chained',
                'pylm.pipelined'],
      install_requires=['protobuf>=3.0.0b2', 'requests', 'pyzmq', 'plyvel', 'requests']
      )
