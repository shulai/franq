
from setuptools import setup

setup(
    name='franq',
    version='0.1',
    description="PyQt-based report engine",
    author="Julio Cesar Gazquez",
    author_email='julio@mebamutual.com.ar',
    url='http://jotacege.com.ar/franq',
    packages=['franq', 'franq.designer'],
    package_dir={'franq.designer': 'designer'},
    long_description="""
    Franq is a PyQt4 based report engine, similar to Geraldo Reports
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
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        ],
    keywords='reporting pyqt4',
    license='GPL',
    install_requires=[
        'PyQt'
        ])
