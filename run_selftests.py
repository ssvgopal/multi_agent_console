#!/usr/bin/env python
"""
Run selftests for MultiAgentConsole.

This script is a simple wrapper around the selftest_framework.py module.
It provides a convenient way to run selftests for the MultiAgentConsole.
"""

import sys
import argparse
import logging
from selftest_framework import run_self_tests, list_available_tests, create_github_action

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the selftest script."""
    parser = argparse.ArgumentParser(description='Run selftests for MultiAgentConsole')
    
    # Test selection options
    parser.add_argument('--categories', nargs='+', help='Test categories to run (e.g., unit, auth, workflow)')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--core', action='store_true', help='Run core feature tests')
    parser.add_argument('--advanced', action='store_true', help='Run advanced feature tests')
    
    # Test execution options
    parser.add_argument('--integration', action='store_true', help='Include integration tests')
    parser.add_argument('--server', action='store_true', help='Include server tests')
    
    # Output options
    parser.add_argument('--list', action='store_true', help='List available tests')
    parser.add_argument('--github-action', action='store_true', help='Create GitHub Actions workflow file')
    parser.add_argument('--report', help='Path to save the test report')
    
    args = parser.parse_args()
    
    # List available tests if requested
    if args.list:
        list_available_tests()
        return 0
    
    # Create GitHub Actions workflow file if requested
    if args.github_action:
        workflow_file = create_github_action()
        logger.info(f"GitHub Actions workflow file created: {workflow_file}")
        return 0
    
    # Determine which tests to run
    categories = []
    
    if args.all:
        categories = ['all']
    elif args.core:
        categories = ['core']
    elif args.advanced:
        categories = ['advanced']
    elif args.categories:
        categories = args.categories
    else:
        # Default to unit tests
        categories = ['unit']
    
    # Run the tests
    success = run_self_tests(
        categories=categories,
        include_integration=args.integration,
        include_server=args.server
    )
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
