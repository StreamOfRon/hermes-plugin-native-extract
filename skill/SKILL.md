---
name: native-extract
description: Extract content from web pages using native HTTP requests — no API key required
author: Your Name
version: 0.1.0
tags:
  - web
  - extraction
  - http
  - markdown
requires_tools:
  - native_extract
provides_commands:
  - /native-extract
---

## When to Use

- The user asks to extract, summarize, or analyze content from specific URLs
- Other extraction tools are unavailable or fail
- The user wants a no-API-key-required fallback for web content extraction
- Quick content extraction from public web pages

## Procedure

1. Call `native_extract` with the `urls` parameter (array of URLs, max 5)
2. Review the extracted markdown content
3. If the user asked for a summary, summarize the content
4. If extraction fails for some URLs, report which failed and why
5. For large content, focus on the most relevant sections

## Pitfalls

- **Max 5 URLs per call** — if the user provides more, process in batches
- **No JavaScript rendering** — this tool fetches raw HTML/JSON. SPA content may be incomplete
- **html-to-markdown required** — if not installed, the tool returns an error
- **SSL errors** — may occur on some Python installations; suggest `pip install certifi`
- **Rate limiting** — some sites may block or rate-limit automated requests
- **Authentication required** — this tool cannot access pages requiring login
- **No retry logic** — transient failures are reported as errors; the user can retry

## Verification

- Extracted content should be readable markdown
- Each result includes `url`, `title`, `content`, and `error` fields
- If `error` is not null, the extraction failed for that URL
- Verify extracted content matches the expected page content
