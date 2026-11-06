"""Ensure source schema handling cannot turn retweets into Musk's own vocabulary."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('import_archive', ROOT / 'scripts/import_archive.py')
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)

class ArchiveImportTest(unittest.TestCase):
    def records(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'posts.csv'
            with path.open('w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=['id','fullText','createdAt','isRetweet','isReply','quote'])
                writer.writeheader()
                writer.writerows(rows)
            return list(archive.records(path, archive.DATASETS['recent']))

    def row(self, text, **extra):
        row = dict(id='1911532025233723740', fullText=text, createdAt='2025-04-13 21:28:44+00:00', isRetweet='False', isReply='False', quote='Do not count this quoted text')
        return dict(row, **extra)

    def test_short_replies_survive_and_quote_body_is_not_imported(self):
        records = self.records([self.row('Yes', isReply='True')])
        self.assertEqual(records[0]['text'], 'Yes')
        self.assertEqual(records[0]['type'], 'reply')
        self.assertEqual(records[0]['typeBasis'], 'archive_metadata')
        self.assertFalse(records[0]['verified'])

    def test_retweet_flags_and_rt_prefix_both_exclude_records(self):
        self.assertEqual(self.records([self.row('Somebody else said this', isRetweet='True'), self.row('RT @someone: Quoted text')]), [])

    def test_link_only_and_emoji_only_records_are_excluded(self):
        self.assertEqual(self.records([self.row('https://t.co/example'), self.row('👍 @someone')]), [])

    def test_html_and_escaped_newlines_are_normalized(self):
        record = self.records([self.row(r'Energy\n&amp; freedom')])[0]
        self.assertEqual(record['text'], 'Energy\n& freedom')
        self.assertEqual(record['archiveRow'], 0)

    def test_missing_reply_flag_uses_text_inference(self):
        record = self.records([self.row('@someone True', isReply='')])[0]
        self.assertEqual(record['type'], 'reply')
        self.assertEqual(record['typeBasis'], 'text_inference')

if __name__ == '__main__':
    unittest.main()
