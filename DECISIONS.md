# DECISIONS.md — Architecture Decision Record

Running log of every meaningful choice made during the build.
Written *as decisions are made* (not retrospectively) so it doubles as interview prep.

---

## Phase 1 — Scaffolding

### D1: pgvector over a dedicated vector database (Pinecone, Weaviate, Qdrant)
**Decision:** Store embeddings in PostgreSQL using the `pgvector` extension.
**Reason:** We already need a relational DB for document metadata and audit logs. Adding a second data store (a dedicated vector DB) doubles operational complexity — two services to deploy, two connection strings to manage, two backup strategies. pgvector handles 1M+ vectors comfortably on a single node, which is orders of magnitude beyond our corpus size. The tradeoff is that a dedicated vector DB would give us advanced features (namespacing, payload filtering, HNSW tuning) out of the box, but we don't need any of those at this scale.

### D2: RRF over weighted score blending for hybrid retrieval
**Decision:** Use Reciprocal Rank Fusion (RRF) to combine dense and BM25 rankings.
**Reason:** Score blending (e.g., 0.7 × cosine + 0.3 × BM25) requires careful cross-modal score normalization — cosine similarity and BM25 scores live on completely different scales. RRF sidesteps this by operating on *ranks* rather than raw scores, which makes it robust to outlier scores and requires only one tunable parameter (the constant k, usually 60). It also has strong empirical backing in the IR literature. The tradeoff: it discards the magnitude of individual scores, which could lose signal when one retriever is overwhelmingly confident.

### D3: GPT-4o-mini over GPT-4o for generation
**Decision:** Use `gpt-4o-mini` as the generation model.
**Reason:** For retrieval-grounded answers, the bottleneck is retrieval quality, not generation sophistication — the model's main job is to synthesize provided chunks, not to recall facts. GPT-4o-mini is 10–15× cheaper and fast enough to stay under our 5-second latency target. We'd upgrade to GPT-4o only if we found that summarization quality (not factual accuracy, which is governed by retrieval) was visibly poor.

### D4: No Celery/Redis for ingestion
**Decision:** Ingestion runs as a synchronous CLI script, not a background task queue.
**Reason:** Our corpus is 20–30 PDFs, ingested once. A task queue adds a Redis service, worker process management, and retry logic — real complexity for a one-time batch job. If the corpus grew to thousands of documents ingested daily, Celery would be the right call.

### D5: Manual Terraform apply, no CI auto-deploy
**Decision:** `terraform apply` is run manually from a local machine; CI does not automate it.
**Reason:** For a single-environment, single-VM student project, an auto-apply pipeline adds risk (accidental infrastructure changes from a bad merge) without adding meaningful value. We get the IaC benefit (reproducible, version-controlled infrastructure) while keeping the apply step as an explicit human decision. This is also worth saying plainly in an interview rather than pretending we have a full GitOps pipeline.

## Phase 3 — Ingestion Pipeline

### D6: Split each PDF page independently
**Decision:** Recursive token-aware chunks do not cross page boundaries.
**Reason:** Chunks keep a single source page for accurate citations. The small possibility of splitting a clause at a page break is preferable to ambiguous page attribution.

### D7: Synchronous, per-PDF ingestion
**Decision:** The CLI processes PDFs one at a time and commits each PDF with its chunks in one transaction.
**Reason:** This keeps failures isolated and reruns simple for the small manually seeded corpus, without adding a task queue or partial document records.

## Phase 4 — Hybrid Retrieval

### D8: Combine dense and BM25 rankings with RRF
**Decision:** Fuse retriever ranks rather than blending their raw scores.
**Reason:** Cosine similarity and BM25 scores have different scales, while reciprocal rank fusion is straightforward to verify and needs no score normalization.

### D9: Keep the BM25 index in process memory
**Decision:** Load chunk text and metadata into a reusable in-memory BM25 index for retrieval and evaluation.
**Reason:** The expected corpus is small and manually seeded. This avoids a second persistence system; index rebuilding after ingestion is acceptable at this project scale.
