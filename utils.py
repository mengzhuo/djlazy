# -*- coding: utf-8 -*-s#
import re
import logging
logger = logging.getLogger(__name__)
import json

from django.db.models.query import QuerySet
from django.db.models import Model
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers import serialize

MAX_ITEM_PER_PAGE = getattr(settings, 'MAX_ITEM_PER_PAGE', 10)
API_VERSION = getattr(settings, 'API_VERSION', 1)


__all__ = ('easy_api', 'easy_serialize', 'do_paginator', 'yield_attrs')


def easy_api(target, status=200, defer=[]):
    """
    input a serialized instance dict
    return a standard json
    """
    def key_to_JSON(key):
        """
        The standard JSON key is fooBar, but according to the PEP8,
        all python vars should looks like foo_bar
        this function cover all foo_bar->fooBar
        """
        return re.sub(r'_(\w)', lambda x: x.group(1).upper(), key)

    try:
        if target.__class__ is QuerySet:
            result = easy_serialize(target, defer)

        elif (Model in target.__class__.mro()) or (target.__class__ is dict):
            # XXX: bad approach
            if not target.__class__ is dict:
                target = easy_serialize(target, defer)

            result = {key_to_JSON(key): value for (
                      key, value) in target.iteritems()}
            result.update({'APIVersion': API_VERSION})

        elif target.__class__ is str:
            result = {target}
        else:
            raise TypeError("Don't support with %s" % target)

        result = json.dumps(result, cls=DjangoJSONEncoder)
    except Exception, e:
        logger.warn(e)
        status = 202
        result = json.dumps({'apiError': e.message})
    finally:
        return HttpResponse(result,
                            content_type='application/json',
                            status=status)


def easy_serialize(target, defer=[]):
    """
    transfer model into dictionary or list depends on
    target is a single or QuerySet
    """
    def filter_defer(dict_to_fil, defer=[]):
        if defer:
            return {key: value
                    for key, value in dict_to_fil.iteritems()
                    if key not in defer}
        else:
            return dict_to_fil
    try:
        if target.__class__ is QuerySet:
            # such type is for single module
            struct = json.loads(serialize('json', target.all()))
            # XXX: re-load is bad for performence... but we don't re-invent
            # serialize
            result = [filter_defer(item.get('fields'), defer)
                      for item in struct]
        else:
            struct = json.loads(serialize('json', [target, ]))[0].get('fields')
            result = filter_defer(struct, defer)
    except AttributeError:
        raise TypeError('%s is not a valid model' % target)
    else:
        return result


def do_paginator(origin_list, page, max_item_per_page=None):
    """
    A paginator like doc says, but using default setting
    """
    try:
        max_item_per_page = int(max_item_per_page)
    except:
        max_item_per_page = MAX_ITEM_PER_PAGE

    paginator = Paginator(origin_list, max_item_per_page)

    try:
        origin_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        origin_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        origin_list = paginator.page(paginator.num_pages)

    return origin_list


def yield_attrs(obj, attr_list=None):
    """
        return objects' attrs into a dict
        if attr_list is empty, try all public attr in __dict__
    """
    result = {}
    if attr_list:
        if type(attr_list) is list:
            result.update({key: getattr(obj, key, None) for key in attr_list})
        else:
            result = getattr(obj, attr_list, None)
    else:
        result.update({key: value for (
            key, value) in obj.__dict__.iteritems() if not key[0] is "_"})

    return result

##### test unit #####
def test_easy_api():
    pass


if __name__ == "__main__":
    # TODO: finish test units
    pass
