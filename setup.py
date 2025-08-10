from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="web-scraping-agent",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A powerful and flexible web scraping agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/web-scraping-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.3",
        "lxml>=5.1.0",
        "selenium>=4.18.1",
        "aiohttp>=3.9.3",
        "pandas>=2.2.0",
        "sqlalchemy>=2.0.25",
        "psycopg2-binary>=2.9.9",
        "ratelimit>=2.2.1",
        "tenacity>=8.2.3",
        "fake-useragent>=1.4.0",
        "python-dotenv>=1.0.1",
        "colorlog>=6.8.2",
        "pydantic>=2.5.3",
        "click>=8.1.7",
        "rich>=13.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.3",
            "responses>=0.24.1",
            "black>=24.1.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "webscraper=src.cli:cli",
        ],
    },
)