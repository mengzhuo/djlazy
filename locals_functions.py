# -*- coding: utf-8 -*-s#

import inspect
import re

__all__ = ('tame_locals', 'smart_request', 'StruggleError',
           'IndependenceError')


STANDARD_DJANGO_VIEW_LOCALS = ('request','req' )
CALLER_LINE_REGEX = r'\(?([\w\-]+,?)*\)?=.*'


class IndependenceError(Exception):
    pass


def smart_request(request_dict=None):
    """
    return tuple as what caller asked

    Example:
    from djlazy import smart_request

    def my_view(request):

        (foo, parrot) = smart_request()
    """
    # XXX:bad formatting
    frame_stacks = inspect.getouterframes(inspect.currentframe())[:2]
    try:
        caller_stack = frame_stacks[1]
    except IndexError:
        raise IndependenceError('smart_request can not live alone')

    caller_line = caller_stack[4][0].replace(' ', '')
    """
    FIXME can't retrive if the code looks like:
    (foo,
        bar ) = smart_request(request.GET)
    """
    if not request_dict:
        try:
            # default with Django request.GET
            request_dict = caller_stack[0].f_locals.get('request').get('GET')
        except AttributeError:
            raise TypeError(
                'function %s doesnot contain request in locals()' %
                caller_stack[3])

    match = re.match(CALLER_LINE_REGEX, caller_line)
    if match:
        caller_args = caller_line.split('=')[0].strip('()').split(',')
        update_targets = caller_args
        return [request_dict.get(key) for key in update_targets]
    else:
        raise ValueError('smart_request can not be call without =')


class StruggleError(Exception):
    pass


def tame_locals(exclude=None, include=None):
    """
    return Caller's locals() with filters

    :param exclude: excluded keys from return
    :type exclude: string, list
    :param include: included keys in return
    :type include: string, list
    :returns: filtered dictionary
    :rtype: dict

    Example:

    from djlazy import tame_locals
    def my_view(request):
        foo = 'bar'
        return render('foo.html', tame_locals())
    """
    if exclude and include:
        raise StruggleError("exclude and include can't be set together")
    elif not (exclude or include):
        exclude = STANDARD_DJANGO_VIEW_LOCALS

    outer_stack = inspect.getouterframes(inspect.currentframe())[:2]
    try:
        result = outer_stack[1][0].f_locals
        if exclude:
            # "in" statment support with string
            # therefor we don't need to check type :)
            result = {key: value for key,
                      value in result.items() if key not in exclude}
        if include:
            result = {key: value for key,
                      value in result.items() if key in include}
    except IndexError:
        result = {}
    except TypeError:
        pass
    finally:
        return result


def test_tame_locals():
    pass
    

def test_smart_request():
    pass


if __name__ == "__main__":
    #TODO: finish test units
    test_tame_locals()
    test_smart_request()
