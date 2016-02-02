from django.db import models
from django.db.models import F
from mptt.models import MPTTModel, TreeForeignKey


class Node(MPTTModel):
    """
    For children, all the roles come first, then collections.
    """
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    kind = models.CharField(null=True, blank=True, max_length=100, db_index=False)
    kind_id = models.IntegerField(null=True, blank=True, db_index=False)

    class Meta:
        index_together = [
            ['kind', 'kind_id']
        ]

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


class Facility(CollectionOrRole):
    def add_admin(self, fa):
        self.add_role(fa, "admin")

    def add_classroom(self, classroom):
        self.add_subcollection(classroom)


class Classroom(CollectionOrRole):
    def add_coach(self, coach):
        self.add_role(coach, "coach")

    def add_learner_group(self, lg):
        self.add_subcollection(lg)


class LearnerGroup(CollectionOrRole):
    def add_learner(self, learner):
        self.add_role(learner, "learner")


class User(models.Model):
    def is_learner_in_class_of(self, user):
        return self.is_learner_in_class_of_smart(user)

    def is_learner_in_class_of_naive(self, user):
        # Takes a bunch of queries
        coach_nodes = Node.objects.filter(id__in=[c.node.id for c in user.coach_roles.all()])
        is_learner = [cn.get_descendants().filter(kind="learner", kind_id=self.id) for cn in coach_nodes]
        return any(is_learner)

    def is_learner_in_class_of_smart(self, user):
        return any(self.learner_nodes_in_class_of_queryset(user))

    def learner_nodes_in_class_of_queryset(self, user):
        # 1 query to follow user-role relationship
        coach_query = user.get_my_coach_nodes()
        # We get the lft and rght values so we can use them directly to get descendants, resulting in 1 query...
        # Otherwise we'd first have to filter on the node.id and *then* get descendants, resulting in 2 queries.
        coach_node_vals = [(i.node.lft, i.node.rght, i.node.tree_id) for i in coach_query]
        big_q = []
        for lft, rght, tree_id in coach_node_vals:
            # little_q gets descendants. See https://github.com/django-mptt/django-mptt/blob/master/mptt/models.py#L566
            little_q = models.Q(tree_id=tree_id) & models.Q(lft__gte=lft) & models.Q(lft__lte=rght)
            if big_q:
                # We OR each little_q together to get *all* descendants for the coach nodes in one query
                big_q |= little_q
            else:
                big_q = little_q
        if big_q:
            # The AND finally asserts that the descendants contain the user.id we're looking for
            return Node.objects.filter(big_q & models.Q(kind="learner", kind_id=self.id))
        else:
            return Node.objects.none()

    def get_my_coach_nodes(self):
        return self.coach_roles.select_related('node').all()


class Admin(CollectionOrRole):
    user = models.ForeignKey(User, related_name='admin_roles')


class Coach(CollectionOrRole):
    user = models.ForeignKey(User, related_name='coach_roles')


class Learner(CollectionOrRole):
    user = models.ForeignKey(User, related_name='learner_roles')


class RelatedObject(models.Model):
    user = models.ForeignKey(User)

    @classmethod
    def all_that_user_has_perms_for(cls, coach: User):
        coach_nodes = Node.objects.filter(id__in=coach.get_my_coach_nodes().values("node"))
        if coach_nodes:
            all_coaches_learners = User.objects.filter(
              learner_roles__node__in=coach_nodes.get_descendants()
            )
        else:
            all_coaches_learners = User.objects.none()
        return RelatedObject.objects.filter(user__in=all_coaches_learners)
