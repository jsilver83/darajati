# TODO List

"""
--------------------------------------------------------------
#Done - 1. When changing status of attendance show the corresponding color:

    Absent -> Red
    Late -> Yellow
    Excused -> Green-ish
    
#Done - 2. Do not navigate from a page when someone have changed something without saving.

    This will take effect for Attendances and Grades.
#DONE - 3. Flag for Don't calculate this fragment into the overall total of the student.
#DONE - 4. Divide Boundary Range into 2 fields Upper Range aka + and Lower Range aka - .
#DONE - 5. Add flag to disallow changes after submitting an attendance in course offering.
6. Dynamically calculate section average while the instructor entering grades using JS.
#DONE  - 7. Fix the days of the attendances.
#DONE - 8. Grades Fragment Import.
#DONE - 9. WebService
#Done - 10. Absent & Late Deduction (Complex)
#DONE - 11. Averages
#DONE - 12. Add Serial Number for enrollments
#DONE - 13. Order periods based on the start_time in attendance page.
---------------------------------------------------------------
7/nov
#Done - Grade Fragment should allow entry should be by datetime
#Done - Needs to check the import grades a mark should not have characters
#Done - Grade imports report - errors should be first. also add one more column where accept a remark
#Done - Apply history for enrollments.
#Done - Grade fragment should only be allowed to create, delete them before the deadline and editing them should
be allowed for specific things not all of the fields.

#Done - Mathematical formulas for late and absent deduction using eval():
Introduce deduction value, deduction calculated date.
Late and Absent are dynamic variables for each periods generated at run time.
#Done - If course is coordinated do not show section as a field.
----------------------------------------------------------------
Nov - 13
#Done - Put note on import grades no subjective checks
- excused import page.
#Done - grade fragment information should be shown in the instructor page also depending on which type
also show a red note where to tell the instructor that he can not edit the grade if the allow_change is not marked.
#Done - show the grade fragment start entry and end entry.
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
"""

