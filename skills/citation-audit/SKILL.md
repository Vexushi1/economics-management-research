# Phase 8 — Citation audit

Use `CitationRecord` and `check_claim_evidence`. DOI syntax or metadata verification is not semantic support. Verify title, authors, year, journal, DOI identity and current correction/retraction status from authoritative sources **outside** the offline executor; mark unverified when unavailable.

Attach each textual claim to exactly one audited claim ID/reference key and recorded source locator, then independently compare the precise claim with what the source actually supports. A `CLAIM_UNSUPPORTED` verdict must block G6 even if the DOI exists. `NOT_VERIFIED` also blocks. A claim auditor cannot infer contradiction by DOI string alone and cannot forge an external source review. Duplicate DOIs, absent keys, uncertain retraction status, unsupported claims and unverified DOI metadata do not get silently repaired.

No real source PDF is committed to this public project. Templates include no fictitious BibTeX entries.
