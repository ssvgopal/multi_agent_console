#!/usr/bin/env python
"""
Test runner for MultiAgentConsole.
"""

import os
import sys
import unittest
import argparse
import coverage


def run_tests(test_pattern=None, coverage_report=False):
    """Run the tests."""
    if coverage_report:
        # Start coverage
        cov = coverage.Coverage(
            source=["multi_agent_console"],
            omit=["*/tests/*", "*/venv/*", "*/site-packages/*"]
        )
        cov.start()
    
    # Discover and run tests
    loader = unittest.TestLoader()
    
    if test_pattern:
        # Run specific tests
        test_suite = loader.loadTestsFromName(test_pattern)
    else:
        # Run all tests
        start_dir = os.path.join(os.path.dirname(__file__), "tests")
        test_suite = loader.discover(start_dir)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    if coverage_report:
        # Stop coverage and generate report
        cov.stop()
        cov.save()
        
        print("\nCoverage Report:")
        cov.report()
        
        # Generate HTML report
        html_dir = os.path.join(os.path.dirname(__file__), "coverage_html")
        cov.html_report(directory=html_dir)
        print(f"HTML report generated in {html_dir}")
    
    return result.wasSuccessful()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run MultiAgentConsole tests")
    parser.add_argument(
        "--test", "-t",
        help="Run a specific test (e.g., 'tests.test_plugin')"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    
    args = parser.parse_args()
    
    success = run_tests(args.test, args.coverage)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
