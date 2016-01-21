import progressbar
import random
import time

from django.test import TestCase
from .models import *


class TestSanity(TestCase):
    """
    Just checks that the User.is_learner_in_class_of method works as expected.
    """
    def setUp(self):
        classroom = Collection.objects.create(type="classroom")
        lg = Collection.objects.create(type="learner_group", parent=classroom)
        coach_user, learner_user = self.coach, self.learner = User.objects.create(), User.objects.create()

        coach_role = Role.objects.create(user=coach_user, collection=classroom, type="coach")
        learner_role = Role.objects.create(user=learner_user, collection=lg, type="learner")

    def test_true(self):
        self.assertTrue(self.learner.is_learner_in_class_of(self.coach))

    def test_false(self):
        self.assertFalse(self.coach.is_learner_in_class_of(self.learner))


class TestBenchmark(TestCase):
    def test_is_learner_timing(self):
        random.seed(42)
        users = list(User.objects.all())
        coaches = random.sample(users, 50)
        avg_time = 0
        count = 0

        bar = progressbar.ProgressBar()
        for coach in bar(coaches):
            learners = random.sample(users, 50)
            for learner in learners:
                start = time.time()
                learner.is_learner_in_class_of(coach)
                end = time.time()
                count += 1
                avg_time = (avg_time*(count-1) + (end-start))/count

        print("Average time (ms) for `natural_tree` app's `User.is_learner_in_class_of` method: {}".format(avg_time))
