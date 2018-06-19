from django.test import TestCase
from majority_judgment.tools import get_ranking


class MajorityJudgmentTestCase(TestCase):
    fixtures = ['election.json']

    # def setUp(self):

    def test_ranking(self):
        election_id = 2
        ranking = get_ranking(election_id)
        ranking = [candidate.pk for candidate in ranking]
        real_ranking = [ 2,  3,  4, 13,  6,  7, 15, 14,  8, 12, 16,  5, 11, 17, 10,  1,  9]

        self.assertEqual(ranking, real_ranking)
