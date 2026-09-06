# tree-sitter-parser-ndk

Prebuilt tree-sitter grammar parsers for Android, distributed via GitHub Releases for runtime dynamic loading (`dlopen`).

Each grammar's C source (`src/parser.c` + optional `src/scanner.c`) is compiled with the NDK clang into a shared library exporting the `tree_sitter_<lang>` symbol — not via a Rust `cdylib`, which would hide the C symbol behind its export list.

## Layout

- `grammars.json` — grammar config: repo + pinned tag + list of libs (symbol, source dir).
- `scripts/build.py` — clones grammars, compiles each lib for 4 ABIs via NDK clang, emits `dist/manifest.json` (sha256 + download URLs).
- `.github/workflows/build.yml` — builds on tag push / manual dispatch, publishes `.so` files + `manifest.json` to a GitHub Release.

## ABIs

`arm64-v8a`, `armeabi-v7a`, `x86_64`, `x86` (NDK API 26, NDK 27.1.12297006).

## Manifest

`dist/manifest.json` maps each grammar's libs to per-ABI `{url, sha256, size}`; the app downloads the matching ABI, verifies the sha256, and `dlopen`s it.

## Adding a grammar

Append an entry to `grammars.json` (e.g. from the [List of parsers](https://github.com/tree-sitter/tree-sitter/wiki/List-of-parsers)), pin a tag, and run the workflow.
