#!/usr/bin/env python3
"""P0 八套高保真样张：提示词可由 gemini-3.8 编译，出图只走 Agnes/NewAPI。"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from agnes_gateway import generate, save_image  # noqa: E402
except ImportError:
    generate = None  # type: ignore
    save_image = None  # type: ignore

DEFAULT_OUT_DIR = ROOT / "outputs" / "skill71_hifi_p0"
OUT = DEFAULT_OUT_DIR
DEFAULT_MODEL = "agnes-image-2.5-flash"
DEFAULT_RETRIES = 2


def classify_generation_error(error: object) -> str:
    """将网关/认证/业务失败分层，避免报告把 502 误报成 Hifi 样张失败。"""
    text = str(error or "").lower()
    if "http 502" in text or "bad gateway" in text:
        return "gateway_502"
    if any(token in text for token in ("http 401", "http 403", "unauthorized", "forbidden", "token_rejected")):
        return "auth"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    return "generation_error"

# 统一源图事实（来自 1013 美妆人像：亚麻裙亚裔女子·咖啡馆绿植·自然光）
SOURCE_FACTS = (
    "SOURCE PHOTO FACTS (preserve identity and scene): "
    "a young East Asian woman, long straight black hair, calm expression looking at camera, "
    "wearing a cream sleeveless linen midi dress and thin gold necklace, "
    "seated three-quarter on a black metal bistro chair at a sidewalk cafe terrace, "
    "hands resting near lap, terracotta potted green plants and white flowers behind her, "
    "beige city apartment facades, soft overcast daylight, shallow depth of field, "
    "muted natural palette (cream, olive green, warm beige)."
)

CLEAN = (
    "absolutely clean frame, no text, no letters, no logo, no watermark, "
    "no signature, no corner stamp, no glitch block, ultra sharp"
)

# 按各 SKILL.md 硬约束手写最终生图提示词（不经过 gemini 生图）
PROMPTS = {
    "S05": {
        "name": "少色编辑海报 mono-color",
        "size": "1088x1456",
        "prompt": (
            f"{SOURCE_FACTS}. "
            "Monocolor editorial print poster, vertical 3:4. Controlled two-ink system: "
            "Pale Beige substrate #F5F1E8, dominant Cobalt #2148B8 plate carrying 75% of the image "
            "as medium halftone of the woman and cafe plants, accent Terracotta #C65F38 plate 25% "
            "on dress highlight and one pot. Reproduced photograph via clean plate separation, "
            "not a filter. Large empty paper ~35% on the upper-left for typography tension. "
            "One literary serif English display line of 3 words in near-black, small mono archive mark. "
            "Flat print, no gradients, no fifth color, no sepia aging, no mockup. "
            + CLEAN
        ),
    },
    "S07": {
        "name": "昆汀电影海报 neil-quentin",
        "size": "864x1152",
        "prompt": (
            f"{SOURCE_FACTS}. "
            "1990s pulp-print movie poster, vertical 2:3. One high-chroma flat vermilion #B80102 "
            "floods the entire background, no gradient no sky. The woman is flattened into hard-edged "
            "high-contrast shapes (Tier-1 photographic with graded color so the face stays recognizable), "
            "skin pushed to one warm tone, cream dress as flat off-white #F7F7F7, shadows near-black #010100. "
            "One heavy condensed uppercase golden-yellow #F2B610 title word 'QUIET' across the lower third. "
            "Tiny credit block at the foot with original scene description only (no real film/person/studio names). "
            "Whole sheet covered in aged paper grain and print wear. Palette strictly 3-4 colors. "
            "Hard subject-to-background edges, no soft edges, no gradients. "
            + CLEAN
        ),
    },
    "S09": {
        "name": "孔版印刷 photo-riso-poster",
        "size": "864x1152",
        "prompt": (
            "Quiet riso-print archive poster, portrait 3:4, full-frame scanned warm pale cream paper "
            "with subtle fibers, light never stained, no border no mockup no 3D. "
            "Evidence from source: one seated woman silhouette (anonymous, no face detail), "
            "3-5 potted plant silhouettes at uneven spacing, one bistro chair mark; warm afternoon temperature. "
            "2-3 ink risograph: deep indigo ink, leaf-green ink, vermilion-orange ink as grainy silhouettes "
            "and fields with slight misregistration; primary motif the woman cluster occupying 15% off-center lower-right. "
            "65-85% empty paper. Typography: small typewriter type — poetic phrase 'terrace / afternoon' in 2 stacked lines "
            "near the cluster; tiny archive block 'NO. 014' + warm overcast note; count mark 'x 001'. "
            "Photocopy softness, fine riso grain, ink bleed, slight layer misregistration. "
            "Quiet archival diary mood. Avoid full-bleed scene, sky/ground edge-to-edge, cartoon flatness, "
            "commercial poster layout, cinematic light, 3D, neon, photorealism, long paragraphs, muddy browns. "
            "no text garbling, correctly spelled short English words only, no watermark"
        ),
    },
    "S15": {
        "name": "潘通色卡 create-pantone-photo-posters",
        "size": "1088x1456",
        "prompt": (
            f"{SOURCE_FACTS}. "
            "Premium Pantone-style framed photo poster, vertical 3:4. White/warm-white Pantone card frame "
            "with generous bottom type area. Real photograph of the woman seated at cafe terrace kept clear, "
            "true and recognizable inside the frame. Outer background is a high-value low-saturation soft gradient "
            "extracted from photo main colors (warm beige #E8DFD2, soft olive mist). Three-layer depth: "
            "background field / framed photo / a few restrained subject contours (shoulder, one plant leaf tip) "
            "naturally breaking through the inner frame with subtle contact shadow only. "
            "Elements breaking frame must not touch canvas edges. Bottom type block: clean black sans-serif "
            "approximate Pantone labels '2995 C · COASTAL GREY' and '7527 C · LINEN CREAM' as visual approximations. "
            "All type single-layer sharp pure black, no reflection, no emboss, no glow. "
            "Keep intentional left-side negative space clean. Photographic realism, no plastic skin. "
            + CLEAN
        ),
    },
    "S11": {
        "name": "电影印相 kodak-2383-film-look",
        "size": "1086x1449",
        "prompt": (
            f"{SOURCE_FACTS}. "
            "Vertical film-board artwork 1086x1449, stacked comparison layout. "
            "Adaptive board color sampled from cream dress and warm beige facades, desaturated, "
            "as visible low-contrast brushed/rolled pigment texture (not flat fill). "
            "Upper ungraded subject-led crop of the woman (original color/tonality). "
            "Lower 2383-inspired print-film crop, slightly tighter: print-film density and color separation, "
            "smooth highlight roll-off, deep but readable blacks, cool steel shadow separation, "
            "warm practical highlights on skin and linen, localized warm edge halation on sunlit rims and pale dress, "
            "restrained highlight diffusion, fine organic film grain. "
            "Narrow uneven amber-red emulsion overflow on short broken segments of the lower print only "
            "(5-8% of lower perimeter), one incomplete red/cyan registration shift, faint chemical tide line, "
            "one localized light leak. Small quiet widely-tracked label 'Kodak-2383' centered below lower print only. "
            "No other text. Not a teal-orange blockbuster filter. Preserve face identity. "
            + CLEAN
        ),
    },
    "N01": {
        "name": "工业夜景 neil-monochrome-night",
        "size": "864x1536",
        "prompt": (
            "Controlled photographic night-scene reconstruction, full-bleed near-9:16 portrait. "
            "Rebuild this sidewalk cafe terrace street into Neil Monochrome Night. "
            "Must retain: intimate street terrace scene class, camera facing seated woman, "
            "identity anchors: bistro chair geometry, potted plant cluster, beige facade rhythm. "
            "Vertical plan: upper colored atmospheric field with industrial haze and urban light pollution "
            "(sky is cyan-teal, not black), middle scene with simplified woman silhouette and terrace, "
            "lower wet pavement reflective field (post-rain, no falling rain). "
            "Complementary opposition: broad cool cyan-teal ambient field (25-35% readable core) "
            "against compact amber warm-white practical emitters (~10% footprint) from cafe lamps and one neon sign. "
            "Deep readable darkness, dry industrial particulate haze catching city glow. "
            "One physical two-word uppercase English neon phrase 'SLOW AFTERNOON' embedded on a cafe lightbox. "
            "Photographic materials, restrained bloom, imperfect exposure. Avoid cyberpunk label, "
            "megastructures, hero-portrait framing, unrelated neon clutter. "
            + CLEAN
        ),
    },
    "S04": {
        "name": "现实重新布景 reality-restaged",
        "size": "864x1152",
        "prompt": (
            f"{SOURCE_FACTS}. "
            "Reality Restaged cinematic still, vertical 3:4. Documentary memory rebuilt as art-directed stage. "
            "Preserve documentary anchors: the seated young woman (same face, cream linen dress, gold necklace, pose), "
            "one terracotta pot plant as memory cue. Aggressively simplify: remove cafe clutter, extra chairs, "
            "street details. COLOR IS ARCHITECTURE: expand latent colors into monumental fields — "
            "vast cream-white void wall, one monumental olive-green vertical plane from the plants, "
            "warm beige floor plane. Strong negative space. One impossible relationship: "
            "the potted plant grows to monumental scale beside her like a column while she remains human-sized. "
            "Believable analog photographic realism on skin and fabric, cinematic location light, "
            "large-format practical-cinema tension. Not merely adding a strange object — "
            "composition, space, scale, and color must transform. No text. "
            + CLEAN
        ),
    },
    "S02": {
        "name": "超现实波普拼贴 surreal-pop-collage",
        "size": "864x1152",
        "prompt": (
            "surreal pop collage, vertical 3:4. "
            "keep the seated young Asian woman in cream linen dress clearly recognizable but desaturated to black and white, "
            "preserving her texture and face; cafe terrace plants and chair as secondary B&W reality anchors. "
            "the background replaced by huge flat matte color shapes: one flat lemon-yellow sky plane purified from warm afternoon light, "
            "one flat brick-red floor plane from terracotta pots. flat matte colors, no gradients, no shadows on the color shapes. "
            "one impossible giant element only: a giant white coffee cup larger than the apartment facades hanging in the air like a moon. "
            "3-5 small white birds in graduated sizes 100/60/30 following an arc. "
            "a few white hand-drawn graffiti strokes. "
            "the black-and-white reality collides with the flat color world, bright and dreamlike, not dark horror. "
            "no second impossible object, no text, no watermark, no border frame"
        ),
    },
}


def list_hifi_presets() -> list[tuple[str, str, str, str]]:
    """返回全部 P0 高保真样张预设清单 (sid, name, size, prompt)。"""
    return [(sid, spec["name"], spec["size"], spec["prompt"]) for sid, spec in PROMPTS.items()]


def get_hifi_preset(sid: str) -> dict[str, str] | None:
    """根据 Skill ID 获取对应的预设元数据（支持大小写不敏感匹配）。"""
    if not sid or not isinstance(sid, str):
        return None
    s_clean = sid.strip().upper()
    for key, spec in PROMPTS.items():
        if key.upper() == s_clean:
            return {"id": key, "name": spec["name"], "size": spec["size"], "prompt": spec["prompt"]}
    return None


def render_single_hifi(
    sid: str,
    spec: dict[str, str] | None = None,
    out_dir: Path | str = DEFAULT_OUT_DIR,
    model: str = DEFAULT_MODEL,
    size: str | None = None,
    retries: int = DEFAULT_RETRIES,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """渲染单套 P0 高保真样张。"""
    if not sid or not str(sid).strip():
        return {"id": str(sid), "ok": False, "err": "Skill ID cannot be empty"}

    sid_clean = str(sid).strip()
    preset = get_hifi_preset(sid_clean)

    if spec is None:
        if not preset:
            return {"id": sid_clean, "ok": False, "err": f"Skill preset '{sid_clean}' not found in PROMPTS"}
        active_spec = preset
    else:
        active_spec = spec

    name = active_spec.get("name") or sid_clean
    img_size = size or active_spec.get("size") or "1088x1456"
    prompt = active_spec.get("prompt") or ""

    if not prompt or not str(prompt).strip():
        return {"id": sid_clean, "name": name, "ok": False, "err": "Prompt cannot be empty"}

    slug = name.split()[0] if name else "sample"
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    fp = target_dir / f"{sid_clean}_{slug}.png"

    # 若文件已存在且未开启强制覆盖，且大于 20KB 则跳过
    if fp.exists() and fp.stat().st_size > 20_000 and not force:
        return {
            "id": sid_clean,
            "name": name,
            "ok": True,
            "skipped": True,
            "path": str(fp),
            "kb": fp.stat().st_size // 1024,
            "prompt": prompt,
        }

    if dry_run:
        return {
            "id": sid_clean,
            "name": name,
            "ok": True,
            "dry_run": True,
            "path": str(fp),
            "size": img_size,
            "prompt": prompt,
            "prompt_len": len(prompt),
        }

    gen = generate_fn or generate
    saver = save_image_fn or save_image

    if not callable(gen):
        return {
            "id": sid_clean,
            "name": name,
            "ok": False,
            "err": "agnes_gateway.generate is not available or not callable",
        }

    t0 = time.time()
    try:
        res = gen(prompt, size=img_size, model=model, retries=retries)
        if isinstance(res, dict) and res.get("ok"):
            if callable(saver):
                saver(res, fp)
            kb = fp.stat().st_size // 1024 if fp.exists() else 0
            return {
                "id": sid_clean,
                "name": name,
                "ok": True,
                "path": str(fp),
                "kb": kb,
                "cost_s": res.get("cost_s"),
                "via": res.get("via"),
                "model": res.get("model", model),
                "elapsed": round(time.time() - t0, 2),
                "prompt": prompt,
            }
        err_msg = res.get("error") if isinstance(res, dict) else str(res)
        return {
            "id": sid_clean,
            "name": name,
            "ok": False,
            "err": err_msg or "Unknown generation error",
            "error_class": classify_generation_error(err_msg),
        }
    except Exception as exc:
        return {
            "id": sid_clean,
            "name": name,
            "ok": False,
            "err": str(exc),
            "error_class": classify_generation_error(exc),
        }


def run_batch_hifi(
    skills: list[str] | str | None = None,
    limit: int | None = None,
    out_dir: Path | str = DEFAULT_OUT_DIR,
    model: str = DEFAULT_MODEL,
    size: str | None = None,
    retries: int = DEFAULT_RETRIES,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
) -> list[dict[str, Any]]:
    """批量渲染 P0 高保真样张并生成汇总报告。"""
    target_base = Path(out_dir)
    target_base.mkdir(parents=True, exist_ok=True)

    if skills:
        if isinstance(skills, str):
            s_set = {s.strip().upper() for s in skills.split(",") if s.strip()}
        else:
            s_set = {str(s).strip().upper() for s in skills if str(s).strip()}
        target_keys = [k for k in PROMPTS if k.upper() in s_set]
    else:
        target_keys = list(PROMPTS.keys())

    if limit is not None and limit > 0:
        target_keys = target_keys[:limit]

    print(f"Agnes Studio · P0 高保真样张批量执行: 共 {len(target_keys)} 组预设", flush=True)

    results: list[dict[str, Any]] = []
    total = len(target_keys)

    for idx, sid in enumerate(target_keys, 1):
        spec = PROMPTS[sid]
        res = render_single_hifi(
            sid=sid,
            spec=spec,
            out_dir=target_base,
            model=model,
            size=size,
            retries=retries,
            force=force,
            dry_run=dry_run,
            generate_fn=generate_fn,
            save_image_fn=save_image_fn,
        )
        results.append(res)
        tag = "OK" if res.get("ok") else "FAIL"
        if res.get("dry_run"):
            tag = "DRY"
        elif res.get("skipped"):
            tag = "SKIP"
        p_name = Path(res.get("path", "")).name
        print(f"[{idx}/{total}] {tag} {sid} -> {p_name}", flush=True)

    ok_cnt = sum(1 for r in results if r.get("ok"))
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(results),
        "ok": ok_cnt,
        "failed": len(results) - ok_cnt,
        "results": results,
    }
    report_file = target_base / "hifi_report.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agnes Studio · P0 八套高保真样张批量生成引擎")
    parser.add_argument("--list-presets", action="store_true", help="列出全部 P0 高保真预设清单")
    parser.add_argument("-s", "--skills", default=None, help="筛选执行的特定 Skill 标识 (逗号分隔，如 S05,S07)")
    parser.add_argument("-n", "--limit", type=int, default=None, help="限制最大执行数量")
    parser.add_argument("-o", "--out", default=str(DEFAULT_OUT_DIR), help=f"样张输出目录 (默认: {DEFAULT_OUT_DIR})")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"生图模型名称 (默认: {DEFAULT_MODEL})")
    parser.add_argument("--size", default=None, help="自定义生图分辨率 (默认使用各预设尺寸)")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help=f"失败重试次数 (默认: {DEFAULT_RETRIES})")
    parser.add_argument("-f", "--force", action="store_true", help="强制重新生成已存在的文件")
    parser.add_argument("-d", "--dry-run", action="store_true", help="演练模式，不请求实际生图 API")

    args = parser.parse_args(argv)

    if args.list_presets:
        print("Agnes Studio · P0 八套高保真样张预设清单:")
        for sid, name, sz, prompt in list_hifi_presets():
            print(f"  [{sid}] {name:<30} | {sz} | 提示词长: {len(prompt)}")
        return 0

    results = run_batch_hifi(
        skills=args.skills,
        limit=args.limit,
        out_dir=args.out,
        model=args.model,
        size=args.size,
        retries=args.retries,
        force=args.force,
        dry_run=args.dry_run,
    )

    if results and all(not r.get("ok") for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
