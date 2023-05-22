import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="HITI_anon_internal",
    version="2022.8.27.6",  # versioning schema as the year and month
    author="zmz223",
    author_email="zzaiman@emory.edu",
    description="internal HITI anonymization tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jeong-jasonji/HITI_anon_internal",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.6',
)


