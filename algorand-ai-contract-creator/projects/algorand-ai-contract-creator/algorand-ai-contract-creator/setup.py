"""
Setup script for algorand-ai-contract-creator
Enables editable installation with: pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="algorand-ai-contract-creator",
    version="0.1.0",
    packages=find_packages(include=["tools", "tools.*", "smart_contracts", "smart_contracts.*"]),
    install_requires=[
        "streamlit>=1.28.1",
        "openai>=1.3.5",
        "pyteal>=0.24.0",
        "py-algorand-sdk>=2.6.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "black>=23.11.0",
            "pylint>=3.0.2",
        ],
    },
    python_requires=">=3.10",
)
