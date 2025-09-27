#!/bin/bash

# MoneyManager Deployment Script
# This script automates the deployment process

set -e  # Exit on any error

echo "🚀 Starting MoneyManager deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.9"
PROJECT_NAME="moneymanager"
VENV_NAME="venv"
REQUIREMENTS_FILE="requirements.txt"

# Functions
print_status() {
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

check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python $PYTHON_VERSION or higher."
        exit 1
    fi

    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Found Python $python_version"

    if [ "$(echo "$python_version >= $PYTHON_VERSION" | bc -l)" -eq 0 ] 2>/dev/null; then
        print_warning "Python version might be too old. Recommended: $PYTHON_VERSION+"
    fi
}

setup_virtual_environment() {
    print_status "Setting up virtual environment..."

    if [ -d "$VENV_NAME" ]; then
        print_warning "Virtual environment already exists. Removing..."
        rm -rf "$VENV_NAME"
    fi

    python3 -m venv "$VENV_NAME"
    source "$VENV_NAME/bin/activate"

    # Upgrade pip
    pip install --upgrade pip

    print_success "Virtual environment created and activated"
}

install_dependencies() {
    print_status "Installing Python dependencies..."

    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        print_error "Requirements file not found: $REQUIREMENTS_FILE"
        exit 1
    fi

    pip install -r "$REQUIREMENTS_FILE"
    print_success "Dependencies installed successfully"
}

setup_environment_file() {
    print_status "Setting up environment configuration..."

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Created .env from .env.example. Please update with your settings."

            # Generate a random secret key
            SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

            # Update .env file with generated secret key
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/SECRET_KEY=your-secret-key-here/SECRET_KEY=$SECRET_KEY/" .env
            else
                # Linux
                sed -i "s/SECRET_KEY=your-secret-key-here/SECRET_KEY=$SECRET_KEY/" .env
            fi

            print_success "Generated new SECRET_KEY in .env file"
        else
            print_error ".env.example file not found. Please create .env manually."
            exit 1
        fi
    else
        print_success "Environment file already exists"
    fi
}

setup_database() {
    print_status "Setting up database..."

    # Create logs directory if it doesn't exist
    mkdir -p logs

    # Make migrations
    python manage.py makemigrations

    # Apply migrations
    python manage.py migrate

    # Setup initial data
    python manage.py setup_initial_data

    print_success "Database setup completed"
}

collect_static_files() {
    print_status "Collecting static files..."

    # Create static directories
    mkdir -p static
    mkdir -p staticfiles
    mkdir -p media

    # Collect static files
    python manage.py collectstatic --noinput

    print_success "Static files collected"
}

create_superuser() {
    print_status "Creating superuser account..."

    echo "Please create an admin account:"
    python manage.py createsuperuser

    print_success "Superuser created"
}

run_tests() {
    print_status "Running tests..."

    python manage.py test --verbosity=2

    if [ $? -eq 0 ]; then
        print_success "All tests passed"
    else
        print_warning "Some tests failed. Check the output above."
    fi
}

start_development_server() {
    print_status "Starting development server..."

    echo ""
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Update .env file with your specific settings"
    echo "2. Review the admin panel at: http://127.0.0.1:8000/admin/"
    echo "3. Access the application at: http://127.0.0.1:8000/"
    echo ""
    echo "To start the server manually later, run:"
    echo "  source $VENV_NAME/bin/activate"
    echo "  python manage.py runserver"
    echo ""

    read -p "Start the development server now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python manage.py runserver
    fi
}

# Main deployment process
main() {
    echo "🏦 MoneyManager - Personal Finance Management System"
    echo "=================================================="
    echo ""

    # Check prerequisites
    check_python

    # Setup virtual environment
    setup_virtual_environment

    # Install dependencies
    install_dependencies

    # Setup environment file
    setup_environment_file

    # Setup database
    setup_database

    # Collect static files
    collect_static_files

    # Optionally create superuser
    read -p "Create a superuser account? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        create_superuser
    fi

    # Optionally run tests
    read -p "Run tests? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        run_tests
    fi

    # Start development server
    start_development_server
}

# Handle script arguments
case "${1:-}" in
    --production)
        export DJANGO_SETTINGS_MODULE="moneymanager.settings.production"
        print_status "Using production settings"
        ;;
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --production    Use production settings"
        echo "  --help, -h      Show this help message"
        echo ""
        exit 0
        ;;
esac

# Run main deployment
main

print_success "Deployment script completed!"

exit 0