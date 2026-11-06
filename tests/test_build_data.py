"""Exercise corpus admission, token counting and coverage with isolated fixtures."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CorpusBuildTest(unittest.TestCase):
    def build(self, posts, dictionary=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'scripts').mkdir()
            (root / 'data').mkdir()
            shutil.copy(ROOT / 'scripts/build_data.py', root / 'scripts/build_data.py')
            (root / 'data/posts.json').write_text(json.dumps(posts))
            (root / 'data/dictionary.json').write_text(json.dumps(dictionary or {}))
            subprocess.run([sys.executable, str(root / 'scripts/build_data.py')], check=True, capture_output=True)
            result = json.loads((root / 'data/words.json').read_text())
            result['contextAssets'] = {path.stem: json.loads(path.read_text()) for path in (root / 'data/contexts').glob('*.json')}
            result['chunkAssets'] = {path.name: json.loads(path.read_text()) for path in (root / 'data/post-chunks').glob('*.json')}
            result['indexAsset'] = json.loads((root / 'data/post-index.json').read_text())
            return result

    def post(self, post_id='1532527411484626944', **extra):
        return dict(id=post_id, date='2022-06-03', type='original',
                    text='Energy &amp; energy https://example.com/ignore @someone',
                    source='https://example.com/source', verified=False,
                    sourceStatus='archive_record', **extra)

    def test_archive_record_is_counted_without_claiming_verification(self):
        data = self.build([self.post()], {'energy': {'zh': '能源', 'level': 'A2', 'phonetic': ''}})
        self.assertEqual([(w['word'], w['count']) for w in data['words']], [('energy', 2)])
        self.assertEqual(data['metadata']['tokenCount'], 2)
        self.assertEqual(data['metadata']['archivePostCount'], 1)
        self.assertFalse(data['chunkAssets']['0000.json']['1532527411484626944']['verified'])
        self.assertEqual(data['contextAssets']['e']['energy'], ['1532527411484626944'])
        self.assertEqual(data['words'][0]['postCount'], 1)
        self.assertEqual(data['indexAsset']['1532527411484626944'], '0000.json')

    def test_duplicate_retweet_and_unadmitted_records_are_excluded(self):
        post = self.post()
        retweet = dict(self.post('1532527411484626945'), type='retweet')
        unknown = dict(self.post('1532527411484626946'), sourceStatus='unknown')
        data = self.build([post, post, retweet, unknown])
        self.assertEqual(data['metadata']['postCount'], 1)
        self.assertEqual(data['metadata']['tokenCount'], 2)

    def test_coverage_and_missing_translation_follow_corpus(self):
        older = dict(self.post('1532527411484626945'), date='2020-01-02', text='Prototype')
        data = self.build([self.post(), older])
        self.assertIn('2020-01-02 至 2022-06-03', data['metadata']['coverage'])
        self.assertEqual(data['metadata']['missingTranslations'], 2)
        self.assertTrue(all(w['level'] == '未标注' for w in data['words']))

    def test_empty_corpus_has_valid_metadata(self):
        data = self.build([])
        self.assertEqual(data['words'], [])
        self.assertEqual(data['metadata']['coverage'], '暂无帖子')
        self.assertEqual(data['metadata']['tokenCount'], 0)

if __name__ == '__main__':
    unittest.main()
