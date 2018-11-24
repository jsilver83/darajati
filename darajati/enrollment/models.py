from math import *
from django.db import models
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import User as User_model
from .data_types import RoundTypes
from .utils import to_string, now, today, attendance_boundary
from attendance.models import ScheduledPeriod, AttendanceInstance, Attendance
from simple_history.models import HistoricalRecords

User = settings.AUTH_USER_MODEL


class Person(models.Model):
    """
    an abstract class that will be inherited by Student and Instructor
    """

    university_id = models.CharField(_('university id'), max_length=20, null=True, blank=True)
    government_id = models.CharField(_('government id'), max_length=20, null=True, blank=True)
    english_name = models.CharField(_('english name'), max_length=255, null=True, blank=False)
    arabic_name = models.CharField(_('arabic name'), max_length=255, null=True, blank=False)
    mobile = models.CharField(_('mobile'), max_length=20, null=True, blank=True)
    personal_email = models.EmailField(_('personal email'), null=True, blank=False)
    active = models.BooleanField(_('is_active'), blank=False, default=False)

    @property
    def name(self):
        """
        :return: translated name of the person depending on the current active language
        """
        lang = translation.get_language()
        if lang == "ar":
            return self.arabic_name
        else:
            return self.english_name

    class Meta:
        abstract = True


class Student(Person):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student', null=True, blank=True)

    def __str__(self):
        return to_string(self.english_name, self.university_id)

    @staticmethod
    def is_active(user=None):
        """
        :return: True if student is active else False
        """
        return Student.get_student(user).active

    @staticmethod
    def get_student(user=None):
        """
        :param user: current login user
        :return: True if student exist else False
        """
        try:
            return Student.objects.get(user=user)
        except Student.DoesNotExist:
            return None

    @staticmethod
    def is_student_exists(email):
        return Student.objects.filter(personal_email__exact=email).exists()


class Instructor(Person):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor', null=True, blank=True)

    def __str__(self):
        return to_string(self.english_name)

    @staticmethod
    def get_instructor(user=None):
        """
        :parameter user: current login user
        :return: return an instance of instructor if exist
        """
        try:
            return Instructor.objects.get(user=user)
        except Instructor.DoesNotExist:
            return None

    @staticmethod
    def is_active_instructor(user=None):
        """
        :parameter user: current login user
        :return: True if instructor is active else False
        """
        instructor = Instructor.get_instructor(user=user)
        if instructor:
            return instructor.active
        return False

    # FIXME: this shouldnt be a static method since it is passing instructor as first argument...
    # FIXME: ... Moreover, passing no instructor will just throw an exception in the ORM
    @staticmethod
    def is_active_coordinator(instructor=None):
        """
        :parameter instructor: current login user
        :return: True if instructor is active else False
        """
        return Coordinator.get_coordinator(instructor=instructor)

    @staticmethod
    def is_instructor_exists(email):
        """
        :parameter email: a university email
        :return: True if instructor with this email dose exist else False
        """
        return Instructor.objects.filter(personal_email__exact=email).exists()

    def is_coordinator_or_instructor(self):
        """
        :return: None if coordinator else return instructor instance 
        """
        if Coordinator.is_coordinator(self):
            return None
        return self


class Semester(models.Model):
    start_date = models.DateField(_('Start date'))
    end_date = models.DateField(_('End date'))
    grade_fragment_deadline = models.DateField(
        _('Grade break down deadline date'),
        null=True,
        blank=False
    )
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    def __str__(self):
        return to_string(self.code)

    def check_is_accessible_date(self, date, offset_date):
        """
        :param date: the date which coordinator or instructor trying to access for attendance 
        :param offset_date: the allowed offset days to view
        :return: True if the given offset date is less than or equal to the date
        """
        if offset_date <= date and self.start_date <= date <= self.end_date:
            return True
        return False

    def can_create_grade_fragment(self):
        """
        :return: True if the deadline date is greater or equal to the current date else False 
        """
        return True if self.grade_fragment_deadline >= today() else False


class Department(models.Model):
    name = models.CharField(_('english name'), max_length=50, null=True, blank=False)
    arabic_name = models.CharField(_('arabic name'), max_length=50, null=True, blank=False)
    code = models.CharField(max_length=10, null=True, blank=False)

    def __str__(self):
        return to_string(self.name, self.code)


class Course(models.Model):
    name = models.CharField(_('english name'), max_length=255, null=True, blank=False)
    arabic_name = models.CharField(_('arabic name'), max_length=255, null=True, blank=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses', null=True, blank=False)
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    def __str__(self):
        return to_string(self.code)


class CourseOffering(models.Model):
    semester = models.ForeignKey(Semester, related_name='offering', on_delete=models.CASCADE)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='offering',
        null=True,
        blank=False
    )
    attendance_entry_window = models.PositiveIntegerField(
        _('attendance window'),
        null=True,
        blank=False,
        default=7
    )
    coordinated = models.BooleanField(blank=False, default=1)
    formula = models.CharField(
        _('Deduction formula'),
        max_length=200,
        null=True,
        blank=True,
        help_text=_('Formula to calculate the deduction value from students attendance')
    )
    allow_change = models.BooleanField(
        _('Allow changing after submitting attendance?'),
        blank=False,
        default=1,
        help_text=
        _('This if checked will allow the instructors to change the attendances after submitting')
    )
    total_rounding_type = models.CharField(
        _('Total Rounding Type'), max_length=50,
        choices=RoundTypes.choices(),
        null=True,
        blank=False,
        default=RoundTypes.NONE,
        help_text=_('Total grade rounding method for letter grade calculation')
    )

    def __str__(self):
        return to_string(self.semester, self.course)

    @staticmethod
    def get_course_offering(course_offering_id):
        """
        :param course_offering_id: an integer number which represent a id of course_offering 
        :return: an instance of that id
        """
        try:
            return CourseOffering.objects.get(id=course_offering_id)
        except CourseOffering.DoesNotExist:
            return None

    @staticmethod
    def get_current_course_offerings():
        """
        :return: current semester course_offering_id and 'semester code - course code'
        """
        return [(course_offering.pk, str(course_offering))
                for course_offering in CourseOffering.objects.filter(
                semester__start_date__lte=now(),
                semester__end_date__gte=now())]


class Section(models.Model):
    course_offering = models.ForeignKey(
        CourseOffering,
        related_name='sections',
        on_delete=models.CASCADE
    )
    code = models.CharField(max_length=20, null=True, blank=False)
    rounding_type = models.CharField(
        _('Rounding Type'),
        max_length=50,
        choices=RoundTypes.choices(),
        null=True,
        blank=False,
        default=RoundTypes.NONE,
        help_text=_('Total grade rounding method for letter grade calculation')
    )
    crn = models.CharField(_('CRN'), max_length=100, null=True, blank=False)
    active = models.BooleanField(_('Active'), default=False)

    def __str__(self):
        return to_string(self.course_offering, self.code)

    @property
    def attendance_entry_window(self):
        """
        :return: a integer defined attendance window if the course coordinator else 0  
        """
        if self.course_offering.coordinated:
            return self.course_offering.attendance_entry_window
        else:
            return 0

    @staticmethod
    def get_section(section_id):
        """
        :param section_id:
        :return: an object of the giving section_id
        """
        try:
            return Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return None

    @staticmethod
    def get_current_semesters_sections():
        """
        :return: objects of all current semesters sections
        """
        return Section.objects.filter(
            course_offering__semester__start_date__lte=now(),
            course_offering__semester__end_date__gte=now()).distinct()

    @staticmethod
    def get_instructor_sections(instructor):
        """
        :param instructor: current login user
        :return: a unique list of section objects for the login user and for the current semester
        """
        return Section.objects.filter(
            scheduled_periods__instructor_assigned=instructor,
            scheduled_periods__section__course_offering__semester__start_date__lte=now(),
            scheduled_periods__section__course_offering__semester__end_date__gte=now()
        ).distinct()

    @staticmethod
    def is_section_exists_in_course_offering(course_offering, section_code):
        """
        :param course_offering: an instance of course_offering 
        :param section_code: a section code
        :return: True of exists else False
        """
        return Section.objects.filter(
            course_offering__exact=course_offering,
            code__exact=section_code
        ).exists()

    def is_instructor_section(self, instructor):
        """
        :param instructor: current login user
        :return: return true if this is the instructor of this section
        """
        return Section.objects.filter(
            id=self.id, scheduled_periods__instructor_assigned=instructor,
            scheduled_periods__section__course_offering__semester__start_date__lte=now(),
            scheduled_periods__section__course_offering__semester__end_date__gte=now()
        ).distinct().exists()

    def is_coordinator_section(self, instructor):
        """
        :param instructor: current login user
        :return:
        """
        return Coordinator.objects.filter(
            instructor=instructor,
            course_offering=self.course_offering,
            course_offering__semester__start_date__lte=now(),
            course_offering__semester__end_date__gte=now()
        ).exists()


class Coordinator(models.Model):
    course_offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name='coordinators',
        null=True,
        blank=False
    )
    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.CASCADE,
        related_name='coordinators',
        null=True,
        blank=False
    )

    def __str__(self):
        return to_string(self.course_offering, self.instructor)

    # FIXME: instructor param cannot be None or else the ORM will throw an exception
    @staticmethod
    def get_coordinator(instructor=None):
        """        
        :param instructor: an instructor instance 
        :return:  list of coordinated course offering of this instructor
        """
        return Coordinator.objects.filter(instructor=instructor)

    @staticmethod
    def is_coordinator(instructor=None):
        """
        :param instructor: an instructor instance 
        :return: True if current instructor is coordinating at least one course offering
        else False
        """
        coordinator = Coordinator.get_coordinator(instructor)
        if coordinator:
            return True
        return False

    @staticmethod
    def is_coordinator_of_course_offering_in_this_semester(instructor, course_offering):
        """
        :param instructor: an instructor instance
        :param course_offering: an instance of course offering
        :return: True if this instructor is coordinator of at least one *Within this semester*
        else False
        """
        return Coordinator.get_coordinator(
            instructor=instructor
        ).filter(
            course_offering=course_offering,
            course_offering__semester__start_date__lte=now(),
            course_offering__semester__end_date__gte=now(),
        ).distinct().exists()


class Enrollment(models.Model):
    student = models.ForeignKey(Student, related_name='enrollments', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='enrollments', on_delete=models.CASCADE)
    active = models.BooleanField(_('Active'), blank=False, default=True)
    comment = models.CharField(_('Comment'), max_length=200, blank=True)
    letter_grade = models.CharField(_('letter grade'), max_length=20, null=True, blank=False, default='UD')
    register_date = models.DateTimeField(_('Enrollment Date'), null=True, blank=False)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollment_creator', null=True, blank=False)
    updated_on = models.DateTimeField(_('Updated on'), auto_now=True)
    history = HistoricalRecords()

    # FIXME: when a students moves from section to other and that student has an id which comes between 2 students id
    # FIXME: the order of the Serial Number would break.
    class Meta:
        unique_together = ('student', 'section')
        ordering = ['student__university_id']

    def __str__(self):
        return to_string(self.student, self.section)

    @property
    def _history_user(self):
        return self.updated_by

    @_history_user.setter
    def _history_user(self, value):
        self.updated_by = value

    @property
    def _history_date(self):
        return self.updated_on

    @_history_date.setter
    def _history_date(self, value):
        self.updated_on = value

    @property
    def get_letter_grade(self):
        """        
        :return: letter grade if it's set other wise return 'UD' which means Undecided   
        """
        return self.letter_grade if self.letter_grade else "UD"

    @staticmethod
    def get_students_of_section(section_id):
        """
        :return: list of all students for a giving section ID
        """
        return Enrollment.objects.filter(section=section_id)

    @staticmethod
    def get_enrollments_of_section_with_students_data(section_id):
        """
        :return: list of all students for a giving section ID
        """
        return Enrollment.objects.select_related('student').filter(section=section_id)

    @staticmethod
    def is_enrollment_exists(student, section):
        return Enrollment.objects.filter(student=student, section=section).exists()

    @staticmethod
    def get_students_attendances_initial_data(section_id, date, instructor=None):
        # FIXME: If possible make me nicer, i look like an ugly method *cry*
        # FIXEDU: stop bitchin'! do u think u look nicer now?! DRAMA QUEEN FUNCTION *sigh*
        """
        :param section_id:
        :param date:
        :param instructor:
        :return: list of enrollments for a giving section_id and a day and instructor
           If the giving day is not exist get the nearest one
        """
        enrollments = []
        day, period_date = ScheduledPeriod.get_nearest_day_and_date(section_id, date, instructor)
        periods = ScheduledPeriod.get_section_periods_of_day(section_id, day, instructor).order_by('start_time')
        enrollment_list = Enrollment.get_enrollments_of_section_with_students_data(section_id)
        count_index = 0

        attendance_instances = []
        for period in periods:
            attendance_instance_temp, created = AttendanceInstance.objects.select_related('period').get_or_create(
                period=period, date=period_date)
            attendance_instances.append(attendance_instance_temp)

        attendances = list(Attendance.objects.select_related('enrollment').filter(
            enrollment__in=enrollment_list,
            attendance_instance__in=attendance_instances)
        )

        for enrollment in enrollment_list:
            if enrollment.active is False:
                count_index += 1
                continue
            else:
                count_index += 1

            for attendance_instance in attendance_instances:
                attendance_id = 0
                updated_by = None
                updated_on = None
                status = None
                for attendance in attendances:
                    if attendance.enrollment == enrollment and attendance.attendance_instance == attendance_instance:
                        status = attendance.status
                        updated_by = attendance.updated_by
                        updated_on = attendance.updated_on
                        attendance_id = attendance.id

                enrollments.append(dict(enrollment=enrollment,
                                        enrollment_pk=enrollment.pk,
                                        student_name=enrollment.student.english_name,
                                        count_index=count_index,
                                        student_university_id=enrollment.student.university_id,
                                        period=attendance_instance.period,
                                        attendance_instance=attendance_instance,
                                        status=status or Attendance.Types.PRESENT,
                                        id=attendance_id,
                                        updated_by=updated_by,
                                        updated_on=updated_on))

        return enrollments

    @property
    def get_enrollment_total_absence(self):
        """
        :return: absence total of an enrollment 
        """
        return self.attendance.filter(status=Attendance.Types.ABSENT).count()

    @property
    def get_enrollment_total_excuses(self):
        """
        :return: excuses total of an enrollment
        """
        return self.attendance.filter(status=Attendance.Types.EXCUSED).count()

    @property
    def get_enrollment_total_late(self):
        """
        :return: late total of an enrollment 
        """
        return self.attendance.filter(status=Attendance.Types.LATE).count()

    @property
    def get_enrollment_total_deduction(self):
        """
        :return: total on this enrollment based on the formula 
        """
        result = 0
        formula = self.section.course_offering.formula
        if formula:
            periods = ScheduledPeriod.objects.filter(section=self.section).distinct(
                'title'
            )
            if periods:
                for period in periods:
                    title = period.title
                    if title in formula:
                        formula = formula.replace(title + "_A", to_string(self.get_enrollment_period_total_absence(title)))
                        formula = formula.replace(title + "_L", to_string(self.get_enrollment_period_total_late(title)))
                result = eval(formula)
        return result

    def get_enrollment_period_total_absence(self, period_title):
        """
        :param period_title: 
        :return: total absence of a a given period_title and enrollment
        """
        return self.attendance.filter(attendance_instance__period__title=period_title,
                                      status=Attendance.Types.ABSENT).count()

    def get_enrollment_period_total_late(self, period_title):
        """
        :param period_title: 
        :return: total late of a a given period_title and enrollment
        """
        return self.attendance.filter(attendance_instance__period__title=period_title,
                                      status=Attendance.Types.LATE).count()

    def get_enrollment_period_total_excused(self, period_title):
        """
        :param period_title: 
        :return: total excused of a a given period_title and enrollment
        """
        return self.attendance.filter(attendance_instance__period__title=period_title,
                                      status=Attendance.Types.EXCUSED).count()
