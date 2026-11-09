# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-09

### Added

- Dependency-free Okapi BM25 index with `index` / `search` API (`BM25`) and Turkish-named
  aliases (`BM25Indeks`, `indeksle`, `ara`).
- Turkish-aware text pipeline: correct `İ`/`ı` lowercasing, NFC normalization, removal of
  invisible characters, tokenization and stopword filtering that keeps negation words.
- Optional pure-Python stemmer (`KokBulucu`) with a plug-in hook for external stemmers such
  as PyStemmer, applied after stopword filtering.
- ASCII tolerance layer: a secondary folded key lets queries typed without Turkish letters
  match documents that contain them.
- `tr-bm25` command line tool with `ara` (search) and `jetonla` (tokenize) subcommands and
  JSON output.
- English and Turkish documentation (`README.md`, `README.tr.md`).

[Unreleased]: https://github.com/YusufBeratZengin/tr-bm25/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/YusufBeratZengin/tr-bm25/releases/tag/v0.1.0
