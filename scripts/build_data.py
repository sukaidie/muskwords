#!/usr/bin/env python3
"""Generate auditable word counts from source-linked, non-retweet post samples."""
import html, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
posts = json.loads((ROOT / 'data/posts.json').read_text(encoding='utf-8'))
dictionary = json.loads((ROOT / 'data/dictionary.json').read_text(encoding='utf-8'))
seen = set()
counts = Counter()
locations = defaultdict(list)
valid = []
for post in posts:
    if not isinstance(post.get('id'), str) or not re.fullmatch(r'\d{10,25}', post['id']):
        raise ValueError('Invalid post ID')
    if post['id'] in seen:
        continue
    seen.add(post['id'])
    if post.get('type') not in ('original', 'reply'):
        continue
    if post.get('sourceStatus') not in ('provided_sample', 'archive_record') and post.get('verified') is not True:
        continue
    if not post.get('source', '').startswith('https://'):
        raise ValueError('Missing data source')
    text = re.sub(r'https?://\S+|@\w+', ' ', html.unescape(post.get('text', '')))
    text = text.replace('’', "'")
    tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text.lower())
    # Keep surface forms, avoid pretending that automated lemmatization is exact.
    for word in tokens:
        counts[word] += 1
        if post['id'] not in locations[word]:
            locations[word].append(post['id'])
    valid.append(post)
words = [dict(word=w, count=n, postIds=locations[w], **dictionary.get(w, {'zh':'释义待核实','level':'未标注','phonetic':''})) for w,n in counts.most_common()]
result = {
    'metadata': {
        'sourceLabel': '用户提供样本 + MohrezSheikh/Elon-Musk-Tweets 历史存档',
        'policy': '仅统计收录的原创帖子与回复，排除纯转发；第三方存档未逐条与 X 核对，不代表全部历史或每日全量',
        'coverage': f"{min(p['date'] for p in valid)} 至 {max(p['date'] for p in valid)}（非连续选样，非完整覆盖）" if valid else '暂无帖子',
        'lastBuilt': '2026-11-06',
        'postCount': len(valid), 'wordCount': len(words), 'tokenCount': sum(counts.values()),
        'missingTranslations': sum(w['zh'] == '释义待核实' for w in words),
        'archivePostCount': sum(p.get('sourceStatus') == 'archive_record' for p in valid),
        'levelPolicy': 'CEFR 为人工估计的学习参考，不是官方或词典认证等级；未标注词与专有名词不参与最低等级筛选'
    },
    'posts': valid, 'words': words
}
(ROOT / 'data/words.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f"{len(valid)} source-linked posts, {len(words)} words, {sum(counts.values())} tokens")
