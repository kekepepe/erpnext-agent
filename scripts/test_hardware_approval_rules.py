"""Approval invariants: changing business inputs, identity and lifecycle states."""
import importlib.util
import unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'apps/hardware_erp/hardware_erp/rules.py'
s=importlib.util.spec_from_file_location('approval_rules',p);rules=importlib.util.module_from_spec(s);s.loader.exec_module(rules)

class RulesTests(unittest.TestCase):
    def test_price_and_tax_changes_are_visible(self):
        old={'items':[{'rate':10000,'qty':1}],'taxes':[{'rate':5}]}
        self.assertNotEqual(rules.fingerprint(old),rules.fingerprint({'items':[{'rate':10000.01,'qty':1}],'taxes':[{'rate':5}]}))
        self.assertNotEqual(rules.fingerprint(old),rules.fingerprint({'items':[{'rate':10000,'qty':1}],'taxes':[{'rate':0}]}))
    def test_framework_timestamps_and_empty_images_are_equivalent(self):
        old={'modified':'old','docstatus':0,'workflow_state':'Pending','items':[{'image':'','rate':60,'docstatus':0}]}
        new={'modified':'new','docstatus':1,'workflow_state':'Approved','items':[{'image':None,'rate':60,'docstatus':1}]}
        self.assertEqual(rules.fingerprint(old),rules.fingerprint(new))
    def test_cannot_direct_submit_or_cancel(self):
        with self.assertRaises(ValueError):rules.require_transition('Pending','Pending',0,1,0)
        with self.assertRaises(ValueError):rules.require_transition('Approved','Approved',1,2,1)
        rules.require_transition('Pending','Approved',0,1,1)
        rules.require_transition('Approved','Rejected',1,2,2)

if __name__=='__main__':unittest.main()
