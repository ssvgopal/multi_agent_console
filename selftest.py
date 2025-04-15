"""Self-test script for MultiAgentConsole features."""

import os
import sys
import unittest
import argparse
import logging
import requests
import time
import subprocess
import signal
import psutil
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define test categories
TEST_CATEGORIES = {
    'unit': ['tests/test_*.py'],
    'mode_selection': ['tests/test_mode_selection.py'],
    'security': ['tests/test_web_server.py'],
    'performance': ['tests/test_monitoring.py'],
    'plugins': ['tests/test_plugin.py'],
    'marketplace': ['tests/test_agent_marketplace.py'],
    'all': ['tests/test_*.py']
}

def run_unittest(test_path):
    """Run a unittest file."""
    logger.info(f"Running unittest: {test_path}")
    result = subprocess.run([sys.executable, '-m', 'unittest', test_path],
                           capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def run_integration_test(mode, port=8099):
    """Run an integration test for a specific mode."""
    logger.info(f"Running integration test for mode: {mode}")

    # Start the server in the background
    server_process = subprocess.Popen(
        [sys.executable, '-m', 'multi_agent_console', '--web',
         f'--port={port}', f'--mode={mode}', '--debug'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for the server to start
    time.sleep(10)  # Increased wait time to ensure server is ready

    try:
        # Test the server with retries
        max_retries = 3
        retry_delay = 5
        success = False

        for attempt in range(max_retries):
            try:
                # Test the server
                response = requests.get(f'http://localhost:{port}/', timeout=10)

                # For multi-user mode, we should be redirected to login
                if mode == 'multi-user':
                    success = response.status_code == 303 and '/login' in response.headers.get('Location', '')
                    if success:
                        logger.info(f"Multi-user mode test passed: Redirected to login page")
                    else:
                        logger.error(f"Multi-user mode test failed: Not redirected to login page")

                # For single-user mode, we should get the main page directly
                else:
                    success = response.status_code == 200
                    if success:
                        logger.info(f"Single-user mode test passed: Direct access to main page")
                    else:
                        logger.error(f"Single-user mode test failed: Could not access main page")

                break  # Exit the retry loop if successful

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Connection attempt {attempt+1} failed: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"All connection attempts failed: {e}")
                    success = False

        return success

    except Exception as e:
        logger.error(f"Error during integration test: {e}")
        return False

    finally:
        # Kill the server process and all its children
        try:
            parent = psutil.Process(server_process.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
        except:
            # If we can't terminate gracefully, force kill
            if server_process.poll() is None:
                os.kill(server_process.pid, signal.SIGTERM)

def run_self_tests(categories=None, args=None):
    """Run self-tests for the specified categories."""
    if categories is None:
        categories = ['all']

    # Use default args if not provided
    if args is None:
        class DefaultArgs:
            integration = False
        args = DefaultArgs()

    test_files = []
    for category in categories:
        if category in TEST_CATEGORIES:
            for pattern in TEST_CATEGORIES[category]:
                import glob
                files = glob.glob(pattern)
                test_files.extend(files)

    # Remove duplicates
    test_files = list(set(test_files))

    if not test_files:
        logger.error(f"No test files found for categories: {categories}")
        return False

    logger.info(f"Running tests for files: {test_files}")

    # Run unit tests
    with ThreadPoolExecutor(max_workers=min(4, len(test_files))) as executor:
        results = list(executor.map(run_unittest, test_files))

    # Check results
    all_passed = all(result[0] for result in results)

    # Print results
    for i, (passed, stdout, stderr) in enumerate(results):
        if passed:
            logger.info(f"Test {test_files[i]} passed")
        else:
            logger.error(f"Test {test_files[i]} failed")
            logger.error(f"Stdout: {stdout}")
            logger.error(f"Stderr: {stderr}")

    # Run integration tests if mode_selection is in categories and --integration flag is set
    if ('mode_selection' in categories or 'all' in categories) and args.integration:
        logger.info("Running integration tests...")
        # Test multi-user mode
        multi_user_passed = run_integration_test('multi-user', port=8099)

        # Test single-user mode
        single_user_passed = run_integration_test('single-user', port=8098)

        all_passed = all_passed and multi_user_passed and single_user_passed
    else:
        logger.info("Skipping integration tests. Use --integration flag to run them.")
        # Consider integration tests passed if not running them
        multi_user_passed = True
        single_user_passed = True

    return all_passed

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run self-tests for MultiAgentConsole')
    parser.add_argument('--categories', nargs='+', choices=list(TEST_CATEGORIES.keys()),
                        default=['all'], help='Test categories to run')
    parser.add_argument('--integration', action='store_true',
                        help='Run integration tests (requires server startup)')

    args = parser.parse_args()

    success = run_self_tests(args.categories, args)

    if success:
        logger.info("All tests passed!")
        sys.exit(0)
    else:
        logger.error("Some tests failed!")
        sys.exit(1)
