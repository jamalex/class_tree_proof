import progressbar
import random
import time

from django.test import TestCase
from .models import *


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
