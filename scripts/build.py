#!/usr/bin/env python3
"""Compile tree-sitter grammar parser.c into Android .so via NDK clang.

For each grammar in grammars.json this clones the grammar repo at a pinned tag
and, for every ABI, compiles src/parser.c (+ src/scanner.c if present) into a
shared library exporting the `tree_sitter_<lang>` symbol. The resulting .so
files are written flat-named under dist/flat/ and a manifest.json with sha256
checksums is emitted under dist/.
"""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NDK = Path(os.environ["ANDROID_NDK_HOME"])
CLANG_DIR = NDK / "toolchains" / "llvm" / "prebuilt" / "linux-x86_64" / "bin"

ABI_TRIPLE = {
    "arm64-v8a": "aarch64-linux-android",
    "armeabi-v7a": "armv7a-linux-androideabi",
    "x86": "i686-linux-android",
    "x86_64": "x86_64-linux-android",
}


def run(cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True)


def main():
    config = json.loads((ROOT / "grammars.json").read_text())
    abis = config["abis"]
    api = config["ndk_api"]
    tag = os.environ.get("RELEASE_TAG", "dev")
    repo = os.environ.get("GITHUB_REPOSITORY", "KylinLee/tree-sitter-parser-ndk")

    dist = ROOT / "dist"
    flat = dist / "flat"
    checkout_root = ROOT / "checkout"
    flat.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema": 1,
        "version": tag,
        "tree_sitter_abi": config["abi"],
        "grammars": {},
    }

    for lang in config["languages"]:
        checkout = checkout_root / lang["id"]
        if not (checkout / ".git").exists():
            run(["git", "clone", "--depth", "1", "--branch", lang["tag"],
                 f"https://github.com/{lang['repo']}.git", str(checkout)])

        lang_manifest = {"libs": []}
        for lib in lang["libs"]:
            src_dir = checkout / lib["dir"]
            lib_manifest = {"name": lib["name"], "symbol": lib["symbol"]}
            for abi in abis:
                clang = CLANG_DIR / f"{ABI_TRIPLE[abi]}{api}-clang"
                out = dist / abi / f"lib{lib['name']}.so"
                out.parent.mkdir(parents=True, exist_ok=True)
                sources = [src_dir / "parser.c"]
                scanner = src_dir / "scanner.c"
                if scanner.exists():
                    sources.append(scanner)
                run([str(clang), "-shared", "-fPIC", "-O2", "-I", str(src_dir),
                     "-o", str(out)] + [str(s) for s in sources])

                asset = f"{lib['name']}.{abi}.so"
                shutil.copyfile(out, flat / asset)
                data = out.read_bytes()
                lib_manifest[abi] = {
                    "url": f"https://github.com/{repo}/releases/download/{tag}/{asset}",
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "size": len(data),
                }
            lang_manifest["libs"].append(lib_manifest)
        manifest["grammars"][lang["id"]] = lang_manifest

    (dist / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
