#!/usr/bin/env python3
"""按 data/gpt_image_agnes_prompts.json 逐条 Agnes 出样张。"""
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
    from agnes_gateway import generate, save_image  # noqa: E402
except ImportError:
    generate = None  # type: ignore
    save_image = None  # type: ignore

DEFAULT_LIB_PATH = ROOT / "data" / "gpt_image_agnes_prompts.json"
LIB = DEFAULT_LIB_PATH
DEFAULT_OUT_DIR = ROOT / "outputs" / "agnes_samples"
OUT = DEFAULT_OUT_DIR
DEFAULT_MODEL = "agnes-image-2.5-flash"
DEFAULT_SIZE = "1088x1456"
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


def slugify(s: str | None, max_len: int = 36) -> str:
    """将字符串规范化为安全文件名片段（保留中英文字符与连接号）。"""
    if not s or not isinstance(s, str):
        return "item"
    cleaned = re.sub(r"[^\w一-鿿-]+", "-", s).strip("-")
    return cleaned[:max_len] or "item"


def load_prompts_library(lib_path: Path | str | None = None) -> list[dict[str, Any]]:
    """加载 GPT Image 转 Agnes 的 Prompt 资产库。"""
    p = Path(lib_path) if lib_path else DEFAULT_LIB_PATH
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


def render_single_sample(
    item: dict[str, Any],
    out_dir: Path | str = DEFAULT_OUT_DIR,
    model: str = DEFAULT_MODEL,
    default_size: str = DEFAULT_SIZE,
    retries: int = DEFAULT_RETRIES,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """渲染单个 Prompt 样本样张。"""
    if not isinstance(item, dict):
        return {"id": "", "ok": False, "error": "Invalid item format: expected dict"}

    raw_id = item.get("id")
    if raw_id is None or str(raw_id).strip() == "":
        return {"id": "", "ok": False, "error": "Item ID cannot be empty"}
    iid = str(raw_id).strip().replace("/", "-")

    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    title = str(item.get("title") or "x")
    name = f"{iid}_{slugify(title)}.png"
    path = target_dir / name

    prompt = build_item_prompt(item)
    if len(prompt) < 40:
        return {"id": iid, "ok": False, "error": "prompt too short"}

    size = str(item.get("agnes_size") or default_size)

    # 若文件已存在且未开启强制覆盖，且大于 20KB 则跳过
    if path.exists() and path.stat().st_size > 20_000 and not force:
        return {
            "id": iid,
            "ok": True,
            "skipped": True,
            "path": str(path),
            "file": name,
            "kb": path.stat().st_size // 1024,
            "prompt": prompt,
        }

    if dry_run:
        return {
            "id": iid,
            "ok": True,
            "dry_run": True,
            "path": str(path),
            "file": name,
            "size": size,
            "prompt": prompt,
            "prompt_len": len(prompt),
        }

    gen = generate_fn or generate
    saver = save_image_fn or save_image

    if not callable(gen):
        return {
            "id": iid,
            "ok": False,
            "error": "agnes_gateway.generate is not available or not callable",
        }

    t0 = time.time()
    try:
        res = gen(prompt, size=size, model=model, retries=retries)
        if isinstance(res, dict) and res.get("ok"):
            if callable(saver):
                saver(res, path)
            kb = path.stat().st_size // 1024 if path.exists() else 0
            return {
                "id": iid,
                "ok": True,
                "path": str(path),
                "file": name,
                "cost_s": res.get("cost_s"),
                "kb": kb,
                "via": res.get("via"),
                "model": res.get("model", model),
                "elapsed": round(time.time() - t0, 2),
            }
        err_msg = res.get("error") if isinstance(res, dict) else str(res)
        return {
            "id": iid,
            "ok": False,
            "error": str(err_msg or "Unknown generation error")[:200],
            "error_class": classify_generation_error(err_msg),
        }
    except Exception as exc:
        return {
            "id": iid,
            "ok": False,
            "error": str(exc)[:200],
            "error_class": classify_generation_error(exc),
        }


def one(item: dict) -> dict:
    """旧接口兼容：渲染单项样张。"""
    return render_single_sample(item, out_dir=OUT)


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


def run_batch_agnes_samples(
    ids: list[str] | str | None = None,
    category: str | None = None,
    limit: int | None = None,
    out_dir: Path | str = DEFAULT_OUT_DIR,
    lib_path: Path | str | None = None,
    workers: int = DEFAULT_WORKERS,
    model: str = DEFAULT_MODEL,
    default_size: str = DEFAULT_SIZE,
    retries: int = DEFAULT_RETRIES,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
    quiet: bool = False,
) -> list[dict[str, Any]]:
    """批量执行 Prompt 样张渲染并输出汇总报告。"""
    target_out = Path(out_dir)
    target_out.mkdir(parents=True, exist_ok=True)
    all_items = load_prompts_library(lib_path)
    selected_items = filter_items(all_items, ids=ids, category=category, limit=limit)

    total = len(selected_items)
    if not quiet:
        print(f"Agnes Studio · GPT Image 样张批量执行: 共 {total} 项 -> {target_out}", flush=True)

    results: list[dict[str, Any]] = []

    def _worker(it: dict[str, Any]) -> dict[str, Any]:
        return render_single_sample(
            item=it,
            out_dir=target_out,
            model=model,
            default_size=default_size,
            retries=retries,
            force=force,
            dry_run=dry_run,
            generate_fn=generate_fn,
            save_image_fn=save_image_fn,
        )

    if workers <= 1 or dry_run or total <= 1:
        for idx, it in enumerate(selected_items, 1):
            r = _worker(it)
            results.append(r)
            if not quiet:
                mark = "✓" if r.get("ok") else "✗"
                tag = "DRY" if r.get("dry_run") else ("SKIP" if r.get("skipped") else mark)
                print(f"[{idx}/{total}] {tag} {r.get('id')} {r.get('kb', 0)}KB {r.get('error', '')[:60]}", flush=True)
    else:
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_worker, it): it for it in selected_items}
            for fut in as_completed(futs):
                r = fut.result()
                results.append(r)
                done += 1
                if not quiet:
                    mark = "✓" if r.get("ok") else "✗"
                    tag = "DRY" if r.get("dry_run") else ("SKIP" if r.get("skipped") else mark)
                    print(f"[{done}/{total}] {tag} {r.get('id')} {r.get('kb', 0)}KB {r.get('error', '')[:60]}", flush=True)

    order_map = {str(it.get("id")): i for i, it in enumerate(selected_items)}
    results.sort(key=lambda r: order_map.get(str(r.get("id")), 9999))

    report_path = target_out / "batch_report.json"
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    ok_cnt = sum(1 for r in results if r.get("ok"))
    if not quiet:
        print(f"done ok={ok_cnt}/{len(results)}", flush=True)
    return results


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
    """构建 GPT Image 样张批量生成引擎命令行参数解析器"""
    parser = argparse.ArgumentParser(description="Agnes Studio · GPT Image 样张批量生成引擎")
    parser.add_argument("--list-items", action="store_true", help="列出全部 Prompt 预设清单")
    parser.add_argument("-i", "--ids", default=None, help="筛选特定 Item ID (逗号分隔，如 1001,1002)")
    parser.add_argument("-c", "--category", default=None, help="按分类筛选 (如 portrait, product)")
    parser.add_argument("-n", "--limit", type=int, default=None, help="限制最大执行数量")
    parser.add_argument("-o", "--out", default=str(DEFAULT_OUT_DIR), help=f"样张输出目录 (默认: {DEFAULT_OUT_DIR})")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help=f"并发工作线程数 (默认: {DEFAULT_WORKERS})")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"生图模型名称 (默认: {DEFAULT_MODEL})")
    parser.add_argument("--size", default=DEFAULT_SIZE, help=f"默认生图分辨率 (默认: {DEFAULT_SIZE})")
    parser.add_argument("--lib", default=str(DEFAULT_LIB_PATH), help=f"Prompt 库 JSON 路径 (默认: {DEFAULT_LIB_PATH})")
    parser.add_argument("-f", "--force", action="store_true", help="强制重新生成已存在的文件")
    parser.add_argument("-d", "--dry-run", action="store_true", help="演练模式，不请求实际生图 API")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出预设清单或批量执行汇总报告")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式，减少标准输出打印")
    parser.add_argument("--strict", action="store_true", help="严格模式：存在任何失败项或执行异常时返回非零退出码 1")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    quiet = args.quiet or args.json

    if args.list_items:
        try:
            items = list_items(lib_path=args.lib)
            if args.json:
                print(json.dumps(items, ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("Agnes Studio · GPT Image 预设清单:")
                for it in items:
                    print(f"  [{it['id']:<6}] {it['title']:<24} | 分类: {it['category']:<12} | 分辨率: {it['agnes_size']}")
                print(f"总计: {len(items)} 项预设")
            return 0
        except Exception as e:
            if args.json:
                print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
            elif not args.quiet:
                print(f"❌ GPT Image 预设清单读取失败: {e}", file=sys.stderr)
            return 1

    try:
        results = run_batch_agnes_samples(
            ids=args.ids,
            category=args.category,
            limit=args.limit,
            out_dir=args.out,
            lib_path=args.lib,
            workers=args.workers,
            model=args.model,
            default_size=args.size,
            force=args.force,
            dry_run=args.dry_run,
            quiet=quiet,
        )

        summary = {
            "total": len(results),
            "ok": sum(1 for r in results if r.get("ok")),
            "failed": sum(1 for r in results if not r.get("ok")),
            "skipped": sum(1 for r in results if r.get("skipped")),
            "dry_run": args.dry_run,
            "results": results,
        }

        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2))

        if args.strict:
            if any(not r.get("ok") for r in results):
                return 1
        elif results and all(not r.get("ok") for r in results):
            return 1
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        elif not args.quiet:
            print(f"❌ GPT Image 样张批量生成失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
