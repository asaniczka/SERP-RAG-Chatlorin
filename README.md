# Google Search API Endpoint

This Python project focuses on creating an API endpoint that searches Google for a given query, scrapes the top 10 results, generates embeddings for RAG, uses OpenAI to generate an answer, and returns the response.

## Task description

- Create an API endpoint for searching Google with a given query
- Scrape the top 10 search results
- Generate embeddings for RAG
- Use OpenAI to generate an answer using the embeddings
- Return the response with the answer

## Notes:

### Messages

- Most of the LLM Messages have been written to be LLM independant.
- The core uses `BaseMessageLog` and `BaseMessage` to pass around messages and roles.
- Only the gemini module uses gemini specific formats.
- You can replace the gemini specific formats with OpenAI chat format and the core should still work.

## Working Mode

- By default, Dockerfile sets the app to be in low-memory mode.
- This mode will not use js rendering to load pages.
- The performance is decent, but if you wish to increase the num of pages scraped, set the `WORKING_MODE` env to anything other than `low-mem`.

## How to Use

1. Clone the project repository to your local machine
2. Run `docker build -t serp_rag:latest .`
3. Launch a container with `docker run -p 8080:8000 --name serp_rag_con -e GOOGLE_GEMINI_KEY="YOUR GEMIMI KEY" serp_rag:latest`
4. Load up `https://localhost:8080/docs` and try the api.
