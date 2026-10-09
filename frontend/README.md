# Finance RAG frontend

React, TypeScript, and Vite interface for querying the Finance RAG API and
browsing indexed RBI and SEBI documents.

## Local development

From this directory:

```powershell
npm ci
npm run dev
```

The API defaults to `http://localhost:8000`. To use another backend, create a
frontend `.env.local` file and set:

```dotenv
VITE_API_URL=http://localhost:8000
```

Restart Vite after changing the variable. The API must allow the frontend
origin in its CORS configuration.

## Features

- Submit regulatory questions with regulator and document-type filters.
- View grounded answers and navigate from inline source markers to citations.
- Expand a citation to inspect its indexed excerpt and page number.
- Browse and filter the indexed document library, paginate results, and view
  document metadata and indexed passage counts.
- See loading, empty, low-confidence, and API-error states.

The document API currently returns metadata and chunk counts, not downloadable
PDF files. Source excerpts shown with citations are the excerpts returned by
the query API.

## Local checks

```powershell
npm run lint
npm run build
```
