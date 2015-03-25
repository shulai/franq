# -*- coding: utf-8 -*-
#
# This file is part of the Franq reporting framework
# Franq is (C)2012,2013 Julio César Gázquez
#
# Franq is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# any later version.
#
# Franq is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Franq; If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup

setup(
    name='franq',
    version='0.9.6',
    description="PyQt-based reporting framework",
    author="Julio Cesar Gazquez",
    author_email='julio@mebamutual.com.ar',
    packages=['franq', 'franq.designer'],
    package_dir={'franq.designer': 'designer'},
    use_2to3=True,
    long_description="""
    Franq is a PyQt4 based reporting framework
    """,
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v2 or later "
            "(GPLv2+)",
        "Environment :: Console",
        "Environment :: X11 Applications :: Qt",
        "Environment :: X11 Applications :: KDE",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
        "Environment :: No Input/Output (Daemon)",
        "Environment :: Web Environment",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        ],
    keywords='reporting pyqt4',
    license='GPL',
    install_requires=[
        #'PyQt'
        ])
