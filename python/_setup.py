from setuptools import setup, find_packages

setup(
    name='latexminted',
    version='0.5.0',
    packages=find_packages(where='latexminted'),
    package_dir={'': 'latexminted'},
)