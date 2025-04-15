"""
Selftest Framework for MultiAgentConsole.

This module provides a comprehensive framework for running selftests on all features
of the MultiAgentConsole. It can be used to validate functionality during development
and in CI/CD pipelines.
"""

import os
import sys
import unittest
import argparse
import logging
import time
import subprocess
import signal
import json
import glob
import importlib
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define test categories and their corresponding test files
TEST_CATEGORIES = {
    # Test types
    'unit': ['tests/test_*.py'],
    'integration': ['tests/integration/test_*.py'],
    
    # Core features
    'mode_selection': ['tests/test_mode_selection.py'],
    'web_server': ['tests/test_web_server.py'],
    'auth': ['tests/test_auth.py'],
    'cache': ['tests/test_cache.py'],
    
    # Advanced features
    'multi_modal': ['tests/test_multi_modal.py'],
    'workflow': ['tests/test_workflow.py'],
    'offline': ['tests/test_offline.py'],
    'debugging': ['tests/test_debugging.py'],
    'monitoring': ['tests/test_monitoring.py'],
    'marketplace': ['tests/test_agent_marketplace.py', 'tests/test_marketplace.py'],
    'cross_platform': ['tests/test_cross_platform.py'],
    'plugins': ['tests/test_plugin.py'],
    'mcp_server': ['tests/test_mcp_server.py'],
    'a2a': ['tests/test_a2a_adapter.py'],
    'security': ['tests/test_security_enhancements.py', 'tests/test_security_manager.py'],
    'ui': ['tests/test_ui_enhancements.py'],
    'thought_graph': ['tests/test_thought_graph.py'],
    'memory': ['tests/test_memory_manager.py'],
    'optimization': ['tests/test_optimization.py'],
    
    # Feature groups
    'core': ['tests/test_mode_selection.py', 'tests/test_web_server.py', 'tests/test_auth.py', 'tests/test_cache.py'],
    'advanced': ['tests/test_multi_modal.py', 'tests/test_workflow.py', 'tests/test_offline.py', 'tests/test_debugging.py'],
    'security_all': ['tests/test_security_enhancements.py', 'tests/test_security_manager.py', 'tests/test_web_server.py'],
    'plugins_all': ['tests/test_plugin.py', 'tests/test_mcp_server.py'],
    
    # Run all tests
    'all': ['tests/test_*.py', 'tests/integration/test_*.py']
}

def discover_tests() -> Dict[str, List[str]]:
    """Discover all available test files and update the TEST_CATEGORIES dictionary.
    
    Returns:
        Updated TEST_CATEGORIES dictionary
    """
    # Find all test files
    all_test_files = []
    for pattern in ['tests/test_*.py', 'tests/integration/test_*.py']:
        all_test_files.extend(glob.glob(pattern))
    
    # Update the 'all' category
    TEST_CATEGORIES['all'] = sorted(list(set(all_test_files)))
    
    # Update the 'unit' category
    TEST_CATEGORIES['unit'] = sorted(list(set(glob.glob('tests/test_*.py'))))
    
    # Update the 'integration' category
    TEST_CATEGORIES['integration'] = sorted(list(set(glob.glob('tests/integration/test_*.py'))))
    
    # Create categories for each feature based on filename
    for test_file in all_test_files:
        # Extract feature name from filename (e.g., test_auth.py -> auth)
        feature = os.path.basename(test_file).replace('test_', '').replace('.py', '')
        
        # Add or update the category
        if feature not in TEST_CATEGORIES:
            TEST_CATEGORIES[feature] = [test_file]
        elif test_file not in TEST_CATEGORIES[feature]:
            TEST_CATEGORIES[feature].append(test_file)
    
    return TEST_CATEGORIES

def run_unittest(test_path: str) -> Tuple[bool, str, str]:
    """Run a unittest file.
    
    Args:
        test_path: Path to the test file
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    logger.info(f"Running unittest: {test_path}")
    
    # Run the test
    result = subprocess.run(
        [sys.executable, '-m', 'unittest', test_path],
        capture_output=True,
        text=True
    )
    
    # Check if the test passed
    success = result.returncode == 0
    
    # Log the result
    if success:
        logger.info(f"Test {test_path} passed")
    else:
        logger.error(f"Test {test_path} failed")
        logger.error(f"Stdout: {result.stdout}")
        logger.error(f"Stderr: {result.stderr}")
    
    return success, result.stdout, result.stderr

def run_integration_test(test_path: str) -> Tuple[bool, str, str]:
    """Run an integration test.
    
    Args:
        test_path: Path to the test file
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    logger.info(f"Running integration test: {test_path}")
    
    # Run the test with a longer timeout
    result = subprocess.run(
        [sys.executable, '-m', 'unittest', test_path],
        capture_output=True,
        text=True,
        timeout=300  # 5 minutes timeout for integration tests
    )
    
    # Check if the test passed
    success = result.returncode == 0
    
    # Log the result
    if success:
        logger.info(f"Integration test {test_path} passed")
    else:
        logger.error(f"Integration test {test_path} failed")
        logger.error(f"Stdout: {result.stdout}")
        logger.error(f"Stderr: {result.stderr}")
    
    return success, result.stdout, result.stderr

def run_server_test(port: int = 8099, mode: str = "single-user", timeout: int = 30) -> bool:
    """Run a test that starts the server and checks if it's accessible.
    
    Args:
        port: Port to use for the server
        mode: Mode to run the server in (single-user or multi-user)
        timeout: Timeout in seconds
        
    Returns:
        True if the test passed, False otherwise
    """
    import requests
    
    logger.info(f"Running server test in {mode} mode on port {port}")
    
    # Start the server in the background
    server_process = subprocess.Popen(
        [sys.executable, '-m', 'multi_agent_console', '--web', f'--port={port}', f'--mode={mode}', '--debug'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Wait for the server to start
        time.sleep(5)
        
        # Try to connect to the server
        start_time = time.time()
        success = False
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f'http://localhost:{port}/', timeout=5)
                
                # Check if the response is as expected
                if mode == "multi-user":
                    # Should redirect to login page
                    success = response.status_code == 303 and '/login' in response.headers.get('Location', '')
                    if success:
                        logger.info(f"Server test passed: Redirected to login page")
                    else:
                        logger.error(f"Server test failed: Not redirected to login page")
                else:
                    # Should return the main page
                    success = response.status_code == 200
                    if success:
                        logger.info(f"Server test passed: Main page returned")
                    else:
                        logger.error(f"Server test failed: Main page not returned")
                
                break
            except requests.RequestException:
                # Wait and try again
                time.sleep(2)
        
        return success
    
    finally:
        # Kill the server process
        if server_process.poll() is None:
            try:
                import psutil
                parent = psutil.Process(server_process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
            except:
                # If psutil is not available, use os.kill
                if server_process.poll() is None:
                    os.kill(server_process.pid, signal.SIGTERM)

def run_self_tests(categories: List[str] = None, include_integration: bool = False, 
                  include_server: bool = False, max_workers: int = 4) -> bool:
    """Run self-tests for the specified categories.
    
    Args:
        categories: List of test categories to run
        include_integration: Whether to include integration tests
        include_server: Whether to include server tests
        max_workers: Maximum number of worker threads
        
    Returns:
        True if all tests passed, False otherwise
    """
    # Use default categories if none specified
    if categories is None:
        categories = ['unit']
    
    # Discover tests
    discover_tests()
    
    # Get test files for the specified categories
    test_files = []
    for category in categories:
        if category in TEST_CATEGORIES:
            for pattern in TEST_CATEGORIES[category]:
                files = glob.glob(pattern)
                test_files.extend(files)
    
    # Remove duplicates and sort
    test_files = sorted(list(set(test_files)))
    
    # Filter out integration tests if not included
    if not include_integration:
        test_files = [f for f in test_files if 'integration' not in f]
    
    if not test_files:
        logger.error(f"No test files found for categories: {categories}")
        return False
    
    logger.info(f"Running tests for files: {test_files}")
    
    # Run unit tests in parallel
    with ThreadPoolExecutor(max_workers=min(max_workers, len(test_files))) as executor:
        results = list(executor.map(run_unittest, test_files))
    
    # Check if all unit tests passed
    all_passed = all(result[0] for result in results)
    
    # Run server tests if requested
    if include_server and all_passed:
        logger.info("Running server tests...")
        
        # Test single-user mode
        single_user_passed = run_server_test(port=8098, mode="single-user")
        
        # Test multi-user mode
        multi_user_passed = run_server_test(port=8099, mode="multi-user")
        
        # Update overall result
        all_passed = all_passed and single_user_passed and multi_user_passed
    
    # Return the overall result
    if all_passed:
        logger.info("All tests passed!")
    else:
        logger.error("Some tests failed!")
    
    return all_passed

def generate_test_report(results: List[Tuple[str, bool, str, str]]) -> Dict[str, Any]:
    """Generate a test report from the test results.
    
    Args:
        results: List of (test_path, success, stdout, stderr) tuples
        
    Returns:
        Report dictionary
    """
    # Count passed and failed tests
    passed = sum(1 for result in results if result[1])
    failed = len(results) - passed
    
    # Create the report
    report = {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "success_rate": f"{passed / len(results) * 100:.2f}%" if results else "N/A",
        "tests": [
            {
                "path": result[0],
                "success": result[1],
                "stdout": result[2],
                "stderr": result[3]
            }
            for result in results
        ]
    }
    
    return report

def save_test_report(report: Dict[str, Any], output_file: str) -> None:
    """Save a test report to a file.
    
    Args:
        report: Report dictionary
        output_file: Path to the output file
    """
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Test report saved to {output_file}")

def list_available_tests() -> None:
    """List all available test categories and files."""
    # Discover tests
    categories = discover_tests()
    
    # Print categories
    print("Available test categories:")
    for category, files in sorted(categories.items()):
        print(f"  {category}: {len(files)} test(s)")
    
    # Print test files
    print("\nAvailable test files:")
    all_files = set()
    for files in categories.values():
        all_files.update(files)
    
    for file in sorted(all_files):
        print(f"  {file}")

def create_github_action() -> str:
    """Create a GitHub Actions workflow file for running selftests on pull requests.
    
    Returns:
        Path to the created file
    """
    workflow_dir = '.github/workflows'
    os.makedirs(workflow_dir, exist_ok=True)
    
    workflow_file = os.path.join(workflow_dir, 'selftests.yml')
    
    workflow_content = """name: Run Selftests

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    
    - name: Run selftests
      run: |
        python selftest_framework.py --categories unit --report-file test-report.json
    
    - name: Upload test report
      uses: actions/upload-artifact@v2
      with:
        name: test-report
        path: test-report.json
"""
    
    with open(workflow_file, 'w') as f:
        f.write(workflow_content)
    
    return workflow_file

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run self-tests for MultiAgentConsole')
    
    # Test selection options
    parser.add_argument('--categories', nargs='+', help='Test categories to run')
    parser.add_argument('--files', nargs='+', help='Specific test files to run')
    
    # Test execution options
    parser.add_argument('--integration', action='store_true', help='Include integration tests')
    parser.add_argument('--server', action='store_true', help='Include server tests')
    parser.add_argument('--max-workers', type=int, default=4, help='Maximum number of worker threads')
    
    # Output options
    parser.add_argument('--report-file', help='Path to save the test report')
    parser.add_argument('--list', action='store_true', help='List available tests')
    parser.add_argument('--create-github-action', action='store_true', help='Create GitHub Actions workflow file')
    
    args = parser.parse_args()
    
    # List available tests if requested
    if args.list:
        list_available_tests()
        sys.exit(0)
    
    # Create GitHub Actions workflow file if requested
    if args.create_github_action:
        workflow_file = create_github_action()
        logger.info(f"GitHub Actions workflow file created: {workflow_file}")
        sys.exit(0)
    
    # Determine which tests to run
    if args.files:
        # Run specific test files
        test_files = args.files
        success, results = run_specific_tests(test_files, args.max_workers)
    else:
        # Run tests by category
        categories = args.categories or ['unit']
        success = run_self_tests(
            categories=categories,
            include_integration=args.integration,
            include_server=args.server,
            max_workers=args.max_workers
        )
    
    # Save test report if requested
    if args.report_file and 'results' in locals():
        report = generate_test_report(results)
        save_test_report(report, args.report_file)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
