from setuptools import setup, find_packages

setup(
    name="RemoveForce",
    version="2.0.0",
    author="Hassan Gaddafi",
    author_email="hassanalkzafy@gmail.com",
    description="Force-delete locked files and folders on Windows with advanced process management",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/HassanGaddafi/RemoveForce",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "customtkinter>=5.2.0",
        "psutil>=5.9.0",
    ],
    entry_points={
        "console_scripts": [
            "removeforce=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
)
