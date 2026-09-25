#!/usr/bin/env python3
"""批量生成「字在人后」时尚字设。用法: python3 scripts/batch_type_behind.py --words MODE,CHIC --out outputs/custom"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from agnes_gateway import generate, save_image

def prompt(word: str) -> str:
    return (
        "PRIMARY: young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light. "
        f"SECONDARY: giant English condensed word {word} in cream #F3EDE3 as BACKDROP architecture. "
        "ABSOLUTE LAYER ORDER: BACKGROUND then TYPE then PERSON. "
        f"Letters {word} pass BEHIND her head and body; hair/face/shoulder silhouette cuts through letterforms; "
        "part of each letter hidden behind her. "
        "FORBIDDEN: type in front of face/body, sticker on her, face gradient, UI, border. "
        f"Exactly ONE word {word}. No other text."
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--words', default='MODE')
    ap.add_argument('--out', default='outputs/type_behind_batch')
    ap.add_argument('--size', default='864x1152')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for w in [x.strip() for x in args.words.split(',') if x.strip()]:
        p = prompt(w)
        r = generate(p, size=args.size, model='agnes-image-2.5-flash', retries=2)
        if r.get('ok'):
            fp = out / f'behind_{w}.png'
            save_image(r, fp)
            print('OK', w, fp.stat().st_size//1024)
        else:
            print('FAIL', w, str(r)[:80])

if __name__ == '__main__':
    main()
