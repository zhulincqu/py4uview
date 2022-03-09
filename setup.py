import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="py4uview",
    version="0.0.4",
    author="Lin Zhu",
    author_email="lin.zhu@maxiv.lu.se",
    description="Data analysis package for MAXPEEM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.maxiv.lu.se/zhulin/py4uview",
    project_urls={
        "Bug Tracker": "https://gitlab.maxiv.lu.se/zhulin/py4uview/-/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    packages=["py4uview"],
    install_requires=[
        "xarray>=0.19.0",
    ],
    python_requires=">=3.9",
)
