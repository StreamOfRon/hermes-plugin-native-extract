"""Tool handlers for the native_extract plugin."""

import json
import logging

logger = logging.getLogger(__name__)


def native_extract_handler(args: dict, **kwargs) -> str:
    """Extract web page content using native HTTP requests.

    Uses requests library to fetch content and html-to-markdown to convert
    HTML to markdown.

    Handler contract:
    1. Receive args (dict) — the parameters the LLM passed
    2. Do the work
    3. Return a JSON string — ALWAYS, even on error
    4. Accept **kwargs for forward compatibility
    """
    try:
        import requests
    except ImportError:
        return json.dumps({
            "error": "The 'requests' library is required but not installed. Run: pip install requests"
        })

    try:
        import html_to_markdown
    except ImportError:
        return json.dumps({
            "error": "The 'html-to-markdown' library is required but not installed. Run: pip install html-to-markdown"
        })

    if not isinstance(args, dict):
        return json.dumps({"error": "Invalid arguments"})

    urls = args.get("urls", [])
    if not isinstance(urls, list):
        return json.dumps({"error": "'urls' must be a list"})
    if not urls:
        return json.dumps({"error": "No URLs provided"})

    results = []
    for url in urls[:5]:  # Max 5 URLs
        try:
            session = requests.Session()
            try:
                import certifi as _certifi
                session.verify = _certifi.where()
            except ImportError:
                pass  # requests defaults to its own bundle

            resp = session.get(
                url,
                headers={
                    "Accept": "application/json, text/markdown;q=0.9, text/html;q=0.8",
                    "User-Agent": "Mozilla/5.0 (compatible; HermesAgent/1.0)",
                },
                timeout=30,
                allow_redirects=True,
            )
            resp.raise_for_status()
            ct = resp.headers.get("Content-Type", "").lower()

            if "application/json" in ct or "text/markdown" in ct:
                content = resp.text
            else:
                content = html_to_markdown.convert(resp.text)

            results.append({
                "url": url,
                "title": "",
                "content": content,
                "error": None,
            })
        except requests.exceptions.SSLError as e:
            logger.warning("Native extract SSL error for %s: %s", url, e)
            results.append({
                "url": url,
                "title": "",
                "content": "",
                "error": (
                    f"SSL certificate verification failed for {url}. "
                    "This may be a Python SSL configuration issue. "
                    f"Details: {e}"
                ),
            })
        except Exception as e:
            logger.warning("Native extract failed for %s: %s", url, e)
            results.append({
                "url": url,
                "title": "",
                "content": "",
                "error": str(e),
            })

    return json.dumps({"success": True, "data": results}, ensure_ascii=False)
