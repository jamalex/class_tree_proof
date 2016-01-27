from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class Collection(MPTTModel):
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    type = models.CharField(max_length=50)


class User(models.Model):
    roles = models.ManyToManyField(Collection, through='Role')

    def is_learner_in_class_of(self, coach):
        classes = coach.my_classes()
        learners = classes.get_descendants().filter(role__user=self, role__type="learner")
        return any(learners)

    def my_classes(self):
        return Collection.objects.filter(role__user=self, role__type="coach", type="classroom")


class Role(models.Model):
    type = models.CharField(max_length=50)
    collection = models.ForeignKey(Collection)
    user = models.ForeignKey(User)


class RelatedObject(models.Model):
    user = models.ForeignKey(User)

    @classmethod
    def all_that_user_has_perms_for(cls, coach: User):
        coaches_learner_roles = []
        for learner_group in coach.my_classes().get_descendants():
            coaches_learner_roles += learner_group.role_set.filter(type="learner")
        return RelatedObject.objects.filter(user__in=User.objects.filter(
            role__in=coaches_learner_roles
        ))
