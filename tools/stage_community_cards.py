"""Stage only the public export manifest's images; WebP is pixel-verified lossless."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from PIL import Image

source, destination = map(Path, sys.argv[1:3])
manifest = json.loads((source / 'index.json').read_text(encoding='utf-8'))
target = destination / 'images'
target.mkdir(parents=True, exist_ok=True)

def stage(url):
    if not re.fullmatch(r'cards/images/[a-f0-9]{64}\.png', url):
        raise ValueError('Unexpected export path')
    original = source / url.removeprefix('cards/')
    if hashlib.sha256(original.read_bytes()).hexdigest() != original.stem:
        raise ValueError('Source image hash mismatch')
    with Image.open(original) as image:
        pixels = image.convert('RGBA')
        if max(image.size) > 16383:
            shutil.copyfile(original, target / original.name)
            return url, url, original.stat().st_size, original.stat().st_size
        temp = target / (original.stem + '.tmp.webp')
        pixels.save(temp, format='WEBP', lossless=True, method=4)
        with Image.open(temp) as check:
            if check.size != pixels.size or check.convert('RGBA').tobytes() != pixels.tobytes():
                raise ValueError('Lossless image verification failed')
        data = temp.read_bytes()
        name = hashlib.sha256(data).hexdigest() + '.webp'
        temp.replace(target / name)
        return url, 'cards/images/' + name, original.stat().st_size, len(data)

urls = sorted({r['url'] for r in manifest['images'].values()})
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(stage, urls))
mapping = {old: new for old, new, _, _ in results}
for record in manifest['images'].values():
    record['url'] = mapping[record['url']]
(destination / 'index.json').write_text(json.dumps(manifest, separators=(',', ':')), encoding='utf-8')
print(json.dumps({'ok': True, 'serials': len(manifest['images']), 'unique_images': len(urls),
                  'source_bytes': sum(r[2] for r in results), 'website_bytes': sum(r[3] for r in results),
                  'pixel_equality_verified': True}))
