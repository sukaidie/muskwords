#!/usr/bin/env python3
"""Import a bounded sample from a pinned public CSV; never claim X verification."""
import argparse
import csv
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '18bee13cf1acb251087343221478bf76ab45ee1a'
SHA256 = '16eafc4a2d9537750385319d0b396a071160feefccc879bf161999a4404bdfc0'
SOURCE = f'https://github.com/MohrezSheikh/Elon-Musk-Tweets/blob/{COMMIT}/ElonMusk%27sTweets.csv'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file', type=Path)
    parser.add_argument('--limit', type=int, default=200)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    if hashlib.sha256(args.csv_file.read_bytes()).hexdigest() != SHA256:
        parser.error('CSV checksum differs from the documented source version')
    posts_path = ROOT / 'data/posts.json'
    # Replace this archive's previous import so repeated runs are deterministic.
    posts = [p for p in json.loads(posts_path.read_text()) if p.get('archiveDataset') != COMMIT]
    seen = {p['id'] for p in posts}
    for p in posts:
        if 'sourceStatus' not in p:
            p['sourceStatus'] = 'provided_sample'
            p['verified'] = False  # Original ZIP claimed verification; not independently established here.
    added = 0
    with args.csv_file.open(encoding='utf-8', newline='') as file:
        for row in csv.DictReader(file):
            text = html.unescape(row['tweet'])
            clean = re.sub(r'https?://\S+|@\w+', ' ', text)
            if re.match(r'^\s*RT\s+@', text) or len(re.findall('[A-Za-z]+', clean)) < 4:
                continue
            post_id = row['id']
            if not re.fullmatch(r'\d{10,25}', post_id) or post_id in seen:
                continue
            seen.add(post_id)
            posts.append({
                'id': post_id, 'date': row['created_at'][:10],
                'type': 'reply' if text.lstrip().startswith('@') else 'original',
                'text': text, 'source': SOURCE,
                'url': f'https://x.com/elonmusk/status/{post_id}',
                'verified': False, 'sourceStatus': 'archive_record',
                'archiveDataset': COMMIT, 'archiveRow': int(row[''])
            })
            added += 1
            if added == args.limit:
                break
    posts_path.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Imported {added} archive records; {len(posts)} total posts. X verification not performed.')

if __name__ == '__main__':
    main()
