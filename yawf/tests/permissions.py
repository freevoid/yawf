from django.test import TestCase

from yawf.permissions import C, allow_to_all, restrict_to_all

__all__ = ('PermissionsTestCase',)


class PermissionsTestCase(TestCase):

    @staticmethod
    def call_count(func):
        func.call_count = 0
        def wrapper(*args):
            func.call_count += 1
            return func(*args)
        wrapper.func = func
        return wrapper

    def setUp(self):
        self.sender_is_even = self.call_count(lambda obj, sender: sender & 1 == 0)
        self.obj_is_even = self.call_count(lambda obj, sender: obj & 1 == 0)

        self.complex_checker = (
            C(self.obj_is_even, self.sender_is_even) |
                allow_to_all & ~C(self.sender_is_even) & allow_to_all)

    def test_custom_sender(self):
        self.assertFalse(self.sender_is_even(None, 3))
        self.assertTrue(self.sender_is_even(None, 4))
        self.assertFalse(self.obj_is_even(3, None))
        self.assertTrue(self.obj_is_even(4, None))

    def test_inversion(self):
        sender_is_odd = ~C(self.sender_is_even)

        self.assertTrue(sender_is_odd(None, 3))
        self.assertFalse(sender_is_odd(None, 4))

        sender_is_even = ~C(sender_is_odd)
        self.assertFalse(sender_is_even(None, 3))
        self.assertTrue(sender_is_even(None, 4))

    def test_inversion_invariance(self):
        sender_is_even = C(self.sender_is_even)
        sender_is_odd = ~sender_is_even
        sender_is_even_again = ~sender_is_odd
        self.assertTrue(sender_is_even is sender_is_even_again)

    def test_checker_expressions(self):
        complex_checker = self.complex_checker
        self.assertTrue(complex_checker(2, 2))
        self.assertTrue(complex_checker(0, 1))
        self.assertFalse(complex_checker(1, 2))

        new_allow_to_all = allow_to_all | complex_checker
        self.assertTrue(new_allow_to_all(2, 2))
        self.assertTrue(new_allow_to_all(0, 1))
        self.assertTrue(new_allow_to_all(1, 2))

        new_restrict_to_all = complex_checker & restrict_to_all
        self.assertFalse(new_restrict_to_all(2, 2))
        self.assertFalse(new_restrict_to_all(0, 1))
        self.assertFalse(new_restrict_to_all(1, 2))

    def test_atomics(self):
        complex_checker = self.complex_checker
        self.assertEqual(len(set(complex_checker.get_atomical_checkers())), 3)

    def test_cache(self):
        '''
        Call complex checker three times and check times that checker
        functions actually been called
        '''
        complex_checker = self.complex_checker
        self.assertEqual(self.sender_is_even.func.call_count, 0)
        self.assertEqual(self.obj_is_even.func.call_count, 0)
        complex_checker(0, 1)
        self.assertEqual(self.sender_is_even.func.call_count, 1)
        self.assertEqual(self.obj_is_even.func.call_count, 1)
        complex_checker(2, 2)
        self.assertEqual(self.sender_is_even.func.call_count, 2)
        self.assertEqual(self.obj_is_even.func.call_count, 2)
        complex_checker(1, 2)
        self.assertEqual(self.sender_is_even.func.call_count, 3)
        self.assertEqual(self.obj_is_even.func.call_count, 3)

    def test_fill_cache(self):
        cache = self.complex_checker.fill_cache(2, 2)
        allower = allow_to_all.get_atomical_checkers().next()
        self.assertEqual(len(cache), 3)
        self.assertTrue(self.sender_is_even in cache)
        self.assertTrue(self.obj_is_even in cache)
        self.assertTrue(allower in cache)

    def test_cyclic(self):
        or_checker = C(self.sender_is_even) | C(self.obj_is_even)
        atom_checkers = list(or_checker.get_atomical_checkers())
        or_checker |= or_checker
        self.assertListEqual(
            atom_checkers,
            list(or_checker.get_atomical_checkers()))

        and_checker = C(self.sender_is_even, self.obj_is_even)
        and_checker &= and_checker
        atom_checkers = list(and_checker.get_atomical_checkers())
        self.assertListEqual(
            atom_checkers,
            list(and_checker.get_atomical_checkers()))
