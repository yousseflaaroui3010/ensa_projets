## Bug Log

### BUG-005 — AI Answer Vanishes After Streaming Completes (2026-05-04)
**Error:** After the AI finishes streaming its answer on `SearchResults`, the text immediately disappears, leaving a blank card.
**Root cause:** `fetchResults` `onDone` callback created `full: AIResponse = { answer: '', ... }` and spread it onto prev state with `setData((prev) => ({ ...prev, ...full }))`. Spreading `answer: ''` overwrote the accumulated streamed text. Display condition `{data && data.answer && (...)}` then hid the card.
**Fix:** `src/pages/SearchResults.tsx:94` — removed `answer` from the `full` metadata object entirely; `setData` now only spreads `sources/isnad/matn/authenticity/responseId` so `prev.answer` is preserved.
**Status:** FIXED

### BUG-006 — PDF Pipeline Ingests Page-Number Strings Instead of Book Text (2026-05-04)
**Error:** Uploaded PDFs produce chunks like "1 of 30 -- 2 of 30 --" instead of Arabic book content. Vector DB embeds garbage data, breaking all search.
**Root cause (primary):** OCR service (Marker/Python at port 8001) is not running in dev. `lib/pipeline.ts` falls back to `pdf-parse`, which on Arabic classical PDFs extracts only page annotation metadata, not body text.
**Root cause (secondary):** No post-processing filter to strip page-number artifacts before chunking.
**Fix 1:** `lib/pipeline.ts` — added `cleanExtractedText()` function that strips `\bN of M\b` patterns and page-label lines before chunking.
**Fix 2:** `lib/pipeline.ts` — `runIngestPipeline` now checks OCR health (3s timeout) before extraction; if unavailable for a PDF, emits a `warning` field in the SSE progress event.
**Fix 3:** `src/pages/Admin.tsx` — renders amber warning banner when pipeline emits `warning` field. Includes start instructions for OCR service.
**Status:** FIXED (artifact filter) / MITIGATED (OCR must be started separately)

### BUG-002 — RLHF Feedback Silently 401s (2026-05-04)
**Error:** Every RLHF button click returns 401; no feedback ever stored in SQLite.  
**Root causes (2):**
1. `RLHFBar.tsx` sent no `Authorization` header — `requireAuth` middleware rejected all requests.
2. `rlhf_feedback.rating` CHECK constraint only allowed `thumbs_up|thumbs_down|retry`; `mark_correct` and `mark_incorrect` would have failed the DB constraint even if auth passed.  
**Fix:** `lib/db.ts` — migration drops old table and recreates with expanded CHECK; `components/RLHFBar.tsx` — imports `useStore`, reads token, adds `Authorization: Bearer <token>` + passes `answer` field.  
**Status:** FIXED

### BUG-003 — Source "Page" Field Shows Author Name (2026-05-04)
**Error:** Sources panel showed e.g. "Imam Al-Bukhari (256 AH)" in the page slot — semantically wrong, breaks deep-linking.  
**Root cause:** `vectorSearch()` set `page` to `` `${p['author']}${hijriYear}` `` instead of the chunk index.  
**Fix:** `server.ts:474` — changed to `` `p. ${Number(p['chunkIndex'] ?? 0) + 1}` ``. Also fixed keyword fallback on line ~518.  
**Status:** FIXED

### BUG-004 — Admin-Uploaded Books Never Visible in Library (2026-05-04)
**Error:** Books uploaded via `/api/upload` indexed in Qdrant with `bookId=upload_${id}` but `/api/books` only returned static `LIBRARY` array. Uploaded books invisible everywhere; citations led to 404.  
**Root cause:** `/api/books` and `/api/books/:id` never queried the `uploads` SQLite table.  
**Fix:** `server.ts` — added `uploadedBooksFromDb()` helper; `/api/books` merges static + DB; `/api/books/:id` falls back to uploads table for `upload_*` ids.  
**Status:** FIXED

### BUG-001 — pdf-parse not a function (2026-05-04)
**Error:** `TypeError: pdfParse is not a function` at `lib/pipeline.ts:31`  
**Root cause:** `pdf-parse@2.4.5` changed API from default function export to named exports `{ PDFParse, ... }`. Previous fix assumed `.default` fallback which also doesn't exist in v2.x.  
**Diagnosis:** `node --input-type=module` inspection showed `createRequire('pdf-parse')` returns an object with keys `[PDFParse, AbortException, FormatError, ...]` — no default, not a function.  
**Fix:** `lib/pipeline.ts` lines 7-9 — fallback chain `_pdfMod.PDFParse ?? (typeof _pdfMod === 'function' ? _pdfMod : _pdfMod.default)` covers v2.x named export + v1.x default + edge case.  
**Status:** FIXED