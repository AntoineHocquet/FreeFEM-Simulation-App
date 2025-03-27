from setuptools import setup, find_packages

setup(
    name="freefem_simulation_app",
    version="0.1.0",
    author="Antoine Hocquet",
    description="Dockerized FreeFEM simulation pipeline with CLI and animated visualization",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas",
        "matplotlib"
    ],
    entry_points={
        "console_scripts": [
            "simulate = main:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)