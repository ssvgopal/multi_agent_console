# Mode Selection Feature

The Mode Selection feature allows users to choose between multi-user mode (with authentication) and single-user mode (without authentication) for the web UI.

## Usage

When starting the MultiAgentConsole with the web interface, you can specify the mode using the `--mode` command-line argument:

```bash
# Start in multi-user mode (default)
python -m multi_agent_console --web --mode=multi-user

# Start in single-user mode
python -m multi_agent_console --web --mode=single-user
```

## Modes

### Multi-User Mode

- Authentication is enabled
- Users must log in before accessing the web interface
- Suitable for shared environments where multiple users need to access the system

### Single-User Mode

- Authentication is disabled
- Direct access to the web interface without login
- Suitable for personal use or when running locally

## Backward Compatibility

For backward compatibility, the `--no-auth` flag is still supported:

```bash
# Equivalent to --mode=single-user
python -m multi_agent_console --web --no-auth
```

## Self-Tests

The mode selection feature includes unit tests and integration tests:

- Unit tests: `tests/test_mode_selection.py`
- Self-test script: `selftest.py`

To run the unit tests:

```bash
python -m unittest tests/test_mode_selection.py
```

To run the self-tests:

```bash
# Run unit tests only
python selftest.py --categories mode_selection

# Run unit tests and integration tests
python selftest.py --categories mode_selection --integration
```

## Implementation Details

The mode selection feature is implemented in the following files:

- `multi_agent_console/app.py`: Command-line argument parsing and mode selection
- `multi_agent_console/web_server.py`: Authentication handling based on the selected mode

The implementation ensures that:

1. When in multi-user mode, authentication is enabled and users must log in
2. When in single-user mode, authentication is disabled and users can access the web interface directly
3. The `--no-auth` flag is still supported for backward compatibility
