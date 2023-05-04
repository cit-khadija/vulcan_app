from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in vulcan_app/__init__.py
from vulcan_app import __version__ as version

setup(
	name="vulcan_app",
	version=version,
	description="Vulcan",
	author="Crafrt",
	author_email="craftinteractive.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
