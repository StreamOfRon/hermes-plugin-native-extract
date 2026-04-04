"""Tool handler implementations for the example plugin.

Each handler must follow the contract:
    def handler(args: dict, **kwargs) -> str

- `args` is a dict of parsed input parameters
- Must return a JSON-encoded string (use json.dumps)
- Must not raise exceptions; catch and return error JSON instead
- Accept **kwargs for forward compatibility
"""

import json


def example_tool_handler(args: dict, **kwargs) -> str:
    """Example tool handler that processes a message.

    Args:
        args: Dict with keys matching the schema parameters.
        **kwargs: Additional context (e.g., plugin context, logger).

    Returns:
        JSON-encoded string with the result or error.
    """
    try:
        message = args.get("message", "")
        verbose = args.get("verbose", False)

        result = {
            "status": "success",
            "message": message,
            "length": len(message),
        }

        if verbose:
            result["details"] = {
                "processed_by": "example_tool",
                "kwargs_keys": list(kwargs.keys()),
            }

        return json.dumps(result)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
        })
