#!/usr/bin/env python

from setuptools import setup

with open('pylm/version.py') as f:
    exec(f.read())

setup(name='pylm',
      version=__version__,
      description='''Pylm is the Python implementation of PALM, a framework to build
clusters of high performance microservices. It is presented in two
different levels of abstraction. In the high level API you will find
servers and clients that are functional *out of the box*. Use the high
level API if you are interested in simple communication patterns like
client-server, master-slave or a streaming pipeline. In the low level
API there are a variety of small components that, once combined
appropiately, they can be used to implement almost any kind of
microservice. It's what the high level API uses under the hood. Choose
the low level API if you are interested in creating your custom
microservice and your custom communication pattern.
''',
      author='Guillem Borrell',
      author_email='guillemborrell@gmail.com',
      packages=['pylm',
                'pylm.components',
                'pylm.persistence',
                'pylm.standalone',
                'pylm.chained',
                'pylm.pipelined'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
          'Topic :: System :: Distributed Computing'
      ],
      install_requires=['protobuf>=3.0.0', 'requests', 'pyzmq', 'requests']
      )
