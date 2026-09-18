# -*- coding: utf-8 -*-
"""关都 151 只宝可梦素材抓取（增量续传）：官方立绘 + 官方简中名 + 稀有度数据"""
import json, os, time, io, urllib.request
from PIL import Image

ROOT = r'C:\Users\clim\Documents\ChatGPT\软件开发'
OUTDIR = os.path.join(ROOT, 'ip', 'poke')
TMP = os.path.join(ROOT, '_tmp_poke')
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
SPDIR = os.path.join(TMP, 'sp')
os.makedirs(SPDIR, exist_ok=True)

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) manman-study-fetch/1.0'}
LOG = io.open(os.path.join(TMP, 'fetch.log'), 'w', encoding='utf-8')

def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.write(s + '\n')
    LOG.flush()
    print(s, flush=True)

def get(url, tries=5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:  # noqa
            last = e
            time.sleep(1.0 * (i + 1))
    raise last

dex = []
total_bytes = 0
for pid in range(1, 152):
    spf = os.path.join(SPDIR, '%03d.json' % pid)
    if os.path.exists(spf):
        sp = json.loads(io.open(spf, encoding='utf-8').read())
    else:
        sp = json.loads(get('https://pokeapi.co/api/v2/pokemon-species/%d/' % pid))
        io.open(spf, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False))

    def lang(x):
        return (x or '').lower().replace('_', '-')

    name = None
    for want in ('zh-hans', 'zh-hant', 'zh'):
        for n in sp.get('names', []):
            if lang(n['language']['name']) == want:
                name = n['name']
                break
        if name:
            break
    genus = ''
    for want in ('zh-hans', 'zh-hant', 'zh'):
        for g in sp.get('genera', []):
            if lang(g['language']['name']) == want:
                genus = g['genus']
                break
        if genus:
            break
    if not name:
        log('!! 缺少官方中文名 id=%d' % pid)
        name = sp.get('name')
    rate = sp.get('capture_rate') or 0
    legend = bool(sp.get('is_legendary') or sp.get('is_mythical'))
    # 种族值总和（base stat total）：稀有度按「强不强」分档，符合直觉
    pf = os.path.join(SPDIR, 'p%03d.json' % pid)
    if os.path.exists(pf):
        pj = json.loads(io.open(pf, encoding='utf-8').read())
    else:
        pj = json.loads(get('https://pokeapi.co/api/v2/pokemon/%d/' % pid))
        io.open(pf, 'w', encoding='utf-8').write(json.dumps(pj, ensure_ascii=False))
    bst = sum(s['base_stat'] for s in pj.get('stats', []))
    if legend:
        tier, pts = '传说', 35
    elif bst >= 480:
        tier, pts = '稀有', 25
    elif bst >= 390:
        tier, pts = '少见', 15
    else:
        tier, pts = '普通', 10

    out = os.path.join(OUTDIR, '%03d.png' % pid)
    if not (os.path.exists(out) and os.path.getsize(out) > 800):
        raw = get('https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/%d.png' % pid)
        im = Image.open(io.BytesIO(raw)).convert('RGBA')
        im = im.resize((200, 200), Image.LANCZOS)
        try:
            im.quantize(colors=128, method=Image.FASTOCTREE).save(out, optimize=True)
        except Exception:
            im.save(out, optimize=True)
    sz = os.path.getsize(out)
    total_bytes += sz
    dex.append({'id': pid, 'name': name, 'genus': genus.replace('宝可梦', ''), 'tier': tier, 'pts': pts, 'rate': rate, 'legend': legend})
    log('%3d %-10s %-8s %-6s rate=%-4d %6dB' % (pid, name, genus, tier, rate, sz))

with io.open(os.path.join(TMP, 'dex.json'), 'w', encoding='utf-8') as f:
    json.dump(dex, f, ensure_ascii=False, indent=0)

rows = []
for d in dex:
    rows.append("{id:%d,name:'%s',g:'%s',tier:'%s',pts:%d}" % (d['id'], d['name'], d['genus'], d['tier'], d['pts']))
with io.open(os.path.join(TMP, 'dex.js'), 'w', encoding='utf-8') as f:
    f.write('var POKE_DEX=[\n' + ',\n'.join(rows) + '\n];\n')

tiers = {}
for d in dex:
    tiers[d['tier']] = tiers.get(d['tier'], 0) + 1
log('===')
log('总数', len(dex), tiers, '图片总体积', round(total_bytes / 1024.0), 'KB', '平均', round(total_bytes / len(dex) / 1024.0, 1), 'KB')
LOG.close()
