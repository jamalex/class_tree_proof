import progressbar
import random

from django.core.management.base import BaseCommand
from django.core.management import call_command
from natural_tree.models import *

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

    Best used with an in-memory database!
    """
    def handle(self, **options):
        call_command("migrate")

        users = [User() for i in range(NUM_USERS)]
        User.objects.bulk_create(users, batch_size=BC_BATCH_SIZE)
        users = list(User.objects.all())

        facility = Collection.objects.create(type="facility")
        classrooms = [Collection.objects.create(parent=facility, type="classroom") for i in range(NUM_CLASS)]

        bar = progressbar.ProgressBar()
        lgs_per_class = int(NUM_LGS/NUM_CLASS)
        for classroom in bar(Collection.objects.filter(type="classroom")):
            coaches = [Role.objects.create(user=random.sample(users, 1)[0], collection=classroom, type="coach") for i in range(COACHES_PER_CLASS)]
            lgs = [Collection.objects.create(parent=classroom, type="learner_group") for i in range(lgs_per_class)]
            for lg in Collection.objects.filter(type="learner_group", parent=classroom):
                learners = [Role.objects.create(user=random.sample(users, 1)[0], collection=lg, type="learner") for i in range(USERS_PER_LG)]

        total_expected = NUM_LGS*(1 + USERS_PER_LG) + NUM_CLASS*(1 + COACHES_PER_CLASS)
        actual = Collection.objects.get(id=facility.id).get_descendants().count() + Role.objects.count()
        assert actual == total_expected, "actual: {}\nexpected {}".format(actual, total_expected)
        call_command('dumpdata', output="treedump.json")
        print("Total number of nodes + roles: {}".format(total_expected))
