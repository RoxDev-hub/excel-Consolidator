from io import BytesIO
import unittest
from unittest.mock import Mock, patch
from test_web import workbook
from app import app
from comparison import compare_workbooks
from workbook_reader import ConsolidationError


class ComparisonTests(unittest.TestCase):
    def compare(self, actual, expected):
        return compare_workbooks(('actual.xlsx', workbook(actual)), ('expected.xlsx', workbook(expected)))

    def test_order_and_numeric_equivalence(self):
        report = self.compare([['Name', 'Units'], ['Pen', 1], ['Book', 2]],
                              [['Units', 'Name'], [2.0, 'Book'], [1.0, 'Pen']])
        self.assertTrue(report['matches'])
        self.assertEqual(report['matching_rows'], 2)

    def test_duplicate_counts_and_changed_rows(self):
        report = self.compare([['Name'], ['Pen'], ['Pen'], ['Book']], [['Name'], ['Pen'], ['Desk']])
        self.assertEqual((report['matching_rows'], report['missing_rows'], report['extra_rows']), (1, 1, 2))
        self.assertEqual(report['missing_examples'][0]['values'], ['Desk'])

    def test_schema_mismatch_and_empty_workbooks(self):
        report = self.compare([['Actual']], [['Expected']])
        self.assertEqual(report['missing_columns'], ['Expected'])
        self.assertEqual(report['extra_columns'], ['Actual'])
        self.assertIsNone(report['matching_rows'])
        self.assertTrue(self.compare([['Name']], [['Name']])['matches'])

    def test_types_and_whitespace_are_significant(self):
        report = self.compare([['Value'], [1], [True], [' Pen']], [['Value'], ['1'], ['True'], ['Pen']])
        self.assertEqual(report['matching_rows'], 0)

    def test_invalid_and_formula_files(self):
        with self.assertRaises(ConsolidationError):
            compare_workbooks(('a.xlsx', BytesIO(b'broken')), ('b.xlsx', workbook([['Name']])))
        with self.assertRaises(ConsolidationError):
            self.compare([['Name']], [['Name'], ['=1+1']])

    def test_http_comparison_and_missing_upload(self):
        client = app.test_client()
        response = client.post('/compare', data={'actual': (workbook([['Name'], ['Pen']]), 'actual.xlsx'),
                                                'expected': (workbook([['Name'], ['Pen']]), 'expected.xlsx')})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['matches'])
        self.assertEqual(client.post('/compare').status_code, 400)

    def test_shutdown_disabled_when_hosted_and_rejects_foreign_requests(self):
        client = app.test_client()
        self.assertNotIn(b'id="stop-app"', client.get('/').data)
        self.assertEqual(client.post('/stop').status_code, 404)
        callback = Mock()
        with patch.dict(app.config, LOCAL_STOP_TOKEN='secret', LOCAL_STOP_CALLBACK=callback, LOCAL_ORIGIN='http://localhost'):
            self.assertIn(b'id="stop-app"', client.get('/').data)
            self.assertEqual(client.post('/stop').status_code, 403)
            self.assertEqual(client.post('/stop', headers={'Origin': 'https://foreign.example', 'X-Stop-Token': 'secret'}).status_code, 403)
            callback.assert_not_called()
            self.assertEqual(client.post('/stop', headers={'Origin': 'http://localhost', 'X-Stop-Token': 'secret'}).status_code, 200)
            callback.assert_called_once()


if __name__ == '__main__':
    unittest.main()
