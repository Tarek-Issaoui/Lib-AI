# Lib-AI

## Library Chatbot

This backend provides a library catalog API and a retrieval-based chatbot powered by Ollama and ChromaDB.

### Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure Ollama is running locally and that your open-source model is available.
   Example environment variable:
   ```bash
   export OLLAMA_MODEL=llama2
   ```

3. Start the FastAPI app:
   ```bash
   uvicorn app.main:app --reload
   ```

### Chatbot API

- `POST /chatbot/index/` — builds the ChromaDB index from the library book records.
- `POST /chatbot/query/` — ask a question about the library.

Example query payload:
```json
{
  "question": "What books do we have by Agatha Christie?"
}
```

### Notes

- The current chatbot indexes book metadata (title, author, year, status, category).
- For richer answers, you can extend the `Livre` model with summaries or full book text.
- The chatbot uses `sentence-transformers` for embeddings and Ollama for text generation.
