# LLM Chat Endpoint with Internet Access

This Python project focuses on creating an API endpoint that:

1. Searches Google for information
2. Scrapes the results
3. Processes the pages for RAG
4. Uses an LLM to generate an answer
5. and returns the response.

## Notes:

### Messages

- Most of the core function have been written to be LLM independent.
- The core uses `BaseMessageLog` and `BaseMessage` to pass around messages and roles.
- Only the Gemini module uses Gemini-specific formats.
- You can replace the Gemini-specific formats with OpenAI chat format and the core should still work.

### Working Mode

- By default, the Dockerfile sets the app to be in low-memory mode.
- This mode will not use JavaScript rendering to load pages.
- The performance is decent, but if you wish to increase the number of pages scraped, set the `WORKING_MODE` env to anything other than `low-mem`.

## How to Use

1. Clone the project repository to your local machine
2. Run `docker build -t serp_rag:latest .`
3. Launch a container with `docker run -p 8080:8000 --name serp_rag_con -e GOOGLE_GEMINI_KEY="YOUR GEMINI KEY" serp_rag:latest`
4. Load up `https://localhost:8080/docs` and try the API.
