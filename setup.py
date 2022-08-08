#!/usr/bin/env python3
from codecs import open
from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))


setup(
    name="pygrenton",
    version="0.0.1",
    description="Lightweight Python library to interact with grenton smart-home system.",
    author="Paweł Rogaliński",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Topic :: Home Automation",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=[
        "cryptography"
    ],
    zip_safe=True,
    keywords="grenton",
)