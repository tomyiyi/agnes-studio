#!/usr/bin/env python3
"""按 data/gpt_image_agnes_prompts.json 逐条 Agnes 出图。"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import sys
import time
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from agnes_gateway import generate, save_image
except ImportError:
    generate = None  # type: ignore
    save_image = None  # type: ignore

DEFAULT_LIB_PATH = ROOT / "data" / "gpt_image_agnes_prompts.json"
LIB = DEFAULT_LIB_PATH
DEFAULT_OUT_DIR = ROOT / "outputs" / "agnes_samples"
OUT = DEFAULT_OUT_DIR
DEFAULT_REPORT_NAME = "_batch_report.json"
REPORT = OUT / DEFAULT_REPORT_NAME
DEFAULT_SIZE = "1088x1456"
DEFAULT_MODEL = "agnes-image-2.5-flash"
DEFAULT_RETRIES = 2
DEFAULT_WORKERS = 3


def classify_generation_error(error: object) -> str:
    """将网关/认证/业务失败分层，避免报告把 502 误报成 Sample 失败。"""
    text = str(error or "").lower()
    if "http 502" in text or "bad gateway" in text:
        return "gateway_502"
    if any(token in text for token in ("http 401", "http 403", "unauthorized", "forbidden", "token_rejected")):
        return "auth"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    return "generation_error"


def slugify(s: str | None, max_len: int = 32) -> str:
    """将字符串规范化为安全文件名片段（保留中英文字符与连接号）。"""
    if not s or not isinstance(s, str):
        return "item"
    cleaned = re.sub(r"[^\w一-鿿-]+", "-", str(s)).strip("-")
    return cleaned[:max_len] or "item"


def load_prompts_library(lib_path: Path | str | None = None) -> list[dict[str, Any]]:
    """加载 GPT Image 转 Agnes 的 Prompt 资产库。"""
    p = Path(lib_path) if lib_path else LIB
    if not p.is_file():
        raise FileNotFoundError(f"Prompts library file not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "items" not in data or not isinstance(data["items"], list):
        raise ValueError(f"Invalid prompts library structure in {p}: missing 'items' list")
    return data["items"]


def build_item_prompt(item: dict[str, Any]) -> str:
    """从 item 中提取生图提示词，优先 agnes_prompt，回退 gpt_image_prompt。"""
    if not isinstance(item, dict):
        return ""
    return str(item.get("agnes_prompt") or item.get("gpt_image_prompt") or "").strip()


def run_one(
    item: dict[str, Any],
    out_dir: Path | str | None = None,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
    default_size: str = DEFAULT_SIZE,
    model: str = DEFAULT_MODEL,
    retries: int = DEFAULT_RETRIES,
) -> dict[str, Any]:
    """渲染单个 Prompt 样本样张并返回执行结果字典。"""
    if not isinstance(item, dict):
        return {"id": "", "title": "", "file": "", "ok": False, "error": "Invalid item format: expected dict"}

    raw_id = item.get("id")
    if raw_id is None or str(raw_id).strip() == "":
        return {"id": "", "title": str(item.get("title") or ""), "file": "", "ok": False, "error": "Item ID cannot be empty"}

    iid = str(raw_id).strip().replace("/", "-")
    title = str(item.get("title") or "")
    name = f"{iid}_{slugify(title)}.png"
    target_dir = Path(out_dir) if out_dir is not None else OUT
    out_file = target_dir / name

    rec: dict[str, Any] = {
        "id": iid,
        "title": item.get("title"),
        "file": name,
        "path": str(out_file),
        "ok": False,
    }

    if out_file.exists() and out_file.stat().st_size > 20_000 and not force:
        rec.update(ok=True, skipped=True, kb=out_file.stat().st_size // 1024)
        return rec

    prompt = build_item_prompt(item)
    if not prompt:
        rec["error"] = "prompt is empty"
        return rec
    rec["prompt"] = prompt

    size = str(item.get("agnes_size") or default_size)

    if dry_run:
        rec.update(ok=True, dry_run=True, kb=0, size=size)
        return rec

    gen = generate_fn or generate
    saver = save_image_fn or save_image

    if not callable(gen):
        rec["error"] = "agnes_gateway.generate is not available or not callable"
        return rec

    t0 = time.time()
    try:
        res = gen(prompt, size=size, model=model, retries=retries)
    except Exception as e:
        rec["error"] = f"exc:{e}"
        rec["error_class"] = classify_generation_error(e)
        return rec

    if not isinstance(res, dict) or not res.get("ok"):
        err_msg = res.get("error") if isinstance(res, dict) else str(res)
        rec["error"] = str(err_msg or "Unknown generation error")[:300]
        rec["error_class"] = classify_generation_error(err_msg)
        return rec

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        if callable(saver):
            saver(res, out_file)
        kb = out_file.stat().st_size // 1024 if out_file.exists() else 0
        rec.update(
            ok=True,
            kb=kb,
            cost_s=res.get("cost_s"),
            via=res.get("via"),
            model=res.get("model", model),
            elapsed=round(time.time() - t0, 2),
        )
    except Exception as e:
        rec["error"] = f"save_error:{e}"
        return rec

    return rec


def filter_items(
    items_list: list[dict[str, Any]],
    ids: list[str] | str | None = None,
    category: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """根据参数筛选待处理的样本列表。"""
    filtered = list(items_list)
    if ids:
        if isinstance(ids, str):
            id_set = {s.strip() for s in ids.split(",") if s.strip()}
        else:
            id_set = {str(s).strip() for s in ids if str(s).strip()}
        filtered = [it for it in filtered if str(it.get("id", "")).strip() in id_set]

    if category:
        cat_clean = category.strip().lower()
        filtered = [it for it in filtered if cat_clean in str(it.get("category", "")).lower()]

    if limit is not None and limit > 0:
        filtered = filtered[:limit]

    return filtered


def run_batch_gen(
    items_to_run: list[dict[str, Any]] | None = None,
    ids: list[str] | str | None = None,
    category: str | None = None,
    limit: int | None = None,
    out_dir: Path | str | None = None,
    lib_path: Path | str | None = None,
    workers: int = DEFAULT_WORKERS,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
    report_name: str = DEFAULT_REPORT_NAME,
    quiet: bool = False,
) -> dict[str, Any]:
    """批量出图并写入 _batch_report.json 报告。"""
    target_out = Path(out_dir) if out_dir is not None else OUT
    target_out.mkdir(parents=True, exist_ok=True)

    if items_to_run is None:
        all_items = load_prompts_library(lib_path)
        items = filter_items(all_items, ids=ids, category=category, limit=limit)
    else:
        items = filter_items(items_to_run, ids=ids, category=category, limit=limit)

    total = len(items)
    if not quiet:
        print(f"items={total} → {target_out}", flush=True)

    results: list[dict[str, Any]] = []
    t0 = time.time()

    def _worker(it: dict[str, Any]) -> dict[str, Any]:
        return run_one(
            item=it,
            out_dir=target_out,
            force=force,
            dry_run=dry_run,
            generate_fn=generate_fn,
            save_image_fn=save_image_fn,
        )

    if workers <= 1 or dry_run or total <= 1:
        for i, it in enumerate(items, 1):
            rec = _worker(it)
            results.append(rec)
            status = "✓" if rec.get("ok") else "✗"
            if not quiet:
                print(f"{status} [{i}/{total}] {rec['id']} {rec.get('file','')} {rec.get('kb', 0)}KB {rec.get('error','')[:80]}", flush=True)
    else:
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_worker, it): it for it in items}
            for fut in as_completed(futs):
                rec = fut.result()
                results.append(rec)
                done += 1
                status = "✓" if rec.get("ok") else "✗"
                if not quiet:
                    print(f"{status} [{done}/{total}] {rec['id']} {rec.get('file','')} {rec.get('kb', 0)}KB {rec.get('error','')[:80]}", flush=True)

    order_map = {str(it.get("id")): i for i, it in enumerate(items)}
    results.sort(key=lambda r: order_map.get(str(r.get("id")), 9999))

    ok = sum(1 for r in results if r.get("ok"))
    elapsed_s = round(time.time() - t0, 1)

    report_path = target_out / report_name
    report_data = {
        "ok": ok,
        "total": len(results),
        "elapsed_s": elapsed_s,
        "results": results,
    }
    report_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")
    if not quiet:
        print(f"done ok={ok}/{len(results)} report={report_path}", flush=True)

    return report_data


def list_items(lib_path: Path | str | None = None) -> list[dict[str, str]]:
    """返回 Prompt 资产库的精简清单。"""
    items = load_prompts_library(lib_path)
    return [
        {
            "id": str(it.get("id", "")),
            "title": str(it.get("title", "")),
            "category": str(it.get("category", "")),
            "agnes_size": str(it.get("agnes_size", "")),
        }
        for it in items
    ]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按 data/gpt_image_agnes_prompts.json 逐条 Agnes 出图")
    parser.add_argument("positional_ids", nargs="*", help="待生成的 Item ID 清单 (位置参数兼容，如 1001 1002)")
    parser.add_argument("-i", "--ids", default=None, help="筛选特定 Item ID (逗号分隔，如 1001,1002)")
    parser.add_argument("-c", "--category", default=None, help="按分类筛选 (如 portrait, commercial)")
    parser.add_argument("-n", "--limit", type=int, default=None, help="限制最大执行数量")
    parser.add_argument("-o", "--out", default=str(DEFAULT_OUT_DIR), help=f"样张输出目录 (默认: {DEFAULT_OUT_DIR})")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help=f"并发工作线程数 (默认: {DEFAULT_WORKERS})")
    parser.add_argument("--lib", default=str(DEFAULT_LIB_PATH), help=f"Prompt 库 JSON 路径 (默认: {DEFAULT_LIB_PATH})")
    parser.add_argument("-f", "--force", action="store_true", help="强制重新生成已存在的文件")
    parser.add_argument("-d", "--dry-run", action="store_true", help="演练模式，不请求实际生图 API")
    parser.add_argument("--list-items", action="store_true", help="列出全部 Prompt 预设清单")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出预设清单或批量执行汇总报告")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式，减少控制台标准输出打印")
    parser.add_argument("--strict", action="store_true", help="严格模式：存在任何失败项或执行异常时返回非零退出码 1")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    quiet = args.quiet or args.json

    if args.list_items:
        items = list_items(lib_path=args.lib)
        if args.json:
            print(json.dumps(items, ensure_ascii=False, indent=2))
        elif not args.quiet:
            print("Agnes Studio · GPT Image 预设清单:")
            for it in items:
                print(f"  [{it['id']:<6}] {it['title']:<24} | 分类: {it['category']:<12} | 分辨率: {it['agnes_size']}")
            print(f"总计: {len(items)} 项预设")
        return 0

    target_ids: list[str] = []
    if args.ids:
        target_ids.extend([s.strip() for s in args.ids.split(",") if s.strip()])
    if args.positional_ids:
        target_ids.extend([str(s).strip() for s in args.positional_ids if str(s).strip()])

    selected_ids = target_ids if target_ids else None

    try:
        report = run_batch_gen(
            ids=selected_ids,
            category=args.category,
            limit=args.limit,
            out_dir=args.out,
            lib_path=args.lib,
            workers=args.workers,
            force=args.force,
            dry_run=args.dry_run,
            quiet=quiet,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        elif not args.quiet:
            print(f"Error during batch generation: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    results = report.get("results", [])
    if args.strict:
        if not results or any(not r.get("ok") for r in results):
            return 1
        return 0

    if results and all(not r.get("ok") for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
