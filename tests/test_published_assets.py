"""Check that every published vocabulary entry has retrievable source contexts."""
import json
import unittest
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'

class PublishedAssetsTest(unittest.TestCase):
    def test_all_word_contexts_and_post_chunks_are_consistent(self):
        payload = json.loads((DATA / 'words.json').read_text())
        index = json.loads((DATA / 'post-index.json').read_text())
        posts = {}
        for path in (DATA / 'post-chunks').glob('*.json'):
            chunk = json.loads(path.read_text())
            self.assertTrue(all(index.get(post_id) == path.name for post_id in chunk))
            self.assertFalse(set(posts) & set(chunk))
            posts.update(chunk)
        self.assertEqual(set(index), set(posts))
        self.assertEqual(len(posts), payload['metadata']['postCount'])
        self.assertEqual(len(payload['words']), payload['metadata']['wordCount'])
        contexts = {}
        for path in (DATA / 'contexts').glob('*.json'):
            contexts.update(json.loads(path.read_text()))
        self.assertEqual(set(contexts), {word['word'] for word in payload['words']})
        post_ids = set(posts)
        for word in payload['words']:
            ids = contexts[word['word']]
            self.assertEqual(len(ids), word['postCount'])
            self.assertEqual(len(ids), len(set(ids)))
            self.assertTrue(set(ids).issubset(post_ids))
            self.assertEqual(ids, sorted(ids, key=int, reverse=True))
        self.assertEqual(sum(word['count'] for word in payload['words']), payload['metadata']['tokenCount'])

if __name__ == '__main__':
    unittest.main()
