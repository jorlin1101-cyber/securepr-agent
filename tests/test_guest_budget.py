import unittest

from securepr_agent.api import GuestReviewBudget


class GuestReviewBudgetTests(unittest.TestCase):
    def test_guest_budget_is_shared_and_renews_after_window(self):
        budget = GuestReviewBudget(limit=2, window_seconds=60)
        self.assertTrue(budget.reserve(now=100))
        self.assertTrue(budget.reserve(now=101))
        self.assertFalse(budget.reserve(now=102))
        self.assertTrue(budget.reserve(now=160))
        self.assertEqual(2, len(budget.events))
