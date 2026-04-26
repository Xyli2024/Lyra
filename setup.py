from setuptools import find_packages, setup

setup(
    name="lyra",
    version="0.1.0",
    description="Real-time Apple Music lyrics display for macOS",
    author="Xinyu Li",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=["requests>=2.31.0", "rich>=13.7.0", "PyQt6>=6.6.0"],
    entry_points={
        "console_scripts": [
            "lyra=lyra.__main__:main",
            "lyra-cli=lyra.cli:run",
        ]
    },
)
