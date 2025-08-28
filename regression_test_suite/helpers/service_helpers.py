import traceback

def update_traceback_item_to_serialize(traceback_item):
    iter1 = lambda item: item.replace('"', "'")
    iter2 = lambda item: item.replace("'", "")
    
    updated_item = iter2(iter1(traceback_item))
    return updated_item

def extract_exception_traceback(xcp):
    """ extract exception and traceback and return """
    traceback_item = traceback.format_exception(xcp)
    if isinstance(traceback_item, list):
        try:
            xcp_detail = update_traceback_item_to_serialize(traceback_item[-2].split("\n")[1].strip()[:-1]).strip() + \
                  ":: " + update_traceback_item_to_serialize(traceback_item[-1].split("\n")[0])
        except:
            xcp_detail = None
        try:
            tb_detail = update_traceback_item_to_serialize(traceback_item[-2].split(",")[0].split("/")[-1][:-1]) + \
                ":: " + update_traceback_item_to_serialize(traceback_item[-2].split(",")[1]).strip()
        except:
            tb_detail = None
        return xcp_detail, tb_detail
    try:
        return str(xcp), traceback.format_exc()
    except:
        return None, None