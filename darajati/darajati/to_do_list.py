# TODO List

"""
1. When changing status of attendance show the corresponding color:

    Absent -> Red
    Late -> Yellow
    Excused -> Green-ish
    
2. Do not navigate from a page when someone have changed something without saving.

    This will take effect for Attendances and Grades.
    
#DONE - 3. Flag for Don't calculate this fragment into the overall total of the student.

#DONE - 4. Divide Boundary Range into 2 fields Upper Range aka + and Lower Range aka - .

#DONE - 5. Add flag to disallow changes after submitting an attendance in course offering.

6. Dynamically calculate section average while the instructor entering grades using JS.

#DONE  - 7. Fix the days of the attendances.

#DONE - 8. Grades Fragment Import.

#DONE - 9. WebService

10. Absent & Late Deduction (Complex)
 
#DONE - 11. Averages

#DONE - 12. Add Serial Number for enrollments

#DONE - 13. Order periods based on the start_time in attendance page.

14 - Coordinator create/edit/delete grade fragment deleting with CASCADE - (Create - Delete needs to be discussed with Joud)
15 - Allow changing countable grade fragment only before the grade_fragment_deadline
16 - Excused Status should be given by Student Affairs with implementing a single page for them to select student and
period and excused that student.

17 - Automate Jobs with celery
18 - Fix the look and field of the website
19 - exporting grade fragments from other semester.

7/nov

#Done - Grade Fragment should allow entry should be by datetime
#Done - Needs to check the import grades a mark should not have characters
#Done - Grade imports report - errors should be first. also add one more column where accept a remark
#Done - Apply history for enrollments.
- Grade fragment should only be allowed to create, delete them before the deadline and editing them should
be allowed for specific things not all of the fields.
- Mathematical formulas for late and absent deduction using eval()
- Auto sent emails or sms to students when they are near a set of numbers of absences.
- If course is coordinated do not show section as a field.
- sticky save button in grades and attendance.

"""

