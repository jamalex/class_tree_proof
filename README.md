What is this?
-------

I encountered a problem at work.
I wrote an email to a friend about it.
Below is the problem as I posed it to him.
Then I thought up a solution, so I decided to make a Django app that demonstrated it.

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

The question then is how to re-encode the first tree into a *different* tree, so that the equivalent of question (0A) 
takes at most 1 query. As I was writing this I panicked and thought it was a trivial problem, but you don't know the 
class in advance! So you can't answer this in one query by for example asking if both the student and the teacher are 
children of the class -- you don't *which* class to ask this about, so in the worst case you'd have to make one query 
for *each* class.

----

P.S. More generally, as I indicated, the class might be one of many where the root node is a "school", and a school 
can have one or more "principals" as children in addition to classes. The other questions I think can be reduced to 
(A) above, but here they are for posterity:

* (B) Are two teachers both children of the same class? And are two students both children of the same learner group?
* (C) Are two learner groups both children of the same class?
* (D) Are two students both children of the same class?

The Answer
-----

Make another tree like [this one](https://docs.google.com/drawings/d/1mnUVKryNqHRo8X6Rp86KVtRdQrtYyPA44P488wA5JXw/edit).
Then you can answer (A) in 1 query, by asking if a student is the child of a teacher. Extend the tree to classes as
children of schools (with principals) similarly.


(B) and (C) are both answered in *at most* 2 queries -- see first if the first teacher is the child of the second, or if 
it's not then see if the second is the child of the first. If yes to either, then the answer to the original is also 
yes, otherwise no. (Replace teacher with students or learner groups.)

Finally (D) is answered in 2 queries -- find the class which is the parent of one student, then check if the other
is also a child of that class.