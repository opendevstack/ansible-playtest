#!/bin/bash
#
# Update the version of AnsiblePlayTest and create a release
#

# Default values
NEW_VERSION=""
TAG_VERSION=true
PUSH_CHANGES=false

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --version) NEW_VERSION="$2"; shift ;;
        --no-tag) TAG_VERSION=false ;;
        --push) PUSH_CHANGES=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Check if version is provided
if [ -z "$NEW_VERSION" ]; then
    echo "Error: Version must be specified with --version parameter"
    echo "Usage: $0 --version X.Y.Z [--no-tag] [--push]"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check that the version has a valid format
if ! [[ $NEW_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format X.Y.Z"
    exit 1
fi

# Update version in pyproject.toml
echo "Updating version in pyproject.toml..."
sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" "$SCRIPT_DIR/pyproject.toml"

# Update version in __init__.py
echo "Updating version in __init__.py..."
sed -i "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" "$SCRIPT_DIR/ansible_playtest/__init__.py"

# Update version in setup.py (if needed)
if [ -f "$SCRIPT_DIR/setup.py" ]; then
    if grep -q "version=" "$SCRIPT_DIR/setup.py"; then
        echo "Updating version in setup.py..."
        sed -i "s/version=\".*\"/version=\"$NEW_VERSION\"/" "$SCRIPT_DIR/setup.py"
    fi
fi

# Create a git commit for the version change
echo "Creating git commit for version $NEW_VERSION..."
git add "$SCRIPT_DIR/pyproject.toml" "$SCRIPT_DIR/ansible_playtest/__init__.py"
if [ -f "$SCRIPT_DIR/setup.py" ]; then
    git add "$SCRIPT_DIR/setup.py"
fi
git commit -m "Release version $NEW_VERSION"

# Create a git tag for the version
if $TAG_VERSION; then
    echo "Creating git tag v$NEW_VERSION..."
    git tag -a "v$NEW_VERSION" -m "Version $NEW_VERSION"
fi

# Push changes if requested
if $PUSH_CHANGES; then
    echo "Pushing changes and tags to remote repository..."
    git push
    git push --tags
fi

echo "Version updated to $NEW_VERSION"
echo ""
echo "Next steps:"
if ! $PUSH_CHANGES; then
    echo "1. Push the changes: git push && git push --tags"
fi
echo "2. Build the distribution: python -m build"
echo "3. Upload to PyPI: twine upload dist/*"

exit 0
