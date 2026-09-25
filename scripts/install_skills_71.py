#!/usr/bin/env python3
"""Install the 71 photo-style skills from skills-manifest.json at pinned commits.

Target: ~/.config/mimocode/skills/<declared_skill_name>/
Source cache: <repo>/.skill-cache/
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

MANIFEST = Path(
    "/Users/tom/Downloads/生图Skill合集-71项/02-给AI看的安装说明书/skills-manifest.json"
)
CACHE = Path("/Users/tom/Desktop/workspace/agnesstudio/.skill-cache")
OUT_ROOT = Path.home() / ".config" / "mimocode" / "skills"
REPORT = CACHE / "install_report.json"
UA = "agnesstudio-skill-installer/1.0 (+local; pinned commit install)"

# License / usage labels applied at install time (from collection docs)
LICENSE_NOTES = {
    "ST09": "Starryear Personal and Non-commercial Use License · 仅个人学习/非商业",
    "ST10": "Starryear Personal and Non-commercial Use License · 仅个人学习/非商业",
    "ST11": "Starryear Personal and Non-commercial Use License · 仅个人学习/非商业",
    "ST12": "Starryear Personal and Non-commercial Use License · 仅个人学习/非商业",
    "ST13": "Starryear Personal and Non-commercial Use License · 仅个人学习/非商业",
    "S28": "上游非商业；商用需作者授权",
    "N32": "MIT · 仅原创角色，不模仿既有动漫IP；保留 system/ 配置",
    "N33": "MIT · 照片留本机不外传；photo-search 为可选依赖",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path, timeout: int = 120) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    dest.write_bytes(data)


def repo_tarball_url(repository: str, commit: str) -> str:
    return f"https://codeload.github.com/{repository}/tar.gz/{commit}"


def raw_url_from_blob(blob_or_raw: str) -> str:
    """Convert github blob/raw URL to raw.githubusercontent.com."""
    u = blob_or_raw
    u = u.replace("https://github.com/", "https://raw.githubusercontent.com/")
    u = u.replace("/blob/", "/")
    return u


def safe_extract_tar(tf: tarfile.TarFile, dest: Path) -> Path:
    """Extract tarball; GitHub archives have a single top-level dir. Return it."""
    dest.mkdir(parents=True, exist_ok=True)
    members = tf.getmembers()
    # reject path escape
    for m in members:
        name = m.name
        if name.startswith("/") or ".." in Path(name).parts:
            raise RuntimeError(f"unsafe tar path: {name}")
    tf.extractall(dest)
    tops = {Path(m.name).parts[0] for m in members if m.name}
    if len(tops) == 1:
        return dest / next(iter(tops))
    return dest


def safe_extract_zip(zf: zipfile.ZipFile, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    for info in zf.infolist():
        name = info.filename
        if name.startswith("/") or ".." in Path(name).parts:
            raise RuntimeError(f"unsafe zip path: {name}")
    zf.extractall(dest)
    tops = {Path(i.filename).parts[0] for i in zf.infolist() if i.filename}
    # if zip root contains the skill dir directly
    return dest


def copy_skill_tree(src_dir: Path, target: Path) -> None:
    if target.exists():
        backup = target.with_name(target.name + f".bak.{int(time.time())}")
        target.rename(backup)
    shutil.copytree(src_dir, target)


def write_meta(target: Path, entry: dict, source_commit: str) -> None:
    lic = LICENSE_NOTES.get(entry["id"]) or entry.get("license_note") or ""
    meta = {
        "collection_id": "image-skills-photo-71",
        "entry_id": entry["id"],
        "display_name": entry.get("display_name"),
        "declared_skill_name": entry.get("declared_skill_name"),
        "repository": entry.get("repository"),
        "verified_ref": source_commit,
        "group": entry.get("group"),
        "license_note": lic,
        "style": entry.get("style"),
        "scope": entry.get("scope"),
        "installed_from_manifest": str(MANIFEST),
        "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (target / "INSTALL_META.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if lic:
        readme = target / "LICENSE_NOTE.md"
        readme.write_text(
            f"# License / Usage\n\n- entry: {entry['id']} {entry.get('display_name')}\n"
            f"- note: {lic}\n"
            f"- source: {entry.get('repository')} @ {source_commit}\n",
            encoding="utf-8",
        )


def verify_skill_md(skill_root: Path, skill_md_rel: str, expected: str) -> tuple[bool, str]:
    p = skill_root / skill_md_rel
    if not p.exists():
        return False, f"missing {skill_md_rel}"
    actual = sha256_file(p)
    if actual != expected:
        return False, f"sha256 mismatch got={actual} want={expected}"
    return True, actual


def install_one(entry: dict) -> dict:
    eid = entry["id"]
    declared = entry["install"]["target_directory_name"]
    kind = entry["install"]["kind"]
    commit = entry.get("verified_ref") or entry.get("evidence", {}).get("commit")
    repo = entry.get("repository")
    result = {
        "id": eid,
        "declared_skill_name": declared,
        "display_name": entry.get("display_name"),
        "group": entry.get("group"),
        "repository": repo,
        "verified_ref": commit,
        "kind": kind,
        "status": "pending",
        "target": str(OUT_ROOT / declared),
        "license_note": LICENSE_NOTES.get(eid) or entry.get("license_note") or "",
    }
    try:
        work = CACHE / "work" / eid
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True, exist_ok=True)

        expected_md = (
            entry["install"].get("skill_md_sha256")
            or (entry.get("evidence") or {}).get("sha256")
        )
        skill_md_rel = entry["install"].get("skill_md_path") or entry["install"].get(
            "skill_path_in_archive"
        )

        if kind in ("zip", "archive"):
            zip_path_key = "zip_path" if kind == "zip" else "archive_path"
            zip_sha_key = "zip_sha256" if kind == "zip" else "archive_sha256"
            zip_name = entry["install"][zip_path_key]
            zip_sha = entry["install"][zip_sha_key]
            # download zip from source_url raw
            src_url = raw_url_from_blob(entry["source_url"])
            zip_local = work / Path(zip_name).name
            fetch(src_url, zip_local)
            got_zip_sha = sha256_file(zip_local)
            if got_zip_sha != zip_sha:
                raise RuntimeError(f"zip sha mismatch got={got_zip_sha} want={zip_sha}")
            extract_root = work / "extracted"
            with zipfile.ZipFile(zip_local) as zf:
                safe_extract_zip(zf, extract_root)
            source_directory = entry["install"]["source_directory"]
            skill_src = extract_root / source_directory
            if not skill_src.exists():
                # maybe zip root is the skill itself
                alt = extract_root / Path(zip_name).stem
                if alt.exists():
                    skill_src = alt
                else:
                    # search
                    candidates = list(extract_root.rglob("SKILL.md"))
                    if not candidates:
                        raise RuntimeError(f"skill dir not found after zip extract: {source_directory}")
                    skill_src = candidates[0].parent
            ok, detail = verify_skill_md(skill_src, "SKILL.md", expected_md)
            if not ok:
                # skill_md_path may be nested
                ok, detail = verify_skill_md(skill_src, skill_md_rel.split("/")[-1], expected_md)
            if not ok:
                raise RuntimeError(detail)
        else:
            # directory: fetch repo tarball at commit
            tarball = work / "repo.tar.gz"
            fetch(repo_tarball_url(repo, commit), tarball)
            extract_root = work / "extracted"
            with tarfile.open(tarball, "r:gz") as tf:
                top = safe_extract_tar(tf, extract_root)
            source_directory = entry["install"]["source_directory"]
            if source_directory in (".", ""):
                skill_src = top
            else:
                skill_src = top / source_directory
            if not skill_src.exists():
                raise RuntimeError(f"source_directory missing: {source_directory}")
            # N32 special: install repo root (already source_directory=".")
            # verify SKILL.md relative to skill_src, but skill_md_path may be repo-relative
            rel_candidates = [
                Path(skill_md_rel).name,
                skill_md_rel,
                "SKILL.md",
            ]
            ok = False
            detail = ""
            for rel in rel_candidates:
                p = skill_src / rel
                if not p.exists() and source_directory not in (".", ""):
                    p = top / skill_md_rel
                if p.exists():
                    actual = sha256_file(p)
                    if actual == expected_md:
                        ok, detail = True, actual
                        break
                    detail = f"sha256 mismatch got={actual} want={expected_md}"
            if not ok:
                raise RuntimeError(detail or "SKILL.md not found")

        target = OUT_ROOT / declared
        # conflict: if exists with same INSTALL_META commit and SKILL.md hash, skip copy
        existing_md = target / "SKILL.md"
        # find SKILL.md at expected relative location after install — install whole tree
        copy_skill_tree(skill_src, target)
        # If skill_md is nested (source_directory contained it), OK.
        # If we installed a parent that includes skill at subpath, keep as-is.
        write_meta(target, entry, commit)

        # post-copy verify
        post_ok = False
        post_detail = ""
        for rel in [Path(skill_md_rel).name, "SKILL.md", skill_md_rel]:
            p = target / rel
            if p.exists():
                actual = sha256_file(p)
                if actual == expected_md:
                    post_ok, post_detail = True, actual
                    break
                post_detail = f"post sha mismatch {actual}"
        if not post_ok:
            # also search
            for p in target.rglob("SKILL.md"):
                actual = sha256_file(p)
                if actual == expected_md:
                    post_ok, post_detail = True, actual
                    break
                post_detail = f"post sha mismatch {actual}"
        if not post_ok:
            raise RuntimeError(f"post-install verify failed: {post_detail}")

        result["status"] = "ok"
        result["skill_md_sha256"] = post_detail
        result["files"] = sum(1 for _ in target.rglob("*") if _.is_file())
        return result
    except Exception as e:  # noqa: BLE001
        result["status"] = "error"
        result["error"] = str(e)[:500]
        return result


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    if len(entries) != 71:
        print(f"WARN: expected 71 entries, got {len(entries)}", file=sys.stderr)

    CACHE.mkdir(parents=True, exist_ok=True)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    results = []
    # modest parallelism to avoid rate limits
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(install_one, e): e["id"] for e in entries}
        for fut in concurrent.futures.as_completed(futs):
            r = fut.result()
            results.append(r)
            print(f"[{r['status']:5}] {r['id']:5} {r['declared_skill_name'][:40]:40} {r.get('error','')[:80]}", flush=True)

    results.sort(key=lambda r: r["id"])
    ok = sum(1 for r in results if r["status"] == "ok")
    report = {
        "total": len(results),
        "ok": ok,
        "error": len(results) - ok,
        "out_root": str(OUT_ROOT),
        "results": results,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDONE ok={ok}/{len(results)} report={REPORT}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
