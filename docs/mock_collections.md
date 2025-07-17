# Mock Collections Directory Configuration

This document explains how to configure the directory where mock collections are stored when using ansible-ci-tools.

## Overview

The mock collections feature allows you to overlay custom ansible modules on top of your real collections during testing. By default, mock modules are looked for in the `ansible_playtest/core/mock_collections/ansible_collections` directory relative to the package installation.

However, you may want to keep your mock modules in a different location, especially if you're testing in a separate project.

## Configuration Options

There are several ways to specify where your mock collections are located:

### 1. Using Pytest Markers

You can use the `mock_collections_dir` marker to specify the path to your mock collections:

```python
import pytest
import os

@pytest.mark.mock_collections_dir('/absolute/path/to/mock_collections')
def test_my_playbook():
    # Test code here
    pass

# Or using a relative path
@pytest.mark.mock_collections_dir('tests/mock_collections')
def test_my_other_playbook():
    # Test code here
    pass
```

### 2. Using Command Line Option

You can provide the path to your mock collections using the command line:

```bash
pytest --ansible-playtest-mock-collections-dir=/path/to/mock_collections
```

### 3. Using Environment Variable

You can set the `ANSIBLE_PLAYTEST_MOCK_COLLECTIONS_DIR` environment variable:

```bash
export ANSIBLE_PLAYTEST_MOCK_COLLECTIONS_DIR=/path/to/mock_collections
pytest
```

## Directory Structure

The mock collections directory should follow the standard Ansible collections structure:

```
mock_collections/
└── ansible_collections/
    └── namespace/
        └── collection/
            ├── plugins/
            │   └── modules/
            │       └── custom_module.py
            └── ...
```

If your specified directory path doesn't include the `ansible_collections` subfolder, the tool will automatically look for it at that location. For example, if you specify `/path/to/mock_collections`, the tool will look for modules in `/path/to/mock_collections/ansible_collections/namespace/collection/...`.

## Priority

The tool will search for mock collections in the following order:

1. Path specified via marker on the test
2. Path specified via CLI option
3. Path specified via environment variable
4. Default path in the ansible-ci-tools package

The first path found with valid mock collections will be used.
