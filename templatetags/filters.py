from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    from collections.abc import Mapping

    # logger.info("dictionary type: {}".format(type(dictionary)))
    # logger.info("dictionary: {}".format(dictionary))
    # logger.info("key: {}".format(key))

    try:
        if isinstance(key, Decimal):
            key = str(key)

        if dictionary is None:
            ret = None
        else:
            if isinstance(dictionary, Mapping):
                if key == "items":
                    ret = list(dictionary.items())
                else:
                    ret = dictionary.get(key)
            elif isinstance(dictionary, list):
                dictionary_tmp = dict(dictionary)
                ret = dictionary_tmp.get(key)
            else:
                ret = getattr(dictionary, key)
    except:
        ret = None

    # logger.info("ret: {}".format(ret))
    return ret

