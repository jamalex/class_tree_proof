from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class Collection(MPTTModel):
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    type = models.CharField(max_length=50)


class User(models.Model):
    roles = models.ManyToManyField(Collection, through='Role', related_query_name='roles')

    def is_learner_in_class_of(self, user):
        classes = Collection.objects.filter(role__user=user, role__type="coach", type="classroom")
        learners = classes.get_descendants().filter(role__user=self, role__type="learner")
        return any(learners)


class Role(models.Model):
    type = models.CharField(max_length=50)
    collection = models.ForeignKey(Collection)
    user = models.ForeignKey(User)


class RelatedObject(models.Model):
    user = models.ForeignKey(User)

    @classmethod
    def all_that_user_has_perms_for(cls, coach: User):
        pass
