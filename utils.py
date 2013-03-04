# -*- coding: utf-8 -*-s#
import json
import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers.python import Serializer as PythonSerializer
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.utils.encoding import smart_unicode

MAX_ITEM_PER_PAGE = getattr(settings, 'MAX_ITEM_PER_PAGE', 10)
API_VERSION = getattr(settings, 'API_VERSION', 1)


__all__ = ('easy_api', 'easy_serialize', 'EasySerializer', 'do_paginator', 'yield_attrs')


def easy_api(target, status=200, defer=[]):
    """
    input a serialized instance dict
    return a standard json
    """
    try:
        if target.__class__ is str:
            result = target
        else:
            result = easy_serialize(target, defer)

        result = json.dumps(result, cls=DjangoJSONEncoder)
    except Exception as e:
        logger.warn(e)
        status = 202
        result = json.dumps({'apiError': e.message})
    finally:
        return HttpResponse(result,
                            content_type='application/json',
                            status=status)


class EasySerializer(PythonSerializer):
    """
    Most of the time,
    we don't need model or pk show on the API
    """
    internal_use_only = False

    def end_object(self, obj):
        appender = {'pk': smart_unicode(obj._get_pk_val())}
        appender.update(self._current)
        self.objects.append(appender)
        self._current = None

__serialier = EasySerializer()

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
            return {key:value for key, value in dict_to_fil.iteritems()}
    try:
        if target.__class__ is QuerySet:
            result = [filter_defer(item) for item in
                      __serialier.serialize(target)]
        else:
            result = filter_defer(yield_attrs(target), defer)
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
