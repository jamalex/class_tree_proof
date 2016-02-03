from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class Collection(MPTTModel):
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    type = models.CharField(max_length=50)


class User(models.Model):
    roles = models.ManyToManyField(Collection, through='Role')

    def is_learner_in_class_of(self, coach):
        sql = '''
        SELECT
            COUNT(desc.id)
        FROM
            natural_tree_collection anc, natural_tree_collection desc
        INNER JOIN
            natural_tree_role coach_role, natural_tree_role learner_role
        WHERE
            coach_role.collection_id = anc.id AND
            learner_role.collection_id = desc.id AND
            coach_role.type = "coach" AND
            learner_role.type = "learner" AND
            coach_role.user_id = {coach_id} AND
            learner_role.user_id = {learner_id} AND
            desc.lft BETWEEN anc.lft AND anc.rght
        '''.format(coach_id=coach.id, learner_id=self.id)
        cursor = connection.cursor()
        cursor.execute(sql)
        return cursor.fetchone()[0] > 0

    def is_learner_in_class_of_old(self, coach):
        classes = coach.my_classes()
        learners = classes.get_descendants().filter(role__user=self, role__type="learner")
        return any(learners)

    def my_classes(self):
        return Collection.objects.filter(role__user=self, role__type="coach", type="classroom")


class Role(models.Model):
    type = models.CharField(max_length=50)
    collection = models.ForeignKey(Collection, db_index=False)
    user = models.ForeignKey(User, db_index=False)

    class Meta:
        index_together = [
            ['collection', 'type'],
            ['user', 'type'],
        ]


class RelatedObject(models.Model):
    user = models.ForeignKey(User)

    @classmethod
    def all_that_user_has_perms_for(cls, coach: User):
        return RelatedObject.objects.filter(user__in=User.objects.filter(
            role__collection__in=coach.my_classes().get_descendants(),
            role__type="learner"
        ))
