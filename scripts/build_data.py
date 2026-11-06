#!/usr/bin/env python3
"""Build word statistics and lazy-loadable context assets from source-linked posts."""
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
posts = json.loads((DATA / 'posts.json').read_text(encoding='utf-8'))
dictionary = json.loads((DATA / 'dictionary.json').read_text(encoding='utf-8'))
seen = set()
counts = Counter()
locations = defaultdict(list)
valid = []
for post in posts:
    if not isinstance(post.get('id'), str) or not re.fullmatch(r'\d{10,25}', post['id']):
        raise ValueError('Invalid post ID')
    if post['id'] in seen:
        continue
    if post.get('type') not in ('original', 'reply'):
        continue
    if post.get('sourceStatus') not in ('provided_sample', 'archive_record') and post.get('verified') is not True:
        continue
    if not post.get('source', '').startswith('https://'):
        raise ValueError('Missing data source')
    seen.add(post['id'])
    text = re.sub(r'https?://\S+|@\w+', ' ', html.unescape(post.get('text', ''))).replace('’', "'")
    tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text.lower())
    counts.update(tokens)
    # One occurrence reference per word per post, even when repeated within a post.
    for word in dict.fromkeys(tokens):
        locations[word].append(post['id'])
    valid.append(post)
valid.sort(key=lambda post: int(post['id']), reverse=True)
for ids in locations.values():
    ids.sort(key=int, reverse=True)
words = [dict(word=w, count=n, postCount=len(locations[w]), **dictionary.get(w, {
    'zh': '释义待核实', 'level': '未标注', 'phonetic': ''
})) for w, n in counts.most_common()]

# Keep the initial word list small; only fetch provenance and post bodies on demand.
for folder in ('contexts', 'post-chunks'):
    (DATA / folder).mkdir(exist_ok=True)
context_files = defaultdict(dict)
for word, ids in locations.items():
    context_files[word[0]][word] = ids
post_index = {}
chunk_files = {}
for offset in range(0, len(valid), 400):
    name = f'{offset // 400:04d}.json'
    chunk = valid[offset:offset + 400]
    chunk_files[name] = {post['id']: post for post in chunk}
    for post in chunk:
        post_index[post['id']] = name

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')

for name, value in context_files.items():
    save(DATA / 'contexts' / f'{name}.json', value)
for name, value in chunk_files.items():
    save(DATA / 'post-chunks' / name, value)
# Remove only previously generated JSON assets that are no longer needed.
for folder, expected in [('contexts', {f'{name}.json' for name in context_files}), ('post-chunks', set(chunk_files))]:
    for path in (DATA / folder).glob('*.json'):
        if path.name not in expected:
            path.unlink()
save(DATA / 'post-index.json', post_index)
archive_sources = defaultdict(list)
for post in valid:
    if post.get('sourceStatus') == 'archive_record':
        archive_sources[post.get('archiveDataset', post['source'])].append(post)
archive_posts = [post for records in archive_sources.values() for post in records]
provided_posts = [post for post in valid if post.get('sourceStatus') == 'provided_sample']
coverage_parts = []
for label, records in [('历史存档', archive_posts), ('用户样本', provided_posts)]:
    if records:
        coverage_parts.append(f"{label} {min(p['date'] for p in records)} 至 {max(p['date'] for p in records)}（{len(records):,} 条）")
if not coverage_parts and valid:
    coverage_parts.append(f"{min(p['date'] for p in valid)} 至 {max(p['date'] for p in valid)}")
metadata = {
    'sourceLabel': '用户提供样本 + 两份公开历史存档（来源见每条记录与 README）',
    'policy': '仅统计收录的原创正文与回复，排除纯转发；第三方存档未逐条与 X 核对，不代表全部历史或每日全量',
    'coverage': '；'.join(coverage_parts) + '；非完整覆盖' if valid else '暂无帖子',
    'lastBuilt': '2026-11-06',
    'postCount': len(valid), 'wordCount': len(words), 'tokenCount': sum(counts.values()),
    'missingTranslations': sum(w['zh'] == '释义待核实' for w in words),
    'archivePostCount': sum(len(records) for records in archive_sources.values()),
    'archives': [{'dataset': key, 'postCount': len(records),
                  'from': min(p['date'] for p in records), 'to': max(p['date'] for p in records),
                  'source': records[0]['source']} for key, records in sorted(archive_sources.items())],
    'levelPolicy': 'CEFR 为人工估计的学习参考，不是官方或词典认证等级；未标注词与专有名词不参与最低等级筛选',
    'countingPolicy': '大小写合并；保留词形变化、缩写、专有名词及技术片段；这是英文候选词形数，不等于词典词条数或个人总词汇量'
}
save(DATA / 'words.json', {
    'metadata': metadata, 'words': words,
    'assetVersion': hashlib.sha256((DATA / 'posts.json').read_bytes() + (DATA / 'dictionary.json').read_bytes() + b'context-schema-2').hexdigest()[:16],
    'contextBase': './data/contexts/', 'postBase': './data/post-chunks/',
    'postIndex': './data/post-index.json'
})
print(f'{len(valid)} source-linked posts, {len(words)} word forms, {sum(counts.values())} tokens; {len(chunk_files)} post chunks')
