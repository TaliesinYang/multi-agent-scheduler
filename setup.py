"""
Multi-Agent Intelligent Scheduler
Setup configuration for pip installation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "docs" / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="multi-agent-scheduler",
    version="1.0.0",
    description="Multi-Agent Intelligent Scheduler with CLI Support for AI Task Coordination",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="FDU OS Course Group",
    author_email="",
    url="https://github.com/YOUR_USERNAME/multi-agent-scheduler",
    license="MIT",

    packages=find_packages(),
    include_package_data=True,
    package_data={
        'src': ['agent_config.yaml'],
    },

    python_requires=">=3.10",

    install_requires=[
        "pyyaml>=6.0",
    ],

    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21.0",
        ],
    },

    entry_points={
        "console_scripts": [
            "mas-demo=demos.demo_cli_full:main",
        ],
    },

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Distributed Computing",
    ],

    keywords="multi-agent scheduler AI task-coordination parallel-execution",

    project_urls={
        "Documentation": "https://github.com/YOUR_USERNAME/multi-agent-scheduler/blob/main/docs/README.md",
        "Source": "https://github.com/YOUR_USERNAME/multi-agent-scheduler",
        "Bug Reports": "https://github.com/YOUR_USERNAME/multi-agent-scheduler/issues",
    },
)
