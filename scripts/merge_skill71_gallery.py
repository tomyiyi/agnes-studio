#!/usr/bin/env python3
"""把 71 项生图 Skill 样张并入 public/index.html 画廊 + 修正分类计数与元数据。"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_HTML_PATH = ROOT / "public" / "index.html"
DEFAULT_SAMPLES_DIR = ROOT / "outputs" / "skill71_samples"
DEFAULT_ASSETS_DIR = ROOT / "public" / "assets" / "skill71_samples"
DEFAULT_INDEX_PATH = ROOT / "data" / "skills_71_index.json"
DEFAULT_OUTPUT_JSON = ROOT / "data" / "gallery_skill71_merge.json"

# Backwards compatibility module globals
HTML = DEFAULT_HTML_PATH
SAMPLES = DEFAULT_SAMPLES_DIR
ASSETS = DEFAULT_ASSETS_DIR
INDEX = DEFAULT_INDEX_PATH

GROUP_META: dict[str, tuple[str, str]] = {
    "照片转超现实叙事": ("skill-surreal", "照片转超现实叙事"),
    "光色与氛围改造": ("skill-atmosphere", "光色与氛围改造"),
    "照片转插画与材质": ("skill-illustration", "照片转插画与材质"),
    "照片转编辑海报": ("skill-poster", "照片转编辑海报"),
    "照片转明信片与记忆档案": ("skill-memory", "照片转明信片与记忆档案"),
    "照片抽象转译": ("skill-abstract", "照片抽象转译"),
}

DEFAULT_CATEGORY_ORDER: list[tuple[str, str]] = [
    ("all", "全部作品全景"),
    ("asian-portraits", "亚洲美人写真"),
    ("character-consistency", "角色一致性 (同一人跨场景)"),
    ("fullbody-fashion", "全身站姿与高级时装"),
    ("commercial-posters", "动漫概念海报 (中文矢量排版)"),
    ("infographics", "Bento 便当格信息图"),
    ("product-commercial", "商业静物与产品摄影"),
    ("3d-assets", "3D 黏土资产与盲盒"),
    ("gpt-portrait", "GPT 人像写真"),
    ("gpt-commercial", "GPT 商业广告"),
    ("gpt-poster", "GPT 海报"),
    ("gpt-infographic", "GPT 信息图"),
]


def build_gallery_item(skill: dict[str, Any], sample_filename: str, cost_s: float = 0.0) -> dict[str, Any]:
    """根据单个 Skill 数据与样张文件名构建画廊卡片对象。"""
    sid = str(skill.get("id") or "UNKNOWN").strip()
    display_name = str(skill.get("display_name") or sid).strip()
    declared_skill_name = str(skill.get("declared_skill_name") or sid).strip()
    group = str(skill.get("group") or "").strip()
    style = str(skill.get("style") or "").strip()

    if group in GROUP_META:
        gid, gname = GROUP_META[group]
    else:
        slug = re.sub(r"[^\w-]+", "-", sid.lower()).strip("-") or "misc"
        gid, gname = f"skill-{slug}", group or "未分类风格"

    duration = 0.0
    try:
        duration = round(float(cost_s or 0.0), 2)
    except (TypeError, ValueError):
        duration = 0.0

    return {
        "id": f"skill71_{sid}",
        "title": f"{sid} · {display_name}",
        "category_id": gid,
        "category_name": gname,
        "style_tag": f"{sid} · {declared_skill_name}",
        "style_slug": declared_skill_name,
        "desc": style,
        "prompt": f"style_skill:{sid} · {declared_skill_name} · {style}",
        "duration": duration,
        "img": f"skill71_samples/{sample_filename}",
        "aspect_ratio": "3:4",
        "model": "agnes-image-2.5-flash",
        "series": "生图 Skill 合集 · 71 项",
        "license": str(skill.get("license_note") or ""),
    }


def load_skills_index(index_path: Path | str) -> list[dict[str, Any]]:
    """加载 71 skills 索引 JSON 文件。"""
    p = Path(index_path)
    if not p.is_file():
        raise FileNotFoundError(f"Skills index not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "skills" in data:
        skills = data["skills"]
        if isinstance(skills, list):
            return skills
    if isinstance(data, list):
        return data
    raise ValueError(f"Invalid skills index structure in {p}")


def load_batch_report(samples_dir: Path | str, report_file: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """加载 batch_report.json，返回按 sid 索引的字典。"""
    s_dir = Path(samples_dir)
    rp = Path(report_file) if report_file else s_dir / "batch_report.json"
    if not rp.is_file():
        return {}
    try:
        data = json.loads(rp.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {r["id"]: r for r in data if isinstance(r, dict) and "id" in r}
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def collect_gallery_items(
    skills: list[dict[str, Any]],
    samples_dir: Path | str,
    report: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[tuple[Path, str]]]:
    """扫描样张文件或报告，与 skills 索引匹配生成画廊条目列表与复制任务。"""
    s_dir = Path(samples_dir)
    report = report or {}
    items: list[dict[str, Any]] = []
    copy_tasks: list[tuple[Path, str]] = []

    for s in skills:
        sid = s.get("id")
        if not sid:
            continue
        r = report.get(sid) or {}
        src = Path(r["path"]) if r.get("path") else None
        if not src or not src.exists():
            cands = sorted(s_dir.glob(f"{sid}_*.png"))
            src = cands[0] if cands else None
        if not src or not src.exists():
            continue

        cost_s = 0.0
        try:
            cost_s = float(r.get("cost_s") or 0.0)
        except (TypeError, ValueError):
            cost_s = 0.0

        items.append(build_gallery_item(s, src.name, cost_s=cost_s))
        copy_tasks.append((src, src.name))

    return items, copy_tasks


def update_index_html(html_text: str, skill_items: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    """在 index.html 中安全更新 SKILL71_GALLERY, MASTER_CATEGORIES, ALL_GALLERY 及画廊统计。"""
    t = html_text

    def load_const(name: str) -> list[dict[str, Any]]:
        m = re.search(rf"const {name} = (\[.*?\]);\n", t, re.S)
        if not m:
            return []
        try:
            parsed = json.loads(m.group(1))
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    gpt = load_const("GPT_AGNES_GALLERY")
    master = load_const("MASTER_GALLERY")
    all_items = gpt + master + skill_items

    # 1. 注入或更新 SKILL71_GALLERY
    payload = json.dumps(skill_items, ensure_ascii=False)
    const_skill71 = f"const SKILL71_GALLERY = {payload};\n"
    if "const SKILL71_GALLERY" in t:
        t = re.sub(r"const SKILL71_GALLERY = \[.*?\];\n", lambda _: const_skill71, t, count=1, flags=re.S)
    elif "const ALL_GALLERY =" in t:
        t = t.replace("const ALL_GALLERY =", f"{const_skill71}    const ALL_GALLERY =", 1)
    elif "const MASTER_CATEGORIES =" in t:
        t = t.replace("const MASTER_CATEGORIES =", f"{const_skill71}    const MASTER_CATEGORIES =", 1)
    elif "const MASTER_GALLERY = " in t:
        t = re.sub(
            r"(const MASTER_GALLERY = \[.*?\];\n)",
            lambda m: f"{m.group(1)}    {const_skill71}",
            t,
            count=1,
            flags=re.S,
        )
    else:
        t = re.sub(r"(</script>)", lambda m: f"    {const_skill71}{m.group(1)}", t, count=1)

    # 2. 注入或更新 MASTER_CATEGORIES
    counts = Counter(x.get("category_id") for x in all_items if isinstance(x, dict))
    order = list(DEFAULT_CATEGORY_ORDER)
    for g, (gid, gname) in GROUP_META.items():
        if (gid, gname) not in order:
            order.append((gid, gname))

    cats: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for cid, cname in order:
        seen_ids.add(cid)
        n = len(all_items) if cid == "all" else counts.get(cid, 0)
        if cid != "all" and n == 0:
            continue
        cats.append({"id": cid, "name": cname, "count": n})

    for cid, count in counts.items():
        if cid and cid not in seen_ids and count > 0:
            cats.append({"id": cid, "name": str(cid), "count": count})

    cats_js = json.dumps(cats, ensure_ascii=False)
    const_cats = f"const MASTER_CATEGORIES = {cats_js};\n"
    if "const MASTER_CATEGORIES" in t:
        t = re.sub(r"const MASTER_CATEGORIES = \[.*?\];\n", lambda _: const_cats, t, count=1, flags=re.S)
    elif "const SKILL71_GALLERY" in t:
        t = re.sub(
            r"(const SKILL71_GALLERY = \[.*?\];\n)",
            lambda m: f"{m.group(1)}    {const_cats}",
            t,
            count=1,
            flags=re.S,
        )
    elif "const MASTER_GALLERY = " in t:
        t = re.sub(
            r"(const MASTER_GALLERY = \[.*?\];\n)",
            lambda m: f"{m.group(1)}    {const_cats}",
            t,
            count=1,
            flags=re.S,
        )

    # 3. 注入或更新 ALL_GALLERY 拼接
    all_gallery_stmt = (
        "const ALL_GALLERY = [...GPT_AGNES_GALLERY, ...MASTER_GALLERY, "
        "...(typeof SKILL71_GALLERY !== 'undefined' ? SKILL71_GALLERY : [])];\n"
    )
    if "const ALL_GALLERY =" in t:
        t = re.sub(r"const ALL_GALLERY = .*?;\n", lambda _: all_gallery_stmt, t, count=1, flags=re.S)
    elif "const MASTER_CATEGORIES" in t:
        t = re.sub(
            r"(const MASTER_CATEGORIES = \[.*?\];\n)",
            lambda m: f"{m.group(1)}    {all_gallery_stmt}",
            t,
            count=1,
            flags=re.S,
        )
    elif "const SKILL71_GALLERY" in t:
        t = re.sub(
            r"(const SKILL71_GALLERY = \[.*?\];\n)",
            lambda m: f"{m.group(1)}    {all_gallery_stmt}",
            t,
            count=1,
            flags=re.S,
        )

    # 4. 更新导航栏画廊数量标签
    total = len(all_items)
    t = re.sub(r"资产画廊 \(\d+\)", f"资产画廊 ({total})", t, count=1)

    meta = {
        "gallery_total": total,
        "skill71": len(skill_items),
        "gpt_agnes": len(gpt),
        "master": len(master),
        "categories": cats,
    }
    return t, meta


def merge_gallery(
    html_path: Path | str = DEFAULT_HTML_PATH,
    index_path: Path | str = DEFAULT_INDEX_PATH,
    samples_dir: Path | str = DEFAULT_SAMPLES_DIR,
    assets_dir: Path | str = DEFAULT_ASSETS_DIR,
    report_file: Path | str | None = None,
    output_json: Path | str | None = DEFAULT_OUTPUT_JSON,
    dry_run: bool = False,
) -> dict[str, Any]:
    """主调度函数：加载、复制样张并更新 HTML 与汇总 JSON。"""
    html_path = Path(html_path)
    if not html_path.is_file():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    skills = load_skills_index(index_path)
    report = load_batch_report(samples_dir, report_file=report_file)
    skill_items, copy_tasks = collect_gallery_items(skills, samples_dir, report=report)

    assets_dir = Path(assets_dir)
    copied = 0
    if not dry_run:
        assets_dir.mkdir(parents=True, exist_ok=True)
        for src, dest_name in copy_tasks:
            dest = assets_dir / dest_name
            dest.write_bytes(src.read_bytes())
            copied += 1

    t = html_path.read_text(encoding="utf-8")
    updated_html, meta = update_index_html(t, skill_items)
    meta["copied"] = copied if not dry_run else len(copy_tasks)
    meta["dry_run"] = dry_run

    if not dry_run:
        html_path.write_text(updated_html, encoding="utf-8")
        if output_json:
            out_p = Path(output_json)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return meta


def build_arg_parser() -> argparse.ArgumentParser:
    """构建命令行解析器。"""
    parser = argparse.ArgumentParser(
        description="把 71 项生图 Skill 样张并入 public/index.html 画廊 + 修正分类计数。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true", help="演练模式，不写盘任何文件")
    parser.add_argument("--html", type=str, default=str(DEFAULT_HTML_PATH), help=f"index.html 路径 (默认: {DEFAULT_HTML_PATH})")
    parser.add_argument("--index", type=str, default=str(DEFAULT_INDEX_PATH), help=f"skills 索引路径 (默认: {DEFAULT_INDEX_PATH})")
    parser.add_argument("--samples-dir", type=str, default=str(DEFAULT_SAMPLES_DIR), help=f"样张存放目录 (默认: {DEFAULT_SAMPLES_DIR})")
    parser.add_argument("--assets-dir", type=str, default=str(DEFAULT_ASSETS_DIR), help=f"画廊 assets 存放目录 (默认: {DEFAULT_ASSETS_DIR})")
    parser.add_argument("--report", type=str, default=None, help="指定的 batch_report.json 路径")
    parser.add_argument("--output-json", type=str, default=str(DEFAULT_OUTPUT_JSON), help=f"合并报告输出路径 (默认: {DEFAULT_OUTPUT_JSON})")
    parser.add_argument("--list-groups", action="store_true", help="列出预设风格分组映射并退出")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出分组映射或画廊合并汇总报告")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式，减少标准输出打印")
    parser.add_argument("--strict", action="store_true", help="严格模式：存在任何执行异常或合并异常时返回非零退出码 1")
    return parser


def main(argv: list[str] | None = None) -> int:
    """主入口函数。"""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    quiet = args.quiet or args.json

    if args.list_groups:
        try:
            groups_data = [
                {
                    "id": gid,
                    "label": label,
                    "source_group": gname,
                }
                for gname, (gid, label) in GROUP_META.items()
            ]
            if args.json:
                print(json.dumps(groups_data, ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("Agnes Studio · 71 项 Skill 分组映射清单:")
                for it in groups_data:
                    print(f"  [{it['id']:<18}] {it['label']} (原组名: {it['source_group']})")
            return 0
        except Exception as e:
            if not args.quiet and not args.json:
                print(f"❌ 71 项 Skill 分组映射读取失败: {e}", file=sys.stderr)
            elif args.json:
                print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
            return 1

    try:
        meta = merge_gallery(
            html_path=args.html,
            index_path=args.index,
            samples_dir=args.samples_dir,
            assets_dir=args.assets_dir,
            report_file=args.report,
            output_json=args.output_json,
            dry_run=args.dry_run,
        )
        if args.json:
            print(json.dumps(meta, ensure_ascii=False, indent=2))
        elif not args.quiet:
            print(f"Agnes Studio · 画廊合并完成 (dry_run={args.dry_run}):")
            print(f"  * 资产总数: {meta['gallery_total']}")
            print(f"  * Skill71 录入: {meta['skill71']}")
            print(f"  * 样张复制: {meta['copied']}")
            print(f"  * 分类数: {len(meta['categories'])}")
        return 0
    except Exception as e:
        if not args.quiet and not args.json:
            print(f"❌ 画廊合并失败: {e}", file=sys.stderr)
        elif args.json:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
