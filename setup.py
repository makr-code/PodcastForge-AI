"""
PodcastForge AI - Setup Configuration
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="podcastforge-ai",
    version="1.0.0",
    author="makr-code",
    author_email="",
    description="KI-gestützter Podcast-Generator mit Ollama und ebook2audiobook",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/makr-code/PodcastForge-AI",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Content Creators",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.3.0",
        ],
        "web": [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
            "gradio>=3.40.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "podcastforge=podcastforge.cli:main",
            "pf=podcastforge.cli:main",  # Kurze Alternative
        ],
    },
    include_package_data=True,
    package_data={
        "podcastforge": [
            "data/*.json",
            "templates/*.yaml",
            "prompts/*.txt",
        ],
    },
    zip_safe=False,
)
