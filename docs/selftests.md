# Selftests for MultiAgentConsole

This document explains how to use the selftest framework for MultiAgentConsole. The framework provides a comprehensive way to run tests for all features of the application.

## Overview

The selftest framework consists of the following components:

1. **selftest_framework.py**: The core framework that provides functions for running tests and generating reports.
2. **run_selftests.py**: A simple wrapper script that provides a convenient command-line interface.
3. **tests/**: Directory containing unit tests for individual features.
4. **tests/integration/**: Directory containing integration tests that test multiple components together.
5. **.github/workflows/selftests.yml**: GitHub Actions workflow file for running selftests on pull requests.

## Running Selftests

You can run selftests using the `run_selftests.py` script. Here are some examples:

```bash
# Run all unit tests
python run_selftests.py --categories unit

# Run tests for specific features
python run_selftests.py --categories auth workflow

# Run all core feature tests
python run_selftests.py --core

# Run all advanced feature tests
python run_selftests.py --advanced

# Run all tests (unit and integration)
python run_selftests.py --all --integration

# Include server tests (starts and tests the server)
python run_selftests.py --categories web_server --server

# List available test categories
python run_selftests.py --list

# Generate a test report
python run_selftests.py --all --report test-report.json

# Create a GitHub Actions workflow file
python run_selftests.py --github-action
```

## Test Categories

The selftest framework organizes tests into categories. Here are the main categories:

- **unit**: All unit tests
- **integration**: All integration tests
- **core**: Core feature tests (mode_selection, web_server, auth, cache)
- **advanced**: Advanced feature tests (multi_modal, workflow, offline, debugging)
- **all**: All tests

Feature-specific categories:

- **mode_selection**: Tests for the mode selection feature
- **web_server**: Tests for the web server
- **auth**: Tests for the authentication system
- **cache**: Tests for the cache system
- **multi_modal**: Tests for multi-modal support
- **workflow**: Tests for workflow features
- **offline**: Tests for offline capabilities
- **debugging**: Tests for debugging and monitoring
- **marketplace**: Tests for the agent marketplace
- **plugins**: Tests for plugin support
- **mcp_server**: Tests for the MCP server
- **a2a**: Tests for A2A protocol support
- **security**: Tests for security enhancements
- **ui**: Tests for UI enhancements
- **thought_graph**: Tests for thought graph analysis
- **memory**: Tests for memory management
- **optimization**: Tests for optimization features

## Adding New Tests

To add tests for a new feature:

1. Create a test file in the `tests/` directory with a name like `test_feature_name.py`.
2. Implement test cases using the `unittest` framework.
3. Run the tests using the selftest framework.

Example test file structure:

```python
"""Test the feature_name module."""

import unittest
from unittest.mock import patch, MagicMock

from multi_agent_console.feature_name import FeatureClass

class TestFeatureClass(unittest.TestCase):
    """Test the FeatureClass class."""

    def setUp(self):
        """Set up the test environment."""
        self.feature = FeatureClass()

    def test_method(self):
        """Test a method of the feature."""
        result = self.feature.method()
        self.assertEqual(result, expected_result)

if __name__ == "__main__":
    unittest.main()
```

## Continuous Integration

The selftest framework includes a GitHub Actions workflow file that runs selftests on pull requests and pushes to the main branch. The workflow:

1. Runs all unit tests
2. Runs core feature tests
3. Generates a test report
4. Uploads the test report as an artifact

You can view the test results in the GitHub Actions tab of the repository.

## Best Practices

- Write tests for all new features
- Run selftests before submitting a pull request
- Keep tests focused and independent
- Use mocks for external dependencies
- Include both positive and negative test cases
- Document test cases with clear docstrings

## Troubleshooting

If you encounter issues with the selftest framework:

- Check that all dependencies are installed
- Verify that the test files are in the correct directory
- Ensure that test file names follow the convention `test_*.py`
- Check for syntax errors in test files
- Run individual test files directly using `python -m unittest tests/test_file.py`
