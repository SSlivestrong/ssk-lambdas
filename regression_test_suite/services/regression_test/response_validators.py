# AO response validation functions
from difflib import HtmlDiff
import json

diff = HtmlDiff()

class ArfComparator():
    def __init__(self, arf1, arf2):
        self.segments1 = arf1.split('@')
        self.segments2 = arf2.split('@')
    
    def mask_segment(self, s, groups, mask_char):
        s_list = list(s)
        for start, end in groups:
            for i in range(start, end):
                s_list[i] = mask_char
        return ''.join(s_list)
        
    def match(self):
        for seg1, seg2 in zip(self.segments1, self.segments2):
            if len(seg1)>0 and len(seg2)>0:
                assert seg1[:3] == seg2[:3] # assert exact sequence
                if seg1.startswith('110'):
                    # mask date time and M-
                    seg1 = self.mask_segment(seg1,[(7,19),(27,27+int(seg1[25:27]))],'X')
                    seg2 = self.mask_segment(seg2,[(7,19),(27,27+int(seg2[25:27]))],'X')
                elif seg1.startswith('100'):
                    # mask date time and M-
                    seg1 = self.mask_segment(seg1,[(8,20),(41,len(seg1))],'X')
                    seg2 = self.mask_segment(seg2,[(8,20),(41,len(seg2))],'X')
                assert seg1 == seg2 # compare segment value
        return True

# depth-first traversal of response payloads
def match_dicts_recursively(dict1, dict2, ignore_values, parent_key=None):
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        keys1, keys2 = dict1.keys(), dict2.keys()
        assert keys1 == keys2 # assert exact keys
        return all(match_dicts_recursively(dict1[k], dict2[k], ignore_values, k) for k in keys1)
    elif isinstance(dict1, list) and isinstance(dict2, list):
        list_match = []
        for d1, d2 in zip(dict1, dict2): # assert exact sequence
            list_match.append(match_dicts_recursively(d1, d2, ignore_values, parent_key))
        return all(list_match)
    else:
        leaf_match = dict1 == dict2 # assert exact values
        if not leaf_match:
            if dict1 in ignore_values and dict2 in ignore_values: # match exceptions
                leaf_match = True
            elif parent_key == 'credit_profile':
                arf_comp = ArfComparator(dict1, dict2)
                leaf_match = arf_comp.match()
            else:
                pass
        return leaf_match

def match_ao_response(req_payload, current_payload, baseline_payload):
    is_match = True
    html_diff = None
    if baseline_payload is None:
        if not 'INVALIDSOLUTIONUID' in json.dumps(req_payload):
            # invalid solution_id edgecase does not have auditlog message for ao_response
            is_match = False
    else:
        try:
            is_match = match_dicts_recursively(current_payload, baseline_payload, 
                [current_payload['payload']['go_transaction_id'], baseline_payload['payload']['go_transaction_id']])
        except:
            is_match = False
    if not is_match:
        html_diff = diff.make_file(json.dumps(baseline_payload, indent=4).replace('@', '@\n').splitlines(), 
                                          json.dumps(current_payload, indent=4).replace('@', '@\n').splitlines())
        
    return is_match, html_diff