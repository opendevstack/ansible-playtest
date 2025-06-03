#!/bin/bash
# Script to build and release the Ansible Scenario Testing package

# Ensure we're in the right directory
cd "$(dirname "$0")" || exit 1

echo "Cleaning previous build artifacts..."
rm -rf build/ dist/ *.egg-info/

echo "Running tests..."
python -m unittest discover -s tests

echo "Building distribution packages..."
python setup.py sdist bdist_wheel

echo "Distribution packages built:"
ls -l dist/

echo "To install the package locally in development mode:"
pip install -e .

echo "To install the package from the distribution files:"
echo "pip install dist/*.whl"

echo "To publish to PyPI (if you have credentials):"
echo "python -m twine upload dist/*"
