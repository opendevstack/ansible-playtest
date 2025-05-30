#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
  echo -e "${GREEN}[✓] $1${NC}"
}

print_error() {
  echo -e "${RED}[✗] $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}[!] $1${NC}"
}

echo "Starting project setup..."

# 1. Check for Python version >= 3.10.12
if command -v python3 &>/dev/null; then
  PYTHON_VERSION=$(python3 -c "import sys; print(sys.version.split()[0])")
  PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
  PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
  PYTHON_PATCH=$(echo $PYTHON_VERSION | cut -d. -f3)

  if [[ "$PYTHON_MAJOR" -ge 3 && "$PYTHON_MINOR" -ge 10 ]]; then
    if [[ "$PYTHON_MINOR" -eq 10 && "$PYTHON_PATCH" -lt 12 ]]; then
      print_error "Python version ${PYTHON_VERSION} detected, but version >= 3.10.12 is required."
      echo "Please update Python and run this script again."
      exit 1
    else
      print_status "Python ${PYTHON_VERSION} is installed."
    fi
  else
    print_error "Python version ${PYTHON_VERSION} detected, but version >= 3.10.12 is required."
    echo "Please update Python and run this script again."
    echo "You can install it using your package manager, for example:"
    echo "   sudo apt install python3.10 python3.10-venv python3.10-dev"
    exit 1
  fi
else
  print_error "Python 3 is not installed."
  echo "Please install Python 3.10.12 or higher and run this script again."
  exit 1
fi

# 2. Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  print_status "Creating virtual environment..."
  python3 -m venv .venv
  if [ $? -ne 0 ]; then
    print_error "Failed to create virtual environment with venv. Trying with virtualenv..."

    # Check if virtualenv exists
    if ! command -v virtualenv &>/dev/null; then
      print_warning "virtualenv is not installed. Installing it now..."
      pip3 install virtualenv
      if [ $? -ne 0 ]; then
        print_error "Failed to install virtualenv. Please install it manually."
        echo "Try: pip3 install virtualenv"
        exit 1
      fi
      print_status "virtualenv has been installed."
    fi

    virtualenv .venv
    if [ $? -ne 0 ]; then
      print_error "Failed to create virtual environment."
      exit 1
    fi
  fi
  print_status "Virtual environment created successfully."
else
  print_status "Virtual environment already exists."
fi

# 4. Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
  print_error "Failed to activate virtual environment."
  exit 1
fi
print_status "Virtual environment activated. ($(which python))"

# 5. Install requirements if they exist
for reqfile in requirements*.txt; do
  if [ -f "$reqfile" ]; then
    print_status "Installing $reqfile..."
    pip install -r "$reqfile"
    if [ $? -ne 0 ]; then
      print_error "Failed to install requirements from $reqfile."
      exit 1
    fi
    print_status "Successfully installed requirements from $reqfile."
  else
    print_warning "$reqfile not found. Skipping..."
  fi
done

print_status "Setup completed successfully!"
echo ""
echo "To activate the virtual environment in the future, you can:"
echo "1. Run: source .venv/bin/activate"
echo ""
echo "You are now working in the virtual environment. Happy coding!"
