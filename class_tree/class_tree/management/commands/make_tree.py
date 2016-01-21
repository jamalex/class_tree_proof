import progressbar
import random

from django.core.management.base import BaseCommand
from django.core.management import call_command
from class_tree.models import *

NUM_USERS = 1000
NUM_LGS = 500
USERS_PER_LG = 10
NUM_CLASS = 100
COACHES_PER_CLASS = 5

BC_BATCH_SIZE = 500


class Command(BaseCommand):
    """
    Creates a tree structure that we can use as a fixture in tests.
    Outputs "treedump.json" database dump in the current directory, that you can copy to the "fixtures" directory
    of this app.
    """
    def handle(self, **options):
        # Some of the weird Model.object.get(id=instance.id).somemethod() calls are so that cached related objects
        # are properly updated.
        call_command("migrate")

        bar = progressbar.ProgressBar()
        users = []
        for i in bar(range(NUM_USERS)):
            users += [User()]
        User.objects.bulk_create(users, batch_size=BC_BATCH_SIZE)
        users = list(User.objects.all())

        bar = progressbar.ProgressBar()
        lgs = []
        for i in bar(range(NUM_LGS)):
            lgs.append(LearnerGroup())
        LearnerGroup.objects.bulk_create(lgs, batch_size=BC_BATCH_SIZE)
        lgs = LearnerGroup.objects.all()

        bar = progressbar.ProgressBar()
        for lg in bar(lgs):
            for user in random.sample(users, USERS_PER_LG):
                learner = Learner.objects.create(user=user)
                lg.add_learner(learner)
            assert LearnerGroup.objects.get(id=lg.id).node.get_descendants().count() == USERS_PER_LG

        cs = [Classroom() for i in range(NUM_CLASS)]
        Classroom.objects.bulk_create(cs, batch_size=BC_BATCH_SIZE)
        cs = Classroom.objects.all()
        facility = Facility.objects.create()
        lgs_per_class = int(NUM_LGS / NUM_CLASS)
        lgs = LearnerGroup.objects.all()

        bar = progressbar.ProgressBar()
        for i, classroom in bar(enumerate(cs)):
            for lg in lgs[i*lgs_per_class:(i+1)*lgs_per_class]:
                classroom.add_learner_group(lg)

            for j in range(COACHES_PER_CLASS):
                coach = Coach.objects.create(user=random.sample(users, 1)[0])
                classroom.add_coach(coach)

            expected = COACHES_PER_CLASS + lgs_per_class*(1 + USERS_PER_LG)
            assert Classroom.objects.get(id=classroom.id).node.get_descendants().count() == expected, "actual: {}\n expected: {}".format(Classroom.objects.get(id=classroom.id).node.get_descendants().count(), expected)
            Facility.objects.get(id=facility.id).add_classroom(Classroom.objects.get(id=classroom.id))

        total_expected = NUM_LGS*(1 + USERS_PER_LG) + NUM_CLASS*(1 + COACHES_PER_CLASS)
        assert Facility.objects.get(id=facility.id).node.get_descendants().count() == total_expected,  "actual: {}\n expected: {}".format(Facility.objects.get(id=facility.id).node.get_descendants().count(), total_expected)
        call_command('dumpdata', output="treedump.json")
        print("Total number of nodes: {}".format(total_expected))
