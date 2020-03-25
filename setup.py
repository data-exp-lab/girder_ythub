from setuptools import setup, find_packages

setup(
    name="girder_ythub",
    version="1.0.0",
    description="ytHub plugin for Girder",
    author="Kacper Kowalik",
    author_email="xarthisius.kk@gmail.com",
    url="https://hub.yt/",
    license="BSD-3",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: CherryPy",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
    ],
    include_package_data=True,
    packages=find_packages(exclude=["plugin_tests"]),
    zip_safe=False,
    setup_requires=["setuptools-git"],
    install_requires=[
        "girder>=3",
        "girder-jobs",
        "girder-worker[girder]",
        "girder-oauth",
    ],
    entry_points={"girder.plugin": ["ythub = girder_ythub:ytHubPlugin"]},
)
