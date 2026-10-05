#!/usr/bin/env python3
"""Install the 71 photo-style skills from skills-manifest.json at pinned commits.

Target: ~/.config/mimocode/skills/<declared_skill_name>/
Source cache: <repo>/.skill-cache/
"""
from __future__ import annotations

import argparse
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
from pathlib import Path
from typing import Any, Callable
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE_DIR = ROOT / ".skill-cache"
DEFAULT_OUT_ROOT = Path.home() / ".config" / "mimocode" / "skills"


def resolve_manifest_path(manifest_path: Path | str | None = None) -> Path:
    """解析 skills-manifest.json 路径，按环境配置与多候选路径回退。"""
    if manifest_path:
        return Path(manifest_path)
    env_p = os.environ.get("SKILLS_MANIFEST_PATH")
    if env_p and Path(env_p).exists():
        return Path(env_p)
    candidates = [
        ROOT / ".skill-cache" / "skills-manifest.json",
        ROOT / "data" / "skills-manifest.json",
        Path("/Users/tom/Downloads/生图Skill合集-71项/02-给AI看的安装说明书/skills-manifest.json"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return ROOT / ".skill-cache" / "skills-manifest.json"


MANIFEST = resolve_manifest_path()
CACHE = Path(os.environ.get("SKILLS_CACHE_DIR") or DEFAULT_CACHE_DIR)
OUT_ROOT = Path(os.environ.get("SKILLS_OUT_ROOT") or DEFAULT_OUT_ROOT)
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
    """计算字节流的 SHA-256 十六进制摘要。"""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """计算指定文件的 SHA-256 十六进制摘要。"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path, timeout: int = 120) -> None:
    """下载远程 URL 文件到本地目标路径。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    dest.write_bytes(data)


def repo_tarball_url(repository: str, commit: str) -> str:
    """构建 GitHub 仓库指定 commit 的 tarball 下载地址。"""
    return f"https://codeload.github.com/{repository}/tar.gz/{commit}"


def raw_url_from_blob(blob_or_raw: str) -> str:
    """Convert github blob/raw URL to raw.githubusercontent.com."""
    u = blob_or_raw
    u = u.replace("https://github.com/", "https://raw.githubusercontent.com/")
    u = u.replace("/blob/", "/")
    return u


def safe_extract_tar(tf: tarfile.TarFile, dest: Path) -> Path:
    """Extract tarball safely without path traversal; GitHub archives have a single top-level dir. Return it."""
    dest.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest.resolve()
    members = tf.getmembers()
    # reject path escape
    for m in members:
        name = m.name
        if name.startswith("/") or ".." in Path(name).parts:
            raise RuntimeError(f"unsafe tar path: {name}")
        target_path = (dest / name).resolve()
        if not str(target_path).startswith(str(dest_resolved)):
            raise RuntimeError(f"unsafe tar path escaping destination: {name}")
    try:
        tf.extractall(dest, filter="data")
    except TypeError:
        tf.extractall(dest)
    tops = {Path(m.name).parts[0] for m in members if m.name}
    if len(tops) == 1:
        top_cand = dest / next(iter(tops))
        if top_cand.is_dir():
            return top_cand
    return dest


def safe_extract_zip(zf: zipfile.ZipFile, dest: Path) -> Path:
    """Extract zip safely without path traversal. Return top directory if singular."""
    dest.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest.resolve()
    for info in zf.infolist():
        name = info.filename
        if name.startswith("/") or ".." in Path(name).parts:
            raise RuntimeError(f"unsafe zip path: {name}")
        target_path = (dest / name).resolve()
        if not str(target_path).startswith(str(dest_resolved)):
            raise RuntimeError(f"unsafe zip path escaping destination: {name}")
    zf.extractall(dest)
    tops = {Path(i.filename).parts[0] for i in zf.infolist() if i.filename}
    if len(tops) == 1:
        top_cand = dest / next(iter(tops))
        if top_cand.is_dir():
            return top_cand
    return dest


def copy_skill_tree(src_dir: Path, target: Path) -> None:
    """复制技能目录到目标路径，如已存在则保留带时间戳备份。"""
    if target.exists():
        backup = target.with_name(target.name + f".bak.{int(time.time())}")
        target.rename(backup)
    shutil.copytree(src_dir, target)


def write_meta(target: Path, entry: dict, source_commit: str, manifest_path: Path | None = None) -> None:
    """写入技能安装元数据 INSTALL_META.json 与许可证说明。"""
    lic = LICENSE_NOTES.get(entry.get("id", "")) or entry.get("license_note") or ""
    meta = {
        "collection_id": "image-skills-photo-71",
        "entry_id": entry.get("id"),
        "display_name": entry.get("display_name"),
        "declared_skill_name": entry.get("declared_skill_name"),
        "repository": entry.get("repository"),
        "verified_ref": source_commit,
        "group": entry.get("group"),
        "license_note": lic,
        "style": entry.get("style"),
        "scope": entry.get("scope"),
        "installed_from_manifest": str(manifest_path) if manifest_path else str(MANIFEST),
        "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (target / "INSTALL_META.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if lic:
        readme = target / "LICENSE_NOTE.md"
        readme.write_text(
            f"# License / Usage\n\n- entry: {entry.get('id')} {entry.get('display_name')}\n"
            f"- note: {lic}\n"
            f"- source: {entry.get('repository')} @ {source_commit}\n",
            encoding="utf-8",
        )


def verify_skill_md(skill_root: Path, skill_md_rel: str, expected: str) -> tuple[bool, str]:
    """验证 SKILL.md 文件是否存在且哈希一致。"""
    p = skill_root / skill_md_rel
    if not p.exists():
        return False, f"missing {skill_md_rel}"
    actual = sha256_file(p)
    if actual != expected:
        return False, f"sha256 mismatch got={actual} want={expected}"
    return True, actual


def load_manifest(manifest_path: Path | str | None = None) -> dict[str, Any]:
    """加载 skills-manifest.json 并执行基础结构校验。"""
    p = resolve_manifest_path(manifest_path)
    if not p.is_file():
        raise FileNotFoundError(f"Skills manifest file not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "entries" not in data or not isinstance(data["entries"], list):
        raise ValueError(f"Invalid skills manifest format in {p}: missing 'entries' list")
    return data


def filter_entries(
    entries: list[dict[str, Any]],
    ids: str | list[str] | None = None,
    group: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """按 ID、分组与数量过滤技能条目。"""
    res = list(entries)
    if ids is not None:
        if isinstance(ids, str):
            id_set = {x.strip() for x in ids.split(",") if x.strip()}
        else:
            id_set = {str(x).strip() for x in ids if str(x).strip()}
        res = [e for e in res if str(e.get("id")) in id_set]
    if group:
        g = group.strip().lower()
        res = [e for e in res if str(e.get("group", "")).strip().lower() == g]
    if limit is not None and limit > 0:
        res = res[:limit]
    return res


def install_one(
    entry: dict,
    out_root: Path | None = None,
    cache_dir: Path | None = None,
    manifest_path: Path | None = None,
    dry_run: bool = False,
    fetch_fn: Callable[[str, Path], None] | None = None,
) -> dict:
    """安装单个技能条目。支持 dry_run 与自定义下载器。"""
    if not isinstance(entry, dict) or not entry.get("id"):
        return {"status": "error", "error": "Invalid entry dict"}

    target_out_root = out_root or OUT_ROOT
    target_cache_dir = cache_dir or CACHE
    target_manifest = manifest_path or MANIFEST
    active_fetch = fetch_fn or fetch

    eid = str(entry["id"])
    install_cfg = entry.get("install")
    if not isinstance(install_cfg, dict):
        return {"id": eid, "status": "error", "error": "Missing install block"}

    declared = install_cfg.get("target_directory_name") or entry.get("declared_skill_name") or eid
    kind = install_cfg.get("kind", "directory")
    commit = entry.get("verified_ref") or (entry.get("evidence") or {}).get("commit") or "HEAD"
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
        "target": str(target_out_root / declared),
        "license_note": LICENSE_NOTES.get(eid) or entry.get("license_note") or "",
    }

    if dry_run:
        result["status"] = "dry_run"
        result["files"] = 0
        return result

    try:
        work = target_cache_dir / "work" / eid
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True, exist_ok=True)

        expected_md = (
            install_cfg.get("skill_md_sha256")
            or (entry.get("evidence") or {}).get("sha256")
        )
        skill_md_rel = install_cfg.get("skill_md_path") or install_cfg.get("skill_path_in_archive") or "SKILL.md"

        if kind in ("zip", "archive"):
            zip_path_key = "zip_path" if kind == "zip" else "archive_path"
            zip_sha_key = "zip_sha256" if kind == "zip" else "archive_sha256"
            zip_name = install_cfg.get(zip_path_key) or f"{eid}.zip"
            zip_sha = install_cfg.get(zip_sha_key)
            src_url = raw_url_from_blob(entry.get("source_url", ""))
            zip_local = work / Path(zip_name).name
            active_fetch(src_url, zip_local)
            if zip_sha:
                got_zip_sha = sha256_file(zip_local)
                if got_zip_sha != zip_sha:
                    raise RuntimeError(f"zip sha mismatch got={got_zip_sha} want={zip_sha}")
            extract_root = work / "extracted"
            with zipfile.ZipFile(zip_local) as zf:
                safe_extract_zip(zf, extract_root)
            source_directory = install_cfg.get("source_directory", ".")
            skill_src = extract_root / source_directory if source_directory not in (".", "") else extract_root
            if not skill_src.exists():
                alt = extract_root / Path(zip_name).stem
                if alt.exists():
                    skill_src = alt
                else:
                    candidates = list(extract_root.rglob("SKILL.md"))
                    if not candidates:
                        raise RuntimeError(f"skill dir not found after zip extract: {source_directory}")
                    skill_src = candidates[0].parent
            if expected_md:
                ok, detail = verify_skill_md(skill_src, "SKILL.md", expected_md)
                if not ok:
                    ok, detail = verify_skill_md(skill_src, skill_md_rel.split("/")[-1], expected_md)
                if not ok:
                    raise RuntimeError(detail)
        else:
            tarball = work / "repo.tar.gz"
            active_fetch(repo_tarball_url(repo, commit), tarball)
            extract_root = work / "extracted"
            with tarfile.open(tarball, "r:*") as tf:
                top = safe_extract_tar(tf, extract_root)
            source_directory = install_cfg.get("source_directory", ".")
            if source_directory in (".", ""):
                skill_src = top
            else:
                skill_src = top / source_directory
            if not skill_src.exists():
                raise RuntimeError(f"source_directory missing: {source_directory}")
            if expected_md:
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

        target = target_out_root / declared
        copy_skill_tree(skill_src, target)
        write_meta(target, entry, commit, manifest_path=target_manifest)

        # post-copy verify
        post_ok = True
        post_detail = ""
        if expected_md:
            post_ok = False
            for rel in [Path(skill_md_rel).name, "SKILL.md", skill_md_rel]:
                p = target / rel
                if p.exists():
                    actual = sha256_file(p)
                    if actual == expected_md:
                        post_ok, post_detail = True, actual
                        break
                    post_detail = f"post sha mismatch {actual}"
            if not post_ok:
                for p in target.rglob("SKILL.md"):
                    actual = sha256_file(p)
                    if actual == expected_md:
                        post_ok, post_detail = True, actual
                        break
                    post_detail = f"post sha mismatch {actual}"
            if not post_ok:
                raise RuntimeError(f"post-install verify failed: {post_detail}")

        result["status"] = "ok"
        result["skill_md_sha256"] = post_detail or expected_md or ""
        result["files"] = sum(1 for _ in target.rglob("*") if _.is_file())
        return result
    except Exception as e:  # noqa: BLE001
        result["status"] = "error"
        result["error"] = str(e)[:500]
        return result


def run_install(
    manifest_path: Path | str | None = None,
    cache_dir: Path | str | None = None,
    out_root: Path | str | None = None,
    ids: str | list[str] | None = None,
    group: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    workers: int = 6,
    fetch_fn: Callable[[str, Path], None] | None = None,
) -> dict[str, Any]:
    """批量执行 71 项生图技能安装管线。"""
    manifest_file = resolve_manifest_path(manifest_path)
    data = load_manifest(manifest_file)
    entries = data.get("entries", [])
    filtered = filter_entries(entries, ids=ids, group=group, limit=limit)

    target_cache = Path(cache_dir) if cache_dir else CACHE
    target_out = Path(out_root) if out_root else OUT_ROOT

    target_cache.mkdir(parents=True, exist_ok=True)
    target_out.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    if workers > 1 and len(filtered) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {
                ex.submit(
                    install_one,
                    e,
                    out_root=target_out,
                    cache_dir=target_cache,
                    manifest_path=manifest_file,
                    dry_run=dry_run,
                    fetch_fn=fetch_fn,
                ): e.get("id")
                for e in filtered
            }
            for fut in concurrent.futures.as_completed(futs):
                results.append(fut.result())
    else:
        for e in filtered:
            r = install_one(
                e,
                out_root=target_out,
                cache_dir=target_cache,
                manifest_path=manifest_file,
                dry_run=dry_run,
                fetch_fn=fetch_fn,
            )
            results.append(r)

    results.sort(key=lambda r: str(r.get("id", "")))
    ok = sum(1 for r in results if r.get("status") == "ok")
    dry_run_count = sum(1 for r in results if r.get("status") == "dry_run")
    error_count = sum(1 for r in results if r.get("status") == "error")

    report_file = target_cache / "install_report.json"
    report = {
        "total": len(results),
        "ok": ok,
        "dry_run": dry_run_count,
        "error": error_count,
        "out_root": str(target_out),
        "results": results,
    }
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_path"] = str(report_file)
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    """构建 CLI 命令行解析器。"""
    parser = argparse.ArgumentParser(description="Install 71 photo-style skills from manifest at pinned commits.")
    parser.add_argument("-m", "--manifest", type=str, default=None, help="Path to skills-manifest.json")
    parser.add_argument("-c", "--cache-dir", type=str, default=None, help="Directory for caching downloads and extraction")
    parser.add_argument("-o", "--out-dir", type=str, default=None, help="Directory to install skills into")
    parser.add_argument("--ids", type=str, default=None, help="Comma-separated IDs to install (e.g. ST03,ST07)")
    parser.add_argument("--group", type=str, default=None, help="Filter by skill group name")
    parser.add_argument("-n", "--limit", type=int, default=None, help="Limit number of skills to install")
    parser.add_argument("--dry-run", action="store_true", help="Validate entries and targets without downloading")
    parser.add_argument("-w", "--workers", type=int, default=6, help="Worker threads for concurrent installation")
    parser.add_argument("--list", action="store_true", help="List matching manifest entries and exit")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出技能清单或安装汇总报告")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式，减少控制台普通日志输出")
    parser.add_argument("--strict", action="store_true", help="严格模式：存在任何失败项或执行异常时返回非零退出码 1")
    return parser


def list_skills(
    manifest_path: Path | str | None = None,
    ids: str | list[str] | None = None,
    group: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """返回 Skill 清单列表及许可证与目标安装目录元数据。"""
    manifest_file = resolve_manifest_path(manifest_path)
    data = load_manifest(manifest_file)
    entries = data.get("entries", [])
    filtered = filter_entries(entries, ids=ids, group=group, limit=limit)
    res: list[dict[str, Any]] = []
    for e in filtered:
        lic = LICENSE_NOTES.get(e.get("id", "")) or e.get("license_note") or ""
        res.append({
            "id": e.get("id", ""),
            "display_name": e.get("display_name", ""),
            "group": e.get("group", ""),
            "target_directory_name": e.get("install", {}).get("target_directory_name", ""),
            "license": lic,
            "repository": e.get("repository", ""),
            "verified_ref": e.get("verified_ref", ""),
        })
    return res


def main(argv: list[str] | None = None) -> int:
    """CLI 主入口函数。"""
    parser = build_arg_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        manifest_data = load_manifest(args.manifest)
    except Exception as e:
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        else:
            print(f"Error loading manifest: {e}", file=sys.stderr)
        return 1

    entries = manifest_data.get("entries", [])
    filtered = filter_entries(entries, ids=args.ids, group=args.group, limit=args.limit)

    if args.list:
        if args.json:
            res = list_skills(
                manifest_path=args.manifest,
                ids=args.ids,
                group=args.group,
                limit=args.limit,
            )
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if not args.quiet:
            print(f"Agnes Studio · Skills Manifest ({len(filtered)} / {len(entries)} entries):")
            for e in filtered:
                lic = LICENSE_NOTES.get(e.get("id", "")) or e.get("license_note") or ""
                lic_str = f" [{lic}]" if lic else ""
                print(f"  [{e.get('id', '???'):5}] {e.get('display_name', ''):20} | 组: {e.get('group', ''):16} | 目录: {e.get('install', {}).get('target_directory_name', '')}{lic_str}")
        return 0

    if not args.quiet and not args.json:
        print(f"Agnes Studio · Skill71 Installer: installing {len(filtered)} skills (workers={args.workers}, dry_run={args.dry_run})")

    report = run_install(
        manifest_path=args.manifest,
        cache_dir=args.cache_dir,
        out_root=args.out_dir,
        ids=args.ids,
        group=args.group,
        limit=args.limit,
        dry_run=args.dry_run,
        workers=args.workers,
    )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif not args.quiet:
        for r in report["results"]:
            print(f"[{r['status']:7}] {r['id']:5} {str(r.get('declared_skill_name',''))[:40]:40} {str(r.get('error',''))[:80]}", flush=True)

        ok_count = report["ok"] + report["dry_run"]
        print(f"\nDONE ok={ok_count}/{report['total']} report={report.get('report_path')}")

    has_error = report.get("error", 0) > 0
    if getattr(args, "strict", False) and has_error:
        return 1
    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
