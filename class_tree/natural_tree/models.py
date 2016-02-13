from django.db import models, connection
from mptt.models import MPTTModel, TreeForeignKey


class Collection(MPTTModel):
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    type = models.CharField(max_length=50)


class User(models.Model):
    roles = models.ManyToManyField(Collection, through='Role')

    def is_learner_in_class_of_count(self, coach):
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

    def is_learner_in_class_of(self, coach):

        params = {
            "role_table": Role._meta.db_table,
            "collection_table": Collection._meta.db_table,
            "user_column": Role._meta.get_field('user').column,
            "collection_column": Role._meta.get_field('collection').column,
            "ancestor_collection": "anc",
            "descendent_collection": "desc",
            "user_role": Role._meta.db_table,
            "learner_role": "learner_role",
            "learner_id": self.id, # change later
            "user_id": coach.id, # change later
        }

        tables = [item.format(**params) for item in [
            '"{collection_table}" AS "{ancestor_collection}"',
            '"{collection_table}" AS "{descendent_collection}"',
            '"{role_table}" AS "{learner_role}"',
        ]]

        conditions = [item.format(**params) for item in [
            "{user_role}.{collection_column} = {ancestor_collection}.id",
            "{user_role}.type != 'learner'",
            "{user_role}.{user_column} = {user_id}",
            "{learner_role}.{collection_column} = {descendent_collection}.id",
            "{learner_role}.type = 'learner'",
            "{learner_role}.{user_column} = {learner_id}",
            "{descendent_collection}.lft BETWEEN {ancestor_collection}.lft AND {ancestor_collection}.rght",
        ]]

        queryset = Role.objects.extra(tables=tables, where=conditions)

        return queryset.exists()


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
