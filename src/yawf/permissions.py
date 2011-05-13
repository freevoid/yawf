# -*- coding: utf-8 -*-


def join_perms(*perm_checkers):
    '''
    Join all checkers in perm_checkers in single with logical AND rule.

    Returns single checker function.
    '''
    # TODO: make JoinedChecker class that encapsulates join logic to be
    # able to use check cache when checking for available messages
    return lambda obj, sender: all(c(obj, sender) for c in perm_checkers)


allow_to_all = lambda obj, sender: True
restrict_to_all = lambda obj, sender: False

class PermissionChecker(object):

    def __call__(self, obj, sender, cache=None):
        if cache is None:
            cache = {}

    def __and__(self, other):
        pass

    def __or__(self, other):
        return self

    def __init__(self, *atomical_checkers):
        self._atomical_checkers = atomical_checkers
