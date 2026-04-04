"""Tool schema definitions for the example plugin.

Each schema follows the OpenAI function-calling format.
The schema name should match the entry in plugin.yaml provides_tools.
"""

EXAMPLE_TOOL_SCHEMA = {
    "name": "example_tool",
    "description": (
        "An example tool that demonstrates the Hermes plugin tool contract. "
        "Use this to see how tool schemas are structured and how the LLM "
        "decides when to call your tool based on the description."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "A message to process",
            },
            "verbose": {
                "type": "boolean",
                "description": "Whether to return verbose output",
                "default": False,
            },
        },
        "required": ["message"],
    },
}
