from setuptools import setup, find_packages

setup(
    name="kyb-automation",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'uvicorn',
        # other dependencies
    ],
)