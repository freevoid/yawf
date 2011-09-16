# -*- coding: utf-8 -*-

allow_to_all = lambda obj, sender: True
restrict_to_all = lambda obj, sender: False


class BasePermissionChecker(object):

    def __init__(self, *checkers):
        self._checkers = list(checkers)
        super(BasePermissionChecker, self).__init__()

    def fill_cache(self, obj, sender):
        cache = {}
        for c in set(self.get_atomical_checkers()):
            cache[c] = c(obj, sender)
        return cache

    def get_atomical_checkers(self):
        for c in self._checkers:
            if isinstance(c, BasePermissionChecker):
                for child_c in c.get_atomical_checkers():
                    yield child_c
            else:
                 yield c

    def perform_child_checker(self, checker, obj, sender, cache):
        if isinstance(checker, BasePermissionChecker):
            return checker(obj, sender, cache=cache)
        else:
            cache_result = cache.get(checker, None)
            return (cache_result
                if cache_result is not None
                else checker(obj, sender))

    def add_checker(self, checker):
        self._checkers.append(checker)

    def __and__(self, other):
        return AndChecker(self, other)

    __rand__ = __and__

    def __invert__(self):
        return NotChecker(self)

    def __or__(self, other):
        return OrChecker(self, other)

    __ror__ = __or__


class AndChecker(BasePermissionChecker):

    def __call__(self, obj, sender, cache=None):
        if cache is None:
            cache = self.fill_cache(obj, sender)

        return all(
            self.perform_child_checker(c, obj, sender, cache=cache)
            for c in self._checkers)

    def __and__(self, other):
        self.add_checker(other)
        return self


class OrChecker(BasePermissionChecker):

    def __call__(self, obj, sender, cache=None):
        if cache is None:
            cache = self.fill_cache(obj, sender)

        return any(
            self.perform_child_checker(c, obj, sender, cache=cache)
            for c in self._checkers)

    def __or__(self, other):
        self.add_checker(other)
        return self


class NotChecker(BasePermissionChecker):

    def __init__(self, checker):
        self._invertable_checker = checker
        super(NotChecker, self).__init__(checker)

    def __call__(self, obj, sender, cache=None):
        if cache is None:
            cache = self.fill_cache(obj, sender)

        return not self.perform_child_checker(self._invertable_checker,
                obj, sender, cache=cache)

    def __invert__(self):
        return self._invertable_checker


C = AndChecker
