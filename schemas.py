"""Tool schemas for the native_extract plugin."""

NATIVE_EXTRACT_SCHEMA = {
    "name": "native_extract",
    "description": (
        "Extract content from web pages using native HTTP requests. "
        "Converts HTML to markdown using html-to-markdown library. "
        "No API key required. "
        "Use this as a fallback when other extraction backends are unavailable "
        "or for simple content extraction tasks."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of URLs to extract content from (max 5 URLs per call)",
                "maxItems": 5,
            },
        },
        "required": ["urls"],
    },
}
