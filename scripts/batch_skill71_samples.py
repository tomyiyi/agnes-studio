#!/usr/bin/env python3
"""71 项生图 Skill 各出 1 张风格样张（Agnes / New API，禁止 MiMo image_gen）。"""
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

DEFAULT_INDEX_PATH = ROOT / "data" / "skills_71_index.json"
INDEX = DEFAULT_INDEX_PATH
DEFAULT_OUT_DIR = ROOT / "outputs" / "skill71_samples"
OUT = DEFAULT_OUT_DIR
DEFAULT_MODEL = "agnes-image-2.5-flash"
DEFAULT_SIZE = "1088x1456"
DEFAULT_RETRIES = 2
DEFAULT_WORKERS = 3


def classify_generation_error(error: object) -> str:
    """将网关/认证/业务失败分层，避免报告把 502 误报成 Skill 失败。"""
    text = str(error or "").lower()
    if "http 502" in text or "bad gateway" in text:
        return "gateway_502"
    if any(token in text for token in ("http 401", "http 403", "unauthorized", "forbidden", "token_rejected")):
        return "auth"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    return "generation_error"

# 统一主体，便于横向比风格；净框后缀去水印/角标
BASE_SUBJECT = (
    "editorial photograph of a young East Asian woman in a light linen dress, "
    "three-quarter view, soft daylight, city cafe terrace with plants, "
    "clear subject identity, natural skin texture, film-like grain"
)
CLEAN = (
    "absolutely clean frame, no text, no letters, no logo, no watermark, "
    "no signature, no corner stamp, no glitch block, ultra sharp, 8k"
)


def slugify(s: str) -> str:
    """将字符串规范化为安全文件名片段（最多保留 28 个字符）。"""
    if not s or not isinstance(s, str):
        return "item"
    cleaned = re.sub(r"[^\w一-鿿-]+", "-", s).strip("-")
    return cleaned[:28] or "item"


def load_skills_index(index_path: Path | str | None = None) -> list[dict[str, Any]]:
    """加载 71 项 Skill 索引配置文件。"""
    p = Path(index_path) if index_path else DEFAULT_INDEX_PATH
    if not p.is_file():
        raise FileNotFoundError(f"Skills index file not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "skills" not in data or not isinstance(data["skills"], list):
        raise ValueError(f"Invalid skills index structure in {p}: missing 'skills' list")
    return data["skills"]


def build_prompt(skill: dict[str, Any], base_subject: str = BASE_SUBJECT) -> str:
    """根据单个 Skill 定义组装规范的生图提示词。"""
    if not isinstance(skill, dict):
        raise ValueError("Skill parameter must be a dictionary")
    style = skill.get("style") or skill.get("scope") or skill.get("declared_skill_name") or ""
    scope = skill.get("scope") or ""
    ages = skill.get("ages")
    keep_text = ages.get("keep_text") if isinstance(ages, dict) else False
    frame = (
        "intentional poster lettering allowed if the style requires typography"
        if keep_text
        else CLEAN
    )
    subj = base_subject.strip() if base_subject else BASE_SUBJECT
    return (
        f"{subj}. "
        f"Visual style transform: {style}. "
        f"Constraints: {scope}. "
        f"{frame}. "
        "photo-derived restyle, preserve core subject identity and scene facts"
    )


def render_single_skill_sample(
    skill: dict[str, Any],
    out_dir: Path | str = DEFAULT_OUT_DIR,
    base_subject: str = BASE_SUBJECT,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    retries: int = DEFAULT_RETRIES,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """渲染单个 Skill 的测试样张。"""
    if not isinstance(skill, dict):
        return {"id": "", "ok": False, "error": "Invalid skill format: expected dict"}

    sid = str(skill.get("id") or "").strip()
    if not sid:
        return {"id": "", "ok": False, "error": "Skill ID cannot be empty"}

    display_name = str(skill.get("display_name") or sid)
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(display_name)
    path = target_dir / f"{sid}_{slug}.png"

    prompt = build_prompt(skill, base_subject=base_subject)

    # 若文件已存在且未开启强制覆盖，且大于 20KB 则跳过
    if path.exists() and path.stat().st_size > 20_000 and not force:
        return {
            "id": sid,
            "ok": True,
            "skipped": True,
            "path": str(path),
            "file": path.name,
            "kb": path.stat().st_size // 1024,
            "prompt": prompt,
        }

    if dry_run:
        return {
            "id": sid,
            "ok": True,
            "dry_run": True,
            "path": str(path),
            "file": path.name,
            "size": size,
            "prompt": prompt,
            "prompt_len": len(prompt),
        }

    gen = generate_fn or generate
    saver = save_image_fn or save_image

    if not callable(gen):
        return {
            "id": sid,
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
                "id": sid,
                "ok": True,
                "path": str(path),
                "file": path.name,
                "cost_s": res.get("cost_s"),
                "kb": kb,
                "via": res.get("via"),
                "model": res.get("model", model),
                "elapsed": round(time.time() - t0, 2),
                "prompt": prompt,
            }
        err_msg = res.get("error") if isinstance(res, dict) else str(res)
        return {
            "id": sid,
            "ok": False,
            "error": str(err_msg or "Unknown generation error")[:220],
            "error_class": classify_generation_error(err_msg),
        }
    except Exception as exc:
        return {
            "id": sid,
            "ok": False,
            "error": str(exc)[:220],
            "error_class": classify_generation_error(exc),
        }


def one(s: dict) -> dict:
    """旧接口兼容：渲染单项样张。"""
    return render_single_skill_sample(s, out_dir=OUT)


def filter_skills(
    skills_list: list[dict[str, Any]],
    skills: list[str] | str | None = None,
    group: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """根据参数筛选待处理的 Skill 列表。"""
    filtered = list(skills_list)
    if skills:
        if isinstance(skills, str):
            id_set = {s.strip().upper() for s in skills.split(",") if s.strip()}
        else:
            id_set = {str(s).strip().upper() for s in skills if str(s).strip()}
        filtered = [s for s in filtered if str(s.get("id", "")).strip().upper() in id_set]

    if group:
        g_clean = group.strip().lower()
        filtered = [s for s in filtered if g_clean in str(s.get("group", "")).lower()]

    if limit is not None and limit > 0:
        filtered = filtered[:limit]

    return filtered


def run_batch_skill_samples(
    skills: list[str] | str | None = None,
    group: str | None = None,
    limit: int | None = None,
    out_dir: Path | str = DEFAULT_OUT_DIR,
    index_path: Path | str | None = None,
    workers: int = DEFAULT_WORKERS,
    base_subject: str = BASE_SUBJECT,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    retries: int = DEFAULT_RETRIES,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
    quiet: bool = False,
) -> list[dict[str, Any]]:
    """批量执行 Skill 样张渲染并输出汇总报告。"""
    target_out = Path(out_dir)
    target_out.mkdir(parents=True, exist_ok=True)
    all_skills = load_skills_index(index_path)
    selected_skills = filter_skills(all_skills, skills=skills, group=group, limit=limit)

    total = len(selected_skills)
    if not quiet:
        print(f"Agnes Studio · 71 项生图 Skill 批量执行: 共 {total} 项 -> {target_out}", flush=True)

    results: list[dict[str, Any]] = []

    def _worker(s: dict[str, Any]) -> dict[str, Any]:
        return render_single_skill_sample(
            skill=s,
            out_dir=target_out,
            base_subject=base_subject,
            model=model,
            size=size,
            retries=retries,
            force=force,
            dry_run=dry_run,
            generate_fn=generate_fn,
            save_image_fn=save_image_fn,
        )

    if workers <= 1 or dry_run or total <= 1:
        for idx, s in enumerate(selected_skills, 1):
            r = _worker(s)
            results.append(r)
            if not quiet:
                mark = "✓" if r.get("ok") else "✗"
                tag = "DRY" if r.get("dry_run") else ("SKIP" if r.get("skipped") else mark)
                print(f"[{idx}/{total}] {tag} {r.get('id')} {r.get('kb', 0)}KB {r.get('error', '')[:70]}", flush=True)
    else:
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_worker, s): s for s in selected_skills}
            for fut in as_completed(futs):
                r = fut.result()
                results.append(r)
                done += 1
                if not quiet:
                    mark = "✓" if r.get("ok") else "✗"
                    tag = "DRY" if r.get("dry_run") else ("SKIP" if r.get("skipped") else mark)
                    print(f"[{done}/{total}] {tag} {r.get('id')} {r.get('kb', 0)}KB {r.get('error', '')[:70]}", flush=True)

    # 按照选定顺序排序结果
    order_map = {str(s.get("id")): i for i, s in enumerate(selected_skills)}
    results.sort(key=lambda r: order_map.get(str(r.get("id")), 9999))

    report_path = target_out / "batch_report.json"
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    ok_cnt = sum(1 for r in results if r.get("ok"))
    if not quiet:
        print(f"done ok={ok_cnt}/{len(results)}", flush=True)
    return results


def list_skills(index_path: Path | str | None = None) -> list[dict[str, str]]:
    """返回 Skill 索引的精简摘要清单。"""
    skills = load_skills_index(index_path)
    return [
        {
            "id": str(s.get("id", "")),
            "display_name": str(s.get("display_name", "")),
            "group": str(s.get("group", "")),
            "declared_skill_name": str(s.get("declared_skill_name", "")),
        }
        for s in skills
    ]


def build_arg_parser() -> argparse.ArgumentParser:
    """构建 71 项生图 Skill 样张批量生成引擎命令行参数解析器"""
    parser = argparse.ArgumentParser(description="71 项生图 Skill 样张批量生成引擎")
    parser.add_argument("--list-skills", action="store_true", help="列出全部 Skill 清单")
    parser.add_argument("-s", "--skills", default=None, help="筛选特定 Skill ID (逗号分隔，如 ST03,ST07)")
    parser.add_argument("-g", "--group", default=None, help="按分类筛选 (如 照片转超现实叙事)")
    parser.add_argument("-n", "--limit", type=int, default=None, help="限制最大执行数量")
    parser.add_argument("-o", "--out", default=str(DEFAULT_OUT_DIR), help=f"样张输出目录 (默认: {DEFAULT_OUT_DIR})")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help=f"并发工作线程数 (默认: {DEFAULT_WORKERS})")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"生图模型名称 (默认: {DEFAULT_MODEL})")
    parser.add_argument("--size", default=DEFAULT_SIZE, help=f"生图分辨率 (默认: {DEFAULT_SIZE})")
    parser.add_argument("--index", default=str(DEFAULT_INDEX_PATH), help=f"Skill 索引 JSON 路径 (默认: {DEFAULT_INDEX_PATH})")
    parser.add_argument("--base-subject", default=BASE_SUBJECT, help="自定义统一基准主体提示词")
    parser.add_argument("-f", "--force", action="store_true", help="强制重新生成已存在的文件")
    parser.add_argument("-d", "--dry-run", action="store_true", help="演练模式，不请求实际生图 API")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出技能清单或批量执行汇总报告")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式，减少标准输出打印")
    parser.add_argument("--strict", action="store_true", help="严格模式：存在任何失败项或执行异常时返回非零退出码 1")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    quiet = args.quiet or args.json

    try:
        if args.list_skills:
            items = list_skills(index_path=args.index)
            if args.json:
                print(json.dumps(items, ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("Agnes Studio · 71 项生图 Skill 索引清单:")
                for item in items:
                    print(f"  [{item['id']}] {item['display_name']:<20} | 分组: {item['group']:<18} | 声明名: {item['declared_skill_name']}")
                print(f"总计: {len(items)} 项技能")
            return 0

        results = run_batch_skill_samples(
            skills=args.skills,
            group=args.group,
            limit=args.limit,
            out_dir=args.out,
            index_path=args.index,
            workers=args.workers,
            base_subject=args.base_subject,
            model=args.model,
            size=args.size,
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
            if getattr(args, "list_skills", False):
                print(f"❌ 查询 71 项 Skill 清单失败: {e}", file=sys.stderr)
            else:
                print(f"❌ 71 项生图 Skill 批量样张生成失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
