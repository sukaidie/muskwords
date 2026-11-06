#!/usr/bin/env python3
"""Generate auditable word counts from verified, non-retweet Elon Musk posts."""
import json, re
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
    if post.get('type') not in ('original', 'reply') or post.get('verified') is not True:
        continue
    if not post.get('source', '').startswith('https://'):
        raise ValueError('Missing verification source')
    text = re.sub(r'https?://\S+|@\w+', ' ', post.get('text', ''))
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
        'sourceLabel': 'Elon Musk Archive · individually verified posts',
        'policy': '仅统计经来源核对的 @elonmusk 原创帖子与回复，排除纯转发；不是全部历史帖子',
        'coverage': '2026-11-06（仅已核对样本，不代表当天全部帖子）',
        'lastBuilt': '2026-11-06',
        'postCount': len(valid), 'wordCount': len(words), 'tokenCount': sum(counts.values()),
        'missingTranslations': sum(w['zh'] == '释义待核实' for w in words)
    },
    'posts': valid, 'words': words
}
(ROOT / 'data/words.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f"{len(valid)} verified posts, {len(words)} words, {sum(counts.values())} tokens")
