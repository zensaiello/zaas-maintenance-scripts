#!/usr/bin/env python

import os.path

from setuptools import setup

NAME = "servicetester"

setup(name=NAME,
      version="1.0",
      description="ZenHub Service Tester",
      author="Ben Hirsch",
      author_email="bhirsch@zenoss.com",
      url="https://www.zenoss.com",
      packages=[NAME],
)

