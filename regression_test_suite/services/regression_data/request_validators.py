# request validation functions for external AO apis

# depth-first traversal of request payloads
def match_dicts_recursively(dict1, dict2, ignore_values=[], ignore_keys=[], parent_key=None):
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        keys1, keys2 = dict1.keys(), dict2.keys()
        assert keys1 == keys2 # assert exact keys
        return all(match_dicts_recursively(dict1[k], dict2[k], 
            ignore_values=ignore_values, ignore_keys=ignore_keys, parent_key=k) for k in keys1)
    elif isinstance(dict1, list) and isinstance(dict2, list):
        list_match = []
        for d1, d2 in zip(dict1, dict2): # assert exact sequence
            list_match.append(match_dicts_recursively(d1, d2, 
            ignore_values=ignore_values, ignore_keys=ignore_keys, parent_key=parent_key))
        return all(list_match)
    else:
        leaf_match = dict1 == dict2 # assert exact values
        if not leaf_match:
            if dict1 in ignore_values or dict2 in ignore_values: # match exceptions
                leaf_match = True
            elif parent_key in ignore_keys:
                leaf_match = True
            else:
                pass
        return leaf_match

def ccr_base_validate(current_payload, baseline_payload):
    is_match = True
    try:
        for key in current_payload:
            if key != 'inquiry':
                assert current_payload[key] == baseline_payload[key]
            else:
                # match inquiry string
                for current_block, baseline_block in zip(current_payload['inquiry'].split(';'), baseline_payload['inquiry'].split(';')):
                    if current_block != baseline_block:
                        if current_block.startswith('VERIFY'):
                            assert set(current_block[7:].split('/')) == set(baseline_block[7:].split('/'))
                        elif current_block.startswith('M-'):
                            continue
                        else:
                            is_match = False
                            break
    except:
        is_match = False
    return is_match

def proctor_base_validate(current_payload, baseline_payload):
    return current_payload == baseline_payload

def pinning_base_validate(current_payload, baseline_payload):
    return current_payload == baseline_payload

def clarity_base_validate(current_payload, baseline_payload):
    return current_payload == baseline_payload

def atb_base_validate(current_payload, baseline_payload, ignore_values):
    is_match = True
    try:
        is_match = match_dicts_recursively(current_payload, baseline_payload, 
                                           ignore_values=ignore_values)
    except:
        is_match = False
    return is_match

def crosscore_token_base_validate(current_payload, baseline_payload):
    return current_payload == baseline_payload

def crosscore_base_validate(current_payload, baseline_payload):
    return current_payload == baseline_payload

def criteria_base_validate(current_payload, baseline_payload):
    return current_payload == baseline_payload

def decision_base_validate(current_payload, baseline_payload):
    return current_payload == baseline_payload

def sagemaker_validate(current_payload, baseline_payload):
    is_match = True
    try:
        is_match = match_dicts_recursively(current_payload, baseline_payload, 
                                        ignore_keys=["experian_consumer_key"])
    except:
        is_match = False
    return is_match