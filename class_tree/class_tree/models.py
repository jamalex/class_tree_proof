from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class Node(MPTTModel):
    """
    For children, all the roles come first, then collections.
    """
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    kind = models.CharField(null=True, blank=True, max_length=100)
    kind_id = models.IntegerField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super(Node, self).__init__(*args, **kwargs)

    def insert_child(self, child):
        old_child = Node.objects.get(id=self.id).get_children().first()
        child.move_to(self, position='first-child')
        if old_child:
            old_child.move_to(child, position='first-child')

    def add_role(self, node):
        self.insert_child(node)

    def add_subcollection(self, node):
        descendants = Node.objects.get(id=self.id).get_descendants().all()
        if descendants:
            first_collection = descendants.filter(kind='collection').first()
            if first_collection:
                first_collection.insert_child(node)
            else:
                descendants.last().insert_child(node)
        else:
            node.move_to(self, position='first-child')


def make_new_node():
    node = Node.objects.create()
    return node.id


class CollectionOrRole(models.Model):
    node = TreeForeignKey(Node, null=False, blank=False, db_index=True, default=make_new_node)

    class Meta:
        abstract = True

    def add_role(self, role, kind):
        self.node.add_role(role.node)
        role.node.kind = kind
        role.node.kind_id = role.user.id
        role.node.save()

    def add_subcollection(self, coll):
        self.node.add_subcollection(coll.node)
        coll.node.kind = "collection"
        coll.node.save()


class Classroom(CollectionOrRole):
    def add_coach(self, coach):
        self.add_role(coach, "coach")

    def add_learner_group(self, lg):
        return self.add_subcollection(lg)


class LearnerGroup(CollectionOrRole):
    def add_learner(self, learner):
        self.add_role(learner, "learner")


class User(models.Model):
    def is_learner_in_class_of(self, user):
        return self.is_learner_in_class_of_smart(user)

    def is_learner_in_class_of_naive(self, user):
        coach_nodes = Node.objects.filter(id__in=[c.node.id for c in user.coach_roles.all()])
        is_learner = [cn.get_descendants().filter(kind="learner", kind_id=self.id) for cn in coach_nodes]
        return any(is_learner)

    def is_learner_in_class_of_smart(self, user):
        # 1 query to follow user-role relationship
        coach_query = list(user.coach_roles.select_related('node').all().values('node'))
        coach_node_ids = [i['node'] for i in coach_query]
        # 2 queries -- 1 to get all "coach" nodes for the user, and another to check descendants!
        # Can we reduce it to 1, by avoiding querying for the "coach" nodes and combining it with "get_descendants"?
        is_learner = Node.objects.filter(id__in=coach_node_ids).get_descendants().filter(kind="learner", kind_id=self.id)
        return any(is_learner)


class Coach(CollectionOrRole):
    user = models.ForeignKey(User, related_name='coach_roles')


class Learner(CollectionOrRole):
    user = models.ForeignKey(User, related_name='learner_roles')
