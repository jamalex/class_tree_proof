import progressbar
import random
import time

from django.test import TestCase
from .models import *


class TestRelatedObject(TestCase):

    def setUp(self):
        classroom1 = Classroom.objects.create()
        user1, user2 = self.user1, self.user2 = User.objects.create(), User.objects.create()
        lg = LearnerGroup.objects.create()

        coach = Coach.objects.create(user=user1)
        learner = Learner.objects.create(user=user2)

        classroom1.add_coach(coach)
        classroom1.add_learner_group(lg)
        lg.add_learner(learner)

        self.related_object = RelatedObject.objects.create(user=user2)

    def test_coach_perms(self):
        self.assertEqual(self.related_object, RelatedObject.all_that_user_has_perms_for(self.user1).first())

    def test_learner_perms(self):
        self.assertFalse(RelatedObject.all_that_user_has_perms_for(self.user2))


class TestBenchmark(TestCase):
    fixtures = ["class_treedump.json"]

    def test_sanity(self):
        facility = Facility.objects.all().first()
        self.assertEqual(facility.node.get_descendants().count(), 6100)  # Magic number comes from make_tree cmd

    def test_is_learner_timing(self):
        random.seed(42)
        users = list(User.objects.all())
        coaches = users
        tot_time = 0
        count = 0

        bar = progressbar.ProgressBar()
        for coach in bar(coaches):
            learners = random.sample(users, 50)
            for learner in learners:
                start = time.time()
                learner.is_learner_in_class_of(coach)
                end = time.time()
                count += 1
                tot_time += (end-start)

        avg_time = tot_time/count
        print("Average time (s) for `class_tree` app's \n\t`User.is_learner_in_class_of` method: {}".format(avg_time))


class TestQueries(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestQueries, cls).setUpClass()
        classroom1 = Classroom.objects.create()
        user1, user2 = User.objects.create(), User.objects.create()
        lg = LearnerGroup.objects.create()

        coach = Coach.objects.create(user=user1)
        learner = Learner.objects.create(user=user2)

        classroom1.add_coach(coach)
        classroom1.add_learner_group(lg)
        lg.add_learner(learner)

        cls.user1 = user1
        cls.user2 = user2

    def test(self):
        with self.assertNumQueries(2):
            self.assertTrue(self.user2.is_learner_in_class_of(self.user1))

        with self.assertNumQueries(1):
            self.assertFalse(self.user1.is_learner_in_class_of(self.user2))
