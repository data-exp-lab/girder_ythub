girder_wholetale |build-status| |codecov-badge|
===============================================

Girder plugin enabling intergration with tmpnb

.. |build-status| image:: https://circleci.com/gh/girder/girder.png?style=shield
    :target: https://circleci.com/gh/whole-tale/girder_wholetale
    :alt: Build Status

.. |codecov-badge| image:: https://img.shields.io/codecov/c/github/whole-tale/girder_wholetale.svg
    :target: https://codecov.io/gh/whole-tale/girder_wholetale
    :alt: Coverage Status

Development
-----------

Running Tests
*************

This Girder plugin includes a set of tests in ``./plugin_tests``. To run these, you'll need to get a copy of the `WholeTale Fork of Girder`_ and run this plugin's test as part of Girder's test suite.

Pre-requisites:

- Python 3
- CMake
- An instance of MongoDB, running at mongodb://localhost:27101

Optional pre-requisites:

- coverage
- flake8

::

    $ git clone https://github.com/whole-tale/girder
    $ cd girder
    $ rm -rf plugins/wholetale
    $ cp -r {path_to_your_version_of_this_repo}/ plugins/wholetale
    $ # Install dependencies
    $ pip install -r requirements-dev.txt
    $ pip install -r plugins/wholetale/requirements.txt
    $ cd tests
    $ # Set up environment variables for CMake
    $ export PYTHON="{YOUR_PYTHON_3_BIN_PATH}"
    $ export COVERAGE="{YOUR_COVERAGE_BIN_PATH}"
    $ export FLAKE8="{YOUR_FLAKE8_BIN_PATH}"
    $ cmake \
        -DRUN_CORE_TESTS:BOOL=OFF \
        -DBUILD_JAVASCRIPT_TESTS:BOOL=OFF \
        -DJAVASCRIPT_STYLE_TESTS:BOOL=OFF \
        -DTEST_PLUGINS:STRING=wholetale \
        -DCOVERAGE_MINIMUM_PASS:STRING=4 \
        -DPYTHON_COVERAGE=ON \
        -DPYTHON_STATIC_ANALYSIS=ON \
        -DPYTHON_VERSION="3.6" \
        -DPYTHON_COVERAGE_EXECUTABLE="$COVERAGE" \
        -DFLAKE8_EXECUTABLE="$FLAKE8" \
        -DPYTHON_EXECUTABLE="$PYTHON" \
        ..
    $ ctest -VV
..

.. _`WholeTale Fork of Girder`: https://github.com/whole-tale/girder
