#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 20.4 Ralph Bean

from setuptools import setup

setup(
    name='mailman3-fedmsg-plugin',
    version='0.4',
    description='Emit fedmsg messages from mailman3',
    author="Ralph Bean",
    author_email="rbean@redhat.com",
    license='LGPLv2',
    url='http://github.com/fedora-infra/mailman3-fedmsg-plugin',
    py_modules=['mailman3_fedmsg_plugin'],
)
