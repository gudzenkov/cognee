# Native Citations for Chunk-Backed Search

## Summary

Add native `path:file:loc` citations to chunk-backed retrieval without adding new endpoints.

Scope for this implementation:
- cover `CHUNKS` and `RAG_COMPLETION`
- expose citations only in verbose/raw modes
- update API and CLI now
- defer MCP for a follow-up

Hard truth:
- Cognee already keeps source provenance at ingest (`original_data_location` / `raw_data_location`)
- citations are missing because chunk line spans are never stamped, and vector indexing strips chunk provenance down to text/id only
- exact `file:line` is not recoverable reliably from current indexed payloads, so this must be added during chunking/indexing and existing datasets must be re-cognified

## Key Changes

### 1. Stamp citation provenance onto `DocumentChunk`

Extend the document/chunk lineage so chunk objects carry citation fields:
- `source_uri: str | None`
- `line_start: int | None`
- `line_end: int | None`

In document classification, carry both:
- `original_data_location` as the canonical citation source when present
- fallback to `raw_data_location` otherwise

For text-backed chunkers:
- compute chunk start/end offsets during chunk construction
- derive `line_start` / `line_end` from the source text at chunking time

For non-text or transformed sources where original line mapping is not trustworthy:
- keep `source_uri`
- leave `line_start` / `line_end` null

Implementation choice:
- `TextChunker` and `TextChunkerWithOverlap` should use offset-aware paragraph/sentence chunking
- `LangchainChunker` should derive offsets from splitter output and compute line spans from source text
- `CsvChunker`, OCR/audio/unstructured flows should return path-only citations for now

### 2. Preserve provenance in vector payloads

Replace the current stripped chunk payload shape with an additive one for `DocumentChunk_text` indexing.

Extend vector `IndexSchema` to carry optional citation fields:
- `source_uri`
- `line_start`
- `line_end`
- `chunk_index`

Update `index_data_points()` so `DocumentChunk` payloads include those citation fields in all supported vector adapters.

Keep existing payload keys intact; this is additive, not a breaking schema rewrite.

Implementation choice:
- do not hydrate citations later from grep/DB joins in the normal retrieval path
- the retrievers should get citation-ready payloads directly from vector search

### 3. Add citations to verbose search results

Keep existing search behavior unchanged when `verbose=false`.

When `verbose=true`, add a new `citations` field to each verbose result for `CHUNKS` and `RAG_COMPLETION`.

Citation shape:

```json
{
  "source": "file:///abs/path/or/original/source",
  "line_start": 12,
  "line_end": 26,
  "chunk_id": "..."
}
```

Build `citations` from `objects_result`, deduped by `(source, line_start, line_end, chunk_id)`.

Preserve current fields:
- `text_result`
- `context_result`
- `objects_result`
- dataset wrapper fields when access control is enabled

Implementation choice:
- use `original_data_location` as `source` when available
- keep API payload as stored URI/string
- CLI may render `file://` sources as plain filesystem paths for readability, but the API contract should not rewrite them

### 4. Expose verbose citations in CLI

Add `--verbose` to `cognee-cli search`.

In in-process and `--api-url` modes, pass `verbose=true`.

CLI formatting:
- `RAG_COMPLETION --verbose`: print answer, then a `Citations` block with `[n] path:start-end`
- `CHUNKS --verbose`: print each chunk plus its citation line
- `--output-format json`: emit the full verbose payload including `citations`

Do not change default non-verbose CLI output.

### 5. Defer MCP cleanly

Do not implement MCP citation exposure in this change.

After API/CLI land, MCP can reuse the same citation payload and either:
- add a `verbose` parameter to `search`, or
- append a human-readable citations block to text output

Keep MCP out of the first implementation to avoid mixing wire-shape work with provenance plumbing.

## Important Interface Changes

- `cognee.search(..., verbose=True)` for `CHUNKS` / `RAG_COMPLETION` returns additive `citations`
- `POST /api/v1/search` with `verbose=true` returns additive `citations` for those search types
- `cognee-cli search` gains `--verbose`
- No new endpoint
- No citation fields in non-verbose responses
- No v1 citation guarantee for `GRAPH_COMPLETION`, `CODE`, `SUMMARIES`, or MCP

## Test Plan

### Unit and contract tests

- chunkers stamp correct `source_uri`, `line_start`, `line_end` for plain text inputs
- transformed/non-text documents keep `source_uri` and null line spans
- vector index payload for `DocumentChunk_text` contains citation fields
- verbose search result contract includes `citations`
- non-verbose search output remains unchanged
- access-control-on mode still wraps dataset info and includes citations in verbose mode

### Integration tests

- ingest + cognify a markdown file with known line numbers, then:
  - `CHUNKS verbose` returns correct file path and line span
  - `RAG_COMPLETION verbose` returns answer plus citations pointing to the same source spans
- API-dispatch CLI search with `--api-url` behaves the same as in-process search
- duplicate chunk hits from the same file are deduped in `citations`

### E2E/manual validation

- local dataset with a simple markdown file:
  - `cognee-cli search -t CHUNKS --verbose ...`
  - `cognee-cli search -t RAG_COMPLETION --verbose ...`
  - `POST /api/v1/search` with `verbose=true`
- verify cited path uses `original_data_location` and the rendered `path:start-end` matches the actual file contents

## Assumptions

- `CHUNKS` and `RAG_COMPLETION` are the only first-pass search types that must emit citations
- `verbose-only` is the exposure policy for now
- `original_data_location` is the canonical citation source when present; otherwise use `raw_data_location`
- existing datasets will need re-cognify to populate citation metadata in vector payloads
- MCP citation support is intentionally deferred in this plan
