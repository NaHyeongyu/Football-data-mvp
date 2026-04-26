CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS football.assistant_documents (
    document_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_uri TEXT NOT NULL,
    title TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (source_type, source_uri)
);

CREATE TABLE IF NOT EXISTS football.assistant_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES football.assistant_documents(document_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    chunk_text TEXT NOT NULL,
    token_estimate INTEGER NOT NULL DEFAULT 0 CHECK (token_estimate >= 0),
    embedding vector,
    embedding_provider TEXT,
    embedding_model TEXT,
    embedding_dimension INTEGER CHECK (embedding_dimension IS NULL OR embedding_dimension > 0),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('simple', COALESCE(chunk_text, ''))) STORED,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_assistant_documents_source
    ON football.assistant_documents(source_type, source_uri);

CREATE INDEX IF NOT EXISTS idx_assistant_chunks_document_id
    ON football.assistant_chunks(document_id);

CREATE INDEX IF NOT EXISTS idx_assistant_chunks_embedding_model
    ON football.assistant_chunks(embedding_provider, embedding_model, embedding_dimension)
    WHERE embedding IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_assistant_chunks_search_vector
    ON football.assistant_chunks USING GIN(search_vector);
