from setuptools import setup

setup(
    name="geecli",
    version="0.1.0",
    packages=["geecli"],
    entry_points={"console_scripts": ["geecli = geecli.__main__:main"]},
    install_requires=[
        "dataclass_wizard>=0.22.2",
    ],
)
