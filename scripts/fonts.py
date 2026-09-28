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
           '用途来自收藏时的设计判断；简体、繁体标签仅描述样张。授权列为历史记录，均未逐款完成最新授权核验。', '',
           '“第三方来源”与“合集来源”需要继续定位具体作者或授权页；所有链接均为来源入口，不承诺直链下载。', '']
    for category, label in CATEGORIES.items():
        fonts = [f for f in data['fonts'] if f['category'] == category]
        out += [f'## {label}（{len(fonts)}）', '', '| 字体 | 已记录变体 | 用途 / 样张 | 授权记录 | 来源 |', '| --- | --- | --- | --- | --- |']
        for f in fonts:
            kind = {'collection': '合集来源', 'third-party': '第三方来源', 'project': '项目来源'}[f['source']['kind']]
            out.append('| ' + ' | '.join([cell(f['name']), cell(f['variant']), cell('、'.join(f['tags'])), cell(f['license']['recordedLabel']), f"[{kind}]({f['source']['url']})"]) + ' |')
        out += ['']
    return '\n'.join(out)


def validate(data):
    assert data['schemaVersion'] == 1
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
        assert f['source']['status'] == 'unverified'
        u = urlsplit(f['source']['url'])
        assert u.scheme == 'https' and u.hostname in {'github.com', 'maoken.com'} and not (u.username or u.password or u.query or u.fragment)
        assert set(f['license']) == {'recordedLabel', 'status'}
        assert isinstance(f['license']['recordedLabel'], str) and f['license']['recordedLabel']
        assert f['license']['status'] == 'unverified'
    assert (ROOT / 'CATALOG.md').read_text(encoding='utf-8') == render(data), 'Run build to update CATALOG.md'
    for file in ROOT.rglob('*'):
        if not file.is_file() or '.git' in file.parts:
            continue
        assert file.suffix.lower() not in {'.woff2', '.woff', '.otf', '.ttf', '.ttc', '.bak', '.log'}, 'Unexpected bundled artifact'
        if file.suffix in {'.md', '.json', '.py', '.yml'}:
            text = file.read_text(encoding='utf-8')
            assert not text.startswith('\ufeff'), f'BOM: {file.name}'
            drive_path = chr(58) + chr(92)
            assert drive_path not in text and ('base64' + ',') not in text, f'Private/runtime data: {file.name}'
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
                print(f"{f['name']} | {CATEGORIES[f['category']]} | {' / '.join(f['tags'])} | {f['source']['url']} | 授权待核验")
        else:
            print('无匹配字体 / No matches')


if __name__ == '__main__':
    main()
