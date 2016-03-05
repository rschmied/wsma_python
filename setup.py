
from setuptools import setup, find_packages
setup(
    name = "wsma",
    version = "0.3",
    packages = find_packages(),
    install_requires = ["requests", "jinja2", 'xmltodict', 'paramiko']

)
