#!/bin/bash
# filepath: install_certificates.sh

set -euo pipefail

# Script to install SSL certificates for Nexus repositories
# This script downloads certificates from specified URLs and installs them
# to the system's trusted certificate store

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# URLs to fetch certificates from
URLS=(
    "nexus-ods.apps.eu-dev.ocp.aws.boehringer.com"
    "nexus-ods.apps.us-test.ocp.aws.boehringer.com"
)

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. Certificates will be installed system-wide."
        return 0
    else
        print_info "Not running as root. You may need sudo privileges for system-wide installation."
        return 1
    fi
}

# Function to detect the operating system
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    elif [[ -f /etc/redhat-release ]]; then
        OS="rhel"
    elif [[ -f /etc/debian_version ]]; then
        OS="debian"
    else
        OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    fi
    
    print_info "Detected OS: $OS"
}

# Function to install required tools
install_dependencies() {
    print_info "Checking and installing required dependencies..."
    
    case $OS in
        ubuntu|debian)
            if ! command -v openssl &> /dev/null; then
                print_info "Installing openssl..."
                sudo apt-get update && sudo apt-get install -y openssl ca-certificates
            fi
            ;;
        centos|rhel|fedora)
            if ! command -v openssl &> /dev/null; then
                print_info "Installing openssl..."
                sudo yum install -y openssl ca-certificates || sudo dnf install -y openssl ca-certificates
            fi
            ;;
        *)
            print_warning "Unknown OS. Please ensure openssl is installed."
            ;;
    esac
}

# Function to download certificate from a host
download_certificate() {
    local hostname=$1
    local port=${2:-443}
    local cert_file="${hostname}.crt"
    
    print_info "Downloading certificate for ${hostname}:${port}..."
    
    # Download the certificate
    if echo "" | openssl s_client -connect "${hostname}:${port}" -servername "${hostname}" 2>/dev/null | \
       openssl x509 -outform PEM > "${cert_file}"; then
        print_success "Certificate downloaded: ${cert_file}"
        return 0
    else
        print_error "Failed to download certificate for ${hostname}"
        return 1
    fi
}

# Function to verify certificate
verify_certificate() {
    local cert_file=$1
    
    print_info "Verifying certificate: ${cert_file}"
    
    if openssl x509 -in "${cert_file}" -text -noout > /dev/null 2>&1; then
        # Display certificate information
        local subject=$(openssl x509 -in "${cert_file}" -subject -noout | sed 's/subject=//')
        local issuer=$(openssl x509 -in "${cert_file}" -issuer -noout | sed 's/issuer=//')
        local expiry=$(openssl x509 -in "${cert_file}" -enddate -noout | sed 's/notAfter=//')
        
        print_info "Subject: ${subject}"
        print_info "Issuer: ${issuer}"
        print_info "Expires: ${expiry}"
        return 0
    else
        print_error "Invalid certificate file: ${cert_file}"
        return 1
    fi
}

# Function to install certificate to system store
install_certificate() {
    local cert_file=$1
    local hostname=$2
    
    print_info "Installing certificate for ${hostname}..."
    
    case $OS in
        ubuntu|debian)
            local dest_file="/usr/local/share/ca-certificates/${hostname}.crt"
            sudo cp "${cert_file}" "${dest_file}"
            sudo update-ca-certificates
            ;;
        centos|rhel|fedora)
            local dest_file="/etc/pki/ca-trust/source/anchors/${hostname}.crt"
            sudo cp "${cert_file}" "${dest_file}"
            sudo update-ca-trust
            ;;
        *)
            print_warning "Unknown OS. Certificate saved as ${cert_file} but not installed to system store."
            print_info "Please manually add ${cert_file} to your system's certificate store."
            return 1
            ;;
    esac
    
    print_success "Certificate installed for ${hostname}"
}

# Function to test certificate installation
test_certificate() {
    local hostname=$1
    local port=${2:-443}
    
    print_info "Testing certificate installation for ${hostname}..."
    
    if echo "" | openssl s_client -connect "${hostname}:${port}" -servername "${hostname}" -verify_return_error > /dev/null 2>&1; then
        print_success "Certificate verification successful for ${hostname}"
        return 0
    else
        print_warning "Certificate verification failed for ${hostname}. This might be expected if using self-signed certificates."
        return 1
    fi
}

# Function to create backup of existing certificates
create_backup() {
    local backup_dir="cert_backup_$(date +%Y%m%d_%H%M%S)"
    
    print_info "Creating backup directory: ${backup_dir}"
    mkdir -p "${backup_dir}"
    
    case $OS in
        ubuntu|debian)
            if [[ -d /usr/local/share/ca-certificates ]]; then
                cp -r /usr/local/share/ca-certificates "${backup_dir}/" 2>/dev/null || true
            fi
            ;;
        centos|rhel|fedora)
            if [[ -d /etc/pki/ca-trust/source/anchors ]]; then
                cp -r /etc/pki/ca-trust/source/anchors "${backup_dir}/" 2>/dev/null || true
            fi
            ;;
    esac
    
    print_info "Backup created in: ${backup_dir}"
}

# Main function
main() {
    print_info "Starting certificate installation for Nexus repositories..."
    
    # Check if running as root
    IS_ROOT=false
    if check_root; then
        IS_ROOT=true
    fi
    
    # Detect operating system
    detect_os
    
    # Install dependencies
    install_dependencies
    
    # Create backup
    if [[ $IS_ROOT == true ]]; then
        create_backup
    fi
    
    # Process each URL
    local success_count=0
    local total_count=${#URLS[@]}
    
    for hostname in "${URLS[@]}"; do
        print_info "Processing ${hostname}..."
        
        # Download certificate
        if download_certificate "${hostname}"; then
            # Verify certificate
            if verify_certificate "${hostname}.crt"; then
                # Install certificate if running as root
                if [[ $IS_ROOT == true ]]; then
                    if install_certificate "${hostname}.crt" "${hostname}"; then
                        ((success_count++))
                    fi
                else
                    print_info "Certificate saved as ${hostname}.crt (not installed to system store - requires root)"
                    ((success_count++))
                fi
            fi
        fi
        
        echo ""
    done
    
    # Summary
    print_info "Certificate installation summary:"
    print_info "Processed: ${total_count} certificates"
    print_success "Successful: ${success_count} certificates"
    
    if [[ $success_count -eq $total_count ]]; then
        print_success "All certificates processed successfully!"
        
        if [[ $IS_ROOT == true ]]; then
            print_info "Testing certificate installations..."
            echo ""
            for hostname in "${URLS[@]}"; do
                test_certificate "${hostname}"
            done
        fi
    else
        print_warning "Some certificates failed to process. Check the output above for details."
        exit 1
    fi
    
    # Cleanup downloaded certificate files if installed to system
    if [[ $IS_ROOT == true ]]; then
        print_info "Cleaning up temporary certificate files..."
        for hostname in "${URLS[@]}"; do
            rm -f "${hostname}.crt"
        done
    fi
    
    print_success "Certificate installation completed!"
}

# Script usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Install SSL certificates for Nexus repositories"
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo "  -v, --verify  Only verify existing certificates (don't install)"
    echo ""
    echo "URLs processed:"
    for url in "${URLS[@]}"; do
        echo "  - https://${url}/"
    done
    echo ""
    echo "Note: Run with sudo for system-wide installation"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -v|--verify)
            print_info "Verification mode - testing existing certificates only"
            for hostname in "${URLS[@]}"; do
                test_certificate "${hostname}"
            done
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Run main function
main "$@"