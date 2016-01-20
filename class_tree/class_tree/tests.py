from django.test import TestCase
from .models import *


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
        with self.assertNumQueries(3):
            self.assertTrue(self.user2.is_learner_in_class_of(self.user1))

        with self.assertNumQueries(1):
            self.assertFalse(self.user1.is_learner_in_class_of(self.user2))
