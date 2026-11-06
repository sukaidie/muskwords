#!/usr/bin/env python3
"""Import source-linked records from pinned public CSVs; never claim X verification."""
import argparse
import csv
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = {
    'legacy': {
        'commit': '18bee13cf1acb251087343221478bf76ab45ee1a',
        'sha256': '16eafc4a2d9537750385319d0b396a071160feefccc879bf161999a4404bdfc0',
        'source': 'https://github.com/MohrezSheikh/Elon-Musk-Tweets/blob/18bee13cf1acb251087343221478bf76ab45ee1a/ElonMusk%27sTweets.csv',
        'id': 'id', 'text': 'tweet', 'date': 'created_at'
    },
    'recent': {
        'commit': '7168f60757af7f7d1c8f85bcf9ddcb5d12ddef32',
        'sha256': 'e3a2d1cecd2f2313b3af9806144fc2d50ce8f4ca605e4006b82c266656912f54',
        'source': 'https://github.com/MagdalenaRomaniecka/Anatomy-of-a-Tweetstorm/blob/7168f60757af7f7d1c8f85bcf9ddcb5d12ddef32/data/all_musk_posts%20(1).zip',
        'id': 'id', 'text': 'fullText', 'date': 'createdAt'
    }
}

def records(csv_file, dataset, limit=None):
    """Yield admitted records in CSV order. archiveRow is a zero-based data row."""
    emitted = 0
    with csv_file.open(encoding='utf-8-sig', newline='') as file:
        for row_number, row in enumerate(csv.DictReader(file)):
            text = html.unescape(row[dataset['text']])
            # Some exports store line breaks as literal backslash sequences.
            text = text.replace(r'\n', '\n').replace(r'\r', '\r').replace(r'\t', '\t')
            if row.get('isRetweet', '').lower() == 'true' or re.match(r'^\s*RT\s+@', text):
                continue
            clean = re.sub(r'https?://\S+|@\w+', ' ', text)
            if not re.search('[A-Za-z]', clean):
                continue
            post_id = row[dataset['id']]
            if not re.fullmatch(r'\d{10,25}', post_id):
                raise ValueError(f'Invalid post ID at data row {row_number}')
            date = row[dataset['date']][:10]
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
                raise ValueError(f'Invalid date at data row {row_number}')
            reply_flag = row.get('isReply', '').lower()
            is_reply = reply_flag == 'true' if reply_flag in ('true', 'false') else text.lstrip().startswith('@')
            yield {
                'id': post_id, 'date': date, 'type': 'reply' if is_reply else 'original',
                'typeBasis': 'archive_metadata' if reply_flag in ('true', 'false') else 'text_inference',
                'text': text, 'source': dataset['source'],
                'url': f'https://x.com/elonmusk/status/{post_id}',
                'verified': False, 'sourceStatus': 'archive_record',
                'archiveDataset': dataset['commit'], 'archiveRow': row_number
            }
            emitted += 1
            if limit is not None and emitted >= limit:
                break

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file', type=Path)
    parser.add_argument('--dataset', choices=DATASETS, default='legacy')
    parser.add_argument('--limit', type=int, help='Optional sample size; omitted imports all usable records')
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    dataset = DATASETS[args.dataset]
    if hashlib.sha256(args.csv_file.read_bytes()).hexdigest() != dataset['sha256']:
        parser.error('CSV checksum differs from the documented source version')
    posts_path = ROOT / 'data/posts.json'
    # Remove only this source's earlier import; preserve all other sources and seed records.
    posts = [p for p in json.loads(posts_path.read_text()) if p.get('archiveDataset') != dataset['commit']]
    seen = {p['id'] for p in posts}
    added = duplicates = 0
    for post in records(args.csv_file, dataset, args.limit):
        if post['id'] in seen:
            duplicates += 1
            continue
        seen.add(post['id'])
        posts.append(post)
        added += 1
    posts.sort(key=lambda p: int(p['id']), reverse=True)
    posts_path.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{args.dataset}: added {added}, skipped {duplicates} duplicate IDs; {len(posts)} total posts. X verification not performed.')

if __name__ == '__main__':
    main()
