"""Safety contracts for isolated native configuration; no ERP access."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('release_config',ROOT/'scripts/phase0-configure-release.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class NoWritesAPI:
    def __init__(self, current=None):
        self.current=current
        self.calls=[]
    def get_doc(self, dt, name):
        self.calls.append(('read',dt,name))
        return self.current
    def insert(self, *args):
        self.calls.append(('write',args))
        raise AssertionError('Unexpected mutation')


class ReleaseSafetyTests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads((ROOT/'phase0/release-baseline.json').read_text())

    def test_non_synthetic_namespace_rejected_before_api(self):
        self.config['company']['company_name']='Unrelated real company'
        api=NoWritesAPI()
        with self.assertRaises(ValueError): module.configure(api,self.config,True)
        self.assertEqual(api.calls,[])

    def test_existing_currency_conflict_never_overwritten(self):
        current=dict(self.config['company'],name=self.config['company']['company_name'],default_currency='USD')
        api=NoWritesAPI(current)
        with self.assertRaisesRegex(ValueError,'Conflicting existing configuration'):
            module.configure(api,self.config,True)
        self.assertTrue(all(call[0]=='read' for call in api.calls))
        self.assertEqual(current['default_currency'],'USD')

    def test_readonly_mode_does_not_create_missing_company(self):
        api=NoWritesAPI()
        with self.assertRaisesRegex(ValueError,'Missing Company'):
            module.configure(api,self.config,False)
        self.assertTrue(all(call[0]=='read' for call in api.calls))


if __name__=='__main__': unittest.main()
