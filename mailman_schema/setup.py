#!/usr/bin/env python
#
# Copyright (C) 2018  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os

from setuptools import setup, find_namespace_packages


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README")) as fd:
    README = fd.read()


setup(
    name="fedora_messaging_mailman_schemas",
    version="0.0.1",
    description="A schema describing fedora-messaging messages sent by mailman",
    long_description=README,
    url="http://github.com/fedora-infra/mailman3-fedmsg-plugin",
    # Possible options are at https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    license="LGPLv3+",
    maintainer="Fedora Infrastructure Team",
    maintainer_email="infrastructure@lists.fedoraproject.org",
    platforms=["Fedora", "GNU/Linux"],
    keywords="fedora",
    packages=find_namespace_packages(include=["fedora_messaging_schemas.*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=["fedora_messaging"],
    test_suite="fedora_messaging_schemas.mailman.tests",
    entry_points={
        "fedora.messages": [
            "mailman.messageV1=fedora_messaging_schemas.mailman.schemas:MessageV1",
            "mailman.messageV2=fedora_messaging_schemas.mailman.schemas:MessageV2",
        ]
    },
)
