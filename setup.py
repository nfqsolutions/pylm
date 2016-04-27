#!/usr/bin/env python

from setuptools import setup

setup(name='pylm_ng',
      version='0.3',
      description='New Python prototype of PALM pipelines',
      author='Guillem Borrell',
      author_email='guillemborrell@gmail.com',
      packages=['pylm_ng',
                'pylm_ng.components',
                'pylm_ng.persistence',
                'pylm_ng.standalone',
                'pylm_ng.chained',
                'pylm_ng.pipelined'],
      install_requires=['protobuf>=3.0.0b2', 'requests', 'pyzmq', 'plyvel', 'requests']
      )
