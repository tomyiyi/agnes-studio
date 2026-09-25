#!/usr/bin/env python3
"""P0 八套高保真样张：提示词可由 gemini-3.8 编译，出图只走 Agnes/NewAPI。"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from agnes_gateway import generate, save_image  # noqa: E402

OUT = ROOT / "outputs" / "skill71_hifi_p0"
OUT.mkdir(parents=True, exist_ok=True)

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


def main() -> None:
    results = []
    for sid, spec in PROMPTS.items():
        out = OUT / f"{sid}_{spec['name'].split()[0]}.png"
        if out.exists() and out.stat().st_size > 20_000:
            results.append({"id": sid, "ok": True, "skipped": True, "path": str(out)})
            print(f"skip {sid}", flush=True)
            continue
        t0 = time.time()
        res = generate(spec["prompt"], size=spec["size"], model="agnes-image-2.5-flash", retries=2)
        if not res.get("ok"):
            results.append({"id": sid, "ok": False, "error": str(res)[:240]})
            print(f"FAIL {sid} {res}", flush=True)
            continue
        save_image(res, out)
        results.append(
            {
                "id": sid,
                "name": spec["name"],
                "ok": True,
                "path": str(out),
                "kb": out.stat().st_size // 1024,
                "cost_s": res.get("cost_s"),
                "via": res.get("via"),
                "model": res.get("model"),
                "elapsed": round(time.time() - t0, 2),
                "prompt": spec["prompt"],
            }
        )
        print(f"OK {sid} {out.name} {out.stat().st_size//1024}KB {res.get('cost_s')}s", flush=True)

    (OUT / "hifi_report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ok = sum(1 for r in results if r.get("ok"))
    print(f"done {ok}/{len(PROMPTS)}", flush=True)


if __name__ == "__main__":
    main()
