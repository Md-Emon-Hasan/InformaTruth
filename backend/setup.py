from setuptools import setup
from setuptools import find_packages

setup(
    name="InformaTruth",
    version="1.0.0",
    author="Md Emon Hasan",
    author_email="iconicemon01@gmail.com",
    description=(
        "AI-Driven News Authenticity Analyzer: BERT-based Multimodal "
        "Fake News Detection with Explanation using FLAN-T5, "
        "and Multi-Agent LangGraph System."
    ),
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Md-Emon-Hasan/InformaTruth",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "torch>=1.13.1",
        "pandas>=1.5.3",
        "scikit-learn>=1.2.2",
        "datasets>=2.16.1",
        "transformers>=4.35.0",
        "tqdm>=4.66.1",
        "newspaper3k>=0.2.8",
        "PyMuPDF>=1.23.2",
        "pytest>=7.4.2",
        "fastapi>=0.110.0",
        "flask>=2.2.5",
        "gunicorn>=21.2.0",
        "uvicorn[standard]>=0.27.1",
        "numpy>=1.24.2",
        "streamlit>=1.35.0",
        "sentencepiece>=0.2.0",
        "protobuf>=4.25.3",
        "requests>=2.31.0",
        "lxml>=5.2.1",
        "lxml-html-clean>=0.1.1",
        "duckduckgo-search",
        "langgraph",
        "langchain",
        "langchain-community",
        "langchain-huggingface",
        "huggingface-hub",
        "langchain-core",
        "langchain-community",
        "sqlmodel",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    entry_points={
        "console_scripts": [
            "informa-truth=app.main:main",
        ],
    },
)
