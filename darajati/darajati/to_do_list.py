# TODO List
"""
----------------------------------------------------------------
- Auto sent emails or sms to students when they are near a set of numbers of absences.
- sticky save button in grades and attendance.
- Excused Status should be given by Student Affairs with implementing a single page for them to select student and
    period and excused that student.
- Automate Jobs with celery
- Fix the look and field of the website
- exporting grade fragments from other semester.
- Averages monitoring

Nov 22
when a student moved to other section, the Serial number sequence should not change.

Dec 25
- redis server is ready for testing, celery needs to be implemented.
- exam app needs to be functional


:::
Jan 2 2018
add last updated by in grades

22 Nov 2018
- fix error messages not being sent to ADMINS
- fix submit buttons in all forms to make it submit only once: https://stackoverflow.com/a/2545795/853175

26 Nov 2018
URGENT:
- fix the grades to be in 4 decimal points instead of 2
- make sure the imported grades (in percentages) are being in proper decimal formats

27 Nov 2018
URGENT:
- investigate whether to have averages in database views or stored values in a table that has is_dirty flag.
    The flag can be an indication whether we should recalculate/update the values on read

28 Nov 2018
- add a flag to ExamSettings to ignore students class timings checks

4 Dec 2018
- change the functions that calculate averages to make it use the section and course averages database view

10 Dec 2018
- fix validation for grade_fragment entry page for different boundaries
- fix bug that enables instructor to edit grades evn if they are not coordinators
- the button show grade is not shown if show grades for instructor is false
- implement formset for all fragments for show_flags for coordinator
- in subjective marking, fix averages to calculate based on weighted mark
- In the “unaccepted marks” report in writing fragments, add the room and section for the student

11 Dec 2018
- remove readonly from grades when viewer is the coordinator
- investigate if instructors changed grades after submitting

19 Dec 2018
- make sure all updated_on fields to be datetime and auto_now=True

22 Dec 2018
- fix all dispatch = super() ... return dispatch
- fake change

25 April 2019
- in grade bulk upload page, before applying the grades, mark all active students grade as 0
- attendance sheet printout
- restrict EP sections to be between 30 and 48(or 49?) only

15 June 2019
- apply grades should be per course offering and it should be applicable any time during the semester

"""

