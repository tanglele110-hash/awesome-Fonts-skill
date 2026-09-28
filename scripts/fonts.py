"""Offline catalog search, Markdown rendering and package checks (standard library only)."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {'sans': '黑体', 'serif': '宋体 / 仿宋', 'kai': '楷体', 'rounded': '圆体', 'handwritten': '手写 / 书法'}
TAGS = {'正文', '标题', '海报', '简体', '繁体', '拼音', '代码', '等宽', '艺术字'}


def load():
    return json.loads((ROOT / 'data/fonts.json').read_text(encoding='utf-8'))


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' / ').replace('<', '&lt;').replace('>', '&gt;')


def render(data):
    out = ['# 中文字体目录', '', f"共 {len(data['fonts'])} 条字体及变体记录。", '',
           '用途与简繁标签描述现有样张。逐款许可、核对日期及移除记录见 [授权复核记录](LICENSE-REVIEW.md)。', '']
    for category, label in CATEGORIES.items():
        fonts = [f for f in data['fonts'] if f['category'] == category]
        out += [f'## {label}（{len(fonts)}）', '', '| 字体 | 已记录变体 | 用途 / 样张 | 授权记录 | 来源 |', '| --- | --- | --- | --- | --- |']
        for f in fonts:
            kind = {'collection': '合集来源', 'third-party': '第三方来源', 'project': '项目来源'}[f['source']['kind']]
            out.append('| ' + ' | '.join([cell(f['name']), cell(f['variant']), cell('、'.join(f['tags'])), f"[{cell(f['license']['recordedLabel'])}]({f['license']['file']})", f"[{kind}]({f['source']['url']})"]) + ' |')
        out += ['']
    return '\n'.join(out)


def validate(data):
    import hashlib
    import re
    assert data['schemaVersion'] == 2
    fonts = data['fonts']
    assert fonts and len({f['id'] for f in fonts}) == len(fonts), 'Empty catalog or duplicate IDs'
    allowed = {'id', 'name', 'family', 'variant', 'category', 'tags', 'sampleText', 'latinSampleSupported', 'source', 'license'}
    for f in fonts:
        assert set(f) == allowed, f"Unexpected fields: {f['id']}"
        assert all(isinstance(f[k], str) and f[k].strip() for k in ('id', 'name', 'family', 'variant', 'sampleText'))
        assert f['category'] in CATEGORIES
        assert isinstance(f['tags'], list) and set(f['tags']) <= TAGS
        assert len(set(f['tags'])) == len(f['tags'])
        assert isinstance(f['latinSampleSupported'], bool)
        assert set(f['source']) == {'url', 'kind', 'status'}
        assert f['source']['kind'] in {'project', 'collection', 'third-party'}
        assert f['source']['status'] == 'verified'
        u = urlsplit(f['source']['url'])
        assert u.scheme == 'https' and u.hostname in {'github.com', 'maoken.com'} and not (u.username or u.password or u.query or u.fragment)
        assert set(f['license']) == {'recordedLabel', 'status', 'checkedAt', 'evidence', 'file'}
        assert f['license']['recordedLabel'] in {'OFL-1.1', '0BSD'}
        assert f['license']['status'] == 'verified'
        assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', f['license']['checkedAt'])
        assert f['license']['evidence'].startswith('https://')
        assert f['license']['file'] == f"assets/fonts/licenses/upstream/{f['id']}.txt"
        assert (ROOT / f['license']['file']).is_file()
    review = json.loads((ROOT / 'data/license-review.json').read_text(encoding='utf-8'))
    records = review['records']
    assert len(records) == len({r['id'] for r in records}) == review['originalCount']
    retained = {r['id']: r for r in records if r['disposition'] == 'retained'}
    removed = {r['id']: r for r in records if r['disposition'] == 'removed'}
    assert len(retained) == review['retainedCount'] and len(removed) == review['removedCount']
    assert len(retained) + len(removed) == len(records)
    assert set(retained) == {f['id'] for f in fonts}
    for f in fonts:
        r = retained[f['id']]
        assert r['source'] == f['source']['url'] and r['license'] == f['license']['recordedLabel']
        assert r['checkedAt'] == f['license']['checkedAt'] and r['evidenceUrls'][0] == f['license']['evidence']
        assert hashlib.sha256((ROOT / r['licenseFile']).read_bytes()).hexdigest() == r['licenseSha256']
    for r in removed.values():
        assert r['reason'] and r['finding'] and r['evidenceUrls']
        assert not (ROOT / f"assets/fonts/{r['id']}-preview.woff2").exists()
    assert (ROOT / 'CATALOG.md').read_text(encoding='utf-8') == render(data), 'Run build to update CATALOG.md'
    previews = json.loads((ROOT / 'data/preview-fonts.json').read_text(encoding='utf-8'))
    assert {p['id'] for p in previews} == {f['id'] for f in fonts}
    for p in previews:
        assert p['sha256'] == retained[p['id']]['distributedSpecimenSha256']
    notices = json.loads((ROOT / 'data/font-notices.json').read_text(encoding='utf-8'))
    assert {n['id'] for n in notices} == set(retained)
    expected_previews = {f"assets/fonts/{f['id']}-preview.woff2" for f in fonts}
    assert {p['file'] for p in previews} == expected_previews
    ui_fonts = json.loads((ROOT / 'data/ui-fonts.json').read_text(encoding='utf-8'))
    assert {p['file'] for p in ui_fonts} == {'assets/ui/chienchia-heading.woff2', 'assets/ui/wenjin-interface.woff2'}
    assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*.woff2')} == expected_previews | {p['file'] for p in ui_fonts}
    for p in previews + ui_fonts:
        binary = (ROOT / p['file']).read_bytes()
        assert binary[:4] == b'wOF2' and len(binary) == p['bytes']
        assert hashlib.sha256(binary).hexdigest() == p['sha256']
    for file in ROOT.rglob('*'):
        if not file.is_file() or '.git' in file.parts:
            continue
        assert file.suffix.lower() not in {'.woff', '.otf', '.ttf', '.ttc', '.bak', '.log'}, 'Unexpected bundled artifact'
        if file.suffix in {'.md', '.json', '.py', '.yml'}:
            text = file.read_text(encoding='utf-8')
            assert not text.startswith('\ufeff'), f'BOM: {file.name}'
            drive_path = re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]', text)
            assert not drive_path and ('base64' + ',') not in text, f'Private/runtime data: {file.name}'
    return len(fonts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search')
    search.add_argument('query', nargs='?', default='')
    search.add_argument('--category', choices=CATEGORIES)
    search.add_argument('--tag', action='append', choices=sorted(TAGS), default=[])
    search.add_argument('--json', action='store_true')
    commands.add_parser('build')
    commands.add_parser('validate')
    args = parser.parse_args()
    data = load()
    if args.command == 'build':
        (ROOT / 'CATALOG.md').write_text(render(data), encoding='utf-8')
        print('CATALOG.md generated')
    elif args.command == 'validate':
        print(f'Validated {validate(data)} records and package boundaries')
    else:
        q = args.query.casefold()
        result = [f for f in data['fonts'] if (not args.category or f['category'] == args.category)
                  and set(args.tag) <= set(f['tags']) and q in ' '.join([f['name'], f['family'], f['variant'], *f['tags']]).casefold()]
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif result:
            for f in result:
                print(f"{f['name']} | {CATEGORIES[f['category']]} | {' / '.join(f['tags'])} | {f['source']['url']} | {f['license']['recordedLabel']}")
        else:
            print('无匹配字体 / No matches')


if __name__ == '__main__':
    main()
