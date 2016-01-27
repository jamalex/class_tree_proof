What is this?
-------

I encountered a problem at work.
I wrote an email to a friend about it.
Below is the problem as I posed it to him.
Then I thought up a solution, so I decided to make a Django app that demonstrated it.

Read this explanation, look at tests.py, then look at models.py.

Install with this cmd: `pip install -r requirements`.

You can run tests with this script: `manage.py test`.

Terms
----
Sorry for potential confusion! However "teacher" is used interchangeably with "coach", and similarly "learner" is used
interchangeably with "student".

The Question
----- 

We have a hierarchical grouping of objects as in [this diagram](https://docs.google.com/drawings/d/1CI_li7fqYpymWDwbhpjkzpB9es76-nzH5lp4hm7akZA/edit).
The root node is a class, which for children has one or more teachers.
It also has one or more learner groups, and learner groups have one or more students.
Students and teachers are both guaranteed to have no children.

This hierarchy must be encoded in a relational database, and we wish to minimize the number of queries to the db it 
takes to answer certain types of questions about the hierarchy. In fact we have many classes, which are all themselves
children of one root node (the "school"). One class of questions is this:

* (A) Given a student and a teacher, are they both children of the same class?

Depending on how you encode the tree, this question could take a very long time to answer. For instance, if you 
naively encode it the hierarchy as a many-to-many relationship, then such a question requires 3 table joins (at least 
as I understand it): First the tables of students must be joined to learner groups, then learner groups to classes, 
then classes to teachers.

[But there are smarter ways to encode a tree using RDBs!](http://www.sitepoint.com/hierarchical-data-database/)
Using the MPTT encoding, a lot of questions about trees require "at most one query", like

1. What are the descendants of a node?
2. The ancestors?
3. All nodes of a given level?
4. All leaf nodes?

The question then is how to re-encode the first tree into a *different* tree, so that the equivalent of question (A) 
takes at most 1 query. As I was writing this I panicked and thought it was a trivial problem, but you don't know the 
class in advance! So you can't answer this in one query by for example asking if both the student and the teacher are 
children of the class -- you don't *which* class to ask this about, so in the worst case you'd have to make one query 
for *each* class.

More types of questions
----

More generally, the class might be one of many where the root node is a "school", and a school 
can have one or more "principals" as children in addition to classes. The other questions I think can be reduced to 
(A) above, but here they are for posterity:

* (B) Are two teachers both children of the same class? And are two students both children of the same learner group?
* (C) Are two learner groups both children of the same class?
* (D) Are two students both children of the same class?

(Almost) The Answer
-----

Make another tree like [this one](https://docs.google.com/drawings/d/1mnUVKryNqHRo8X6Rp86KVtRdQrtYyPA44P488wA5JXw/edit).
Then you can answer (A) in 1 query, by asking if a student is the child of a teacher. Extend the tree to classes as
children of schools (with principals) similarly.

(B) and (C) are both answered in *at most* 2 queries -- see first if the first teacher is the child of the second, or if 
it's not then see if the second is the child of the first. If yes to either, then the answer to the original is also 
yes, otherwise no. (Replace teacher with students or learner groups.)

Finally (D) is answered in 2 queries -- find the class which is the parent of one student, then check if the other
is also a child of that class.

A Complication
-----

In reality we don't deal with students and teachers directly -- we deal with users, which may be mapped in some
way to multiple students and teachers. In other words, a user might be a teacher for one class and a student for
another, or a teacher for three classes, or any combination of student and teacher roles.

The good news is that when you're curious about finding all the descendants for *several* teacher nodes, it *still* 
just takes 1 query using the tree above if it's MPTT-encoded!

(Actually) The Answer
------

Each node in the tree must carry a little extra information in order to keep the number of queries small.
First a teacher or student node should know which user it's associated with, so we don't have to follow some foreign
key relationship from nodes back to users. Secondly, each node should know it's "kind" as well -- whether it's a
"student", "teacher", "learner group" or something else. If not, consider the following pathological 
case:

1. User 1 is a teacher for class A.
2. User 2 is *also* a teacher for class A.
3. Through some accident of insertion order, User 2's teacher node is a child of User 1's teacher node.

Then if we *just* checked descendants, we'd erroneously assume that User 2 is a student of User 1. But if it's
labeled as a "teacher" node we know that's not the case! Knowing the kind *also* helps us to build the tree in the 
first place.

Finally, in the given solution answering (A) actually takes 2 queries -- one to determine all coach nodes associated
with a user, and then one to find all it's descendants matching certain constraints. If the coach nodes' ids are stored
directly on the User model, one query could be avoided -- but then the database isn't normalized!

The Apps here
-------------
The app `class_tree` implements the solution described above.

The app `natural_tree` implements the same solution, but instead of using the modified tree structure it uses the 
"natural" tree structure that the problem is initially framed in. This is to compare performance with `class_tree`.

Conclusion from benchmarking
------

To my surprise both apps perform comparably for the `User.is_learner_in_class_of` method!

Related object benchmarking
---------------------------

`Related objects` are foreign-keyed to users. Once class of methods is to return all related objects that a user has
 permissions to view. We benchmark time to get related objects in a for a large # of users with variable # of related
 objects:
 
```text
Average time (s) for `natural_tree` app's
        `RelatedObject.all_that_user_has_perms_for` method: 0.16647429609298706
Standard deviation is 0.2209921832619154
```

```text
Average time (s) for `class_tree` app's
        `RelatedObject.all_that_user_has_perms_for` method: 0.013064778327941895
Standard deviation is 0.011786503008821534
```

You can replicate by running the `StressTestRelatedObject` tests found in each module.
Note these tests take a long time to run (~260s) because there are a large # of related objects in the test fixture.

In this case we see that `class_tree` is a clear winner, even after refining the `natural_tree` query and indexing
natural_tree.Role fields together to (presumably) speed up lookup time.