from decimal import Decimal
from math import *

from django.conf import settings
from django.contrib.auth.models import User as User_model
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from simple_history.models import HistoricalRecords

from attendance.models import ScheduledPeriod, AttendanceInstance, Attendance
from grade.models import LetterGrade
from .data_types import RoundTypes
from .utils import to_string, now, today

User = settings.AUTH_USER_MODEL


class Person(models.Model):
    """
    an abstract class that will be inherited by Student and Instructor
    """

    university_id = models.CharField(_('university id'), max_length=20, null=True, blank=True, unique=True)
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

    @property
    def kfupm_email(self):
        return '{}@kfupm.edu.sa'.format(getattr(self.user, 'username', 'NO-EMAIL'))


class Student(Person):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student', null=True, blank=True,
                                unique=True)

    class Meta:
        ordering = ('university_id',)

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
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor', null=True, blank=True,
                                unique=True)

    class Meta:
        ordering = ('-user__is_superuser', '-user__is_staff', 'english_name', 'university_id')

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

    @staticmethod
    def can_give_excuses(user):
        return 'attendance.can_give_excuses' in user.get_all_permissions() or user.is_superuser


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

    class Meta:
        ordering = ('-start_date', 'code',)

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

    class Meta:
        ordering = ('code', 'name',)

    def __str__(self):
        return to_string(self.name, self.code)


class Course(models.Model):
    name = models.CharField(_('english name'), max_length=255, null=True, blank=False)
    arabic_name = models.CharField(_('arabic name'), max_length=255, null=True, blank=False)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, related_name='courses', null=True,
                                   blank=False)
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    class Meta:
        ordering = ('department', 'code', 'name',)

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
    total_decimal_places = models.SmallIntegerField(
        _('Total Rounding Decimal Places'),
        null=True,
        blank=True,
        help_text=_('Decimal places in the Total for rounding or truncating methods')
    )
    grade_promotion_borderline = models.DecimalField(
        _('Letter Grade Promotion Borderline Difference For Criteria'),
        null=True,
        blank=True,
        default=0.0,
        max_digits=settings.MAX_DIGITS,
        decimal_places=settings.MAX_DECIMAL_POINT,
        help_text=_('This will be used to check student''s eligibility for letter grade promotion if the student is '
                    'meeting promotion criterion in the grade fragment(s)'),
    )
    auto_grade_promotion_delta = models.DecimalField(
        _('Auto Letter Grade Promotion Difference'),
        null=True,
        blank=True,
        default=0.0,
        max_digits=settings.MAX_DIGITS,
        decimal_places=settings.MAX_DECIMAL_POINT,
        help_text=_('This will be used to check student''s eligibility for letter grade promotion. A student will be '
                    'considered for promotion if his total is within this difference'),
    )

    class Meta:
        ordering = ('semester', 'course',)

    def __str__(self):
        return to_string(self.semester, self.course)

    # TODO: remove; useless
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
    def get_active_course_offerings():
        """
        :return: active semesters' course offerings
        """
        return CourseOffering.objects.filter(semester__start_date__lte=now(), semester__end_date__gte=now())

    def get_letter_grade_promotion_criterion(self):
        """
        This will return the instance of the letter grade promotion fragment
        Only one fragment can be flagged as THE criterion for letter grade promotion
        """
        criterion = self.grade_fragments.filter(grade_promotion_criterion=True)
        if criterion.count() == 1:
            return criterion.first()

    def get_all_letter_grade_promotion_cases(self):
        enrollments = Enrollment.objects.filter(section__course_offering=self)

        eligible_cases = []
        for enrollment in enrollments:
            eligible = enrollment.is_eligible_for_letter_grade_promotion()
            if eligible:
                eligible_cases.append({'enrollment': enrollment, 'promoted_letter_grade': eligible, })

        return eligible_cases


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
    total_decimal_places = models.SmallIntegerField(
        _('Total Rounding Decimal Places'),
        null=True,
        blank=True,
        help_text=_('Decimal places in the Total for rounding or truncating methods')
    )
    crn = models.CharField(_('CRN'), max_length=100, null=True, blank=False)
    active = models.BooleanField(_('Active'), default=False)

    class Meta:
        ordering = ('course_offering', 'code',)

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
        return get_object_or_404(Section, pk=section_id)

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

    @property
    def teachers(self):
        teachers = list(self.scheduled_periods.values_list('instructor_assigned__english_name').distinct())
        return mark_safe(' <b>&</b> '.join([str(x[0]) for x in teachers]))


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

    class Meta:
        ordering = ('course_offering', 'instructor',)

    def __str__(self):
        return to_string(self.course_offering, self.instructor)

    # FIXME: instructor param cannot be None or else the ORM will throw an exception
    @staticmethod
    def get_coordinator(instructor):
        """        
        :param instructor: an instructor instance 
        :return:  list of coordinated course offering of this instructor
        """
        return Coordinator.objects.filter(instructor=instructor)

    @staticmethod
    def is_coordinator(instructor):
        """
        :param instructor: an instructor instance 
        :return: True if current instructor is coordinating at least one course offering
        else False
        """
        return Coordinator.get_coordinator(instructor).exists()

    @staticmethod
    def is_active_coordinator(instructor):
        """
        :param instructor: an instructor instance
        :return: True if current instructor is coordinating at least one course offering in an ACTIVE semester
        else False
        """
        return Coordinator.get_coordinator(instructor).filter(
            course_offering__in=CourseOffering.get_active_course_offerings()
        ).exists()

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

    @staticmethod
    def get_coordinated_courses(instructor=None):
        return Coordinator.objects.filter(instructor=instructor)

    @staticmethod
    def get_active_coordinated_course_offerings_choices(instructor=None):
        """
        :return: current semester course_offering_id and 'semester code - course code'
        """
        offerings = Coordinator.get_coordinated_courses(instructor).filter(
            course_offering__in=CourseOffering.get_active_course_offerings()
        ).values('course_offering', 'course_offering__semester__code', 'course_offering__course__code').distinct()

        return [(co['course_offering'], str(co['course_offering__semester__code']
                                            + ' ' + co['course_offering__course__code'])) for co in offerings]


class Enrollment(models.Model):
    student = models.ForeignKey(Student, related_name='enrollments', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='enrollments', on_delete=models.CASCADE)
    active = models.BooleanField(_('Active'), blank=False, default=True)
    comment = models.CharField(_('Comment'), max_length=200, blank=True)
    letter_grade = models.CharField(_('letter grade'), max_length=20, null=True, blank=True, default='UD')
    register_date = models.DateTimeField(_('Enrollment Date'), null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='updated_enrollments',
                                   null=True, blank=False)
    updated_on = models.DateTimeField(_('Updated on'), auto_now=True)
    history = HistoricalRecords()

    # FIXME: when a students moves from section to other and that student has an id which comes between 2 students id
    # FIXME: the order of the Serial Number would break.
    class Meta:
        unique_together = ('student', 'section')
        ordering = ['student__university_id']

    def __str__(self):
        try:
            return to_string(self.student, self.section)
        except:
            return 'Invalid enrollment: missing student or section info'

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

    def calculated_letter_grade(self):
        try:
            return self.final_data.calculated_letter_grade
        except:
            return "UD"

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

    # TODO: remove
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
        # result = 0
        # formula = self.section.course_offering.formula
        # if formula:
        #     periods = ScheduledPeriod.objects.filter(section=self.section).distinct(
        #         'title'
        #     )
        #     if periods:
        #         for period in periods:
        #             title = period.title
        #             if title in formula:
        #                 formula = formula.replace(title + "_abs", to_string(self.get_enrollment_period_total_absence(title)))
        #                 formula = formula.replace(title + "_lat", to_string(self.get_enrollment_period_total_late(title)))
        #         result = eval(formula)
        # return result
        #### I AM TOO PROUD OF THE ABOVE CODE TO REMOVE IT ENTIRELY ####
        return self.attendance_deduction

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

    def get_total_weights(self):
        try:
            return self.final_data.total_weights if self.final_data.total_weights else Decimal('0.00')
        except:
            return Decimal('0.00')

    def calculated_total(self):
        try:
            return self.final_data.total_rounded
        except:
            return Decimal('0.00')

    def get_enrollment_period_total_excused(self, period_title):
        """
        :param period_title: 
        :return: total excused of a a given period_title and enrollment
        """
        return self.attendance.filter(attendance_instance__period__title=period_title,
                                      status=Attendance.Types.EXCUSED).count()

    def get_grade_in_letter_grade_promotion_criterion(self):
        criterion = self.section.course_offering.get_letter_grade_promotion_criterion()
        if criterion:
            try:
                return self.grades.get(grade_fragment=criterion).grade_quantity
            except:
                return Decimal('0.00')
            
    def get_difference_to_next_letter_grade(self):
        calculated_letter_grade = self.calculated_letter_grade()
        calculated_letter_grade_instance = LetterGrade.get_letter_grade(self.section.course_offering, 
                                                                        calculated_letter_grade)
        if calculated_letter_grade_instance is None:
            return

        the_upper_letter_grade = calculated_letter_grade_instance.get_the_upper_letter_grade()
        if the_upper_letter_grade is None:
            return

        return the_upper_letter_grade.cut_off_point - self.calculated_total()

    def get_next_promotable_letter_grade(self):
        calculated_letter_grade = self.calculated_letter_grade()

        upper_letter_grade = LetterGrade.get_letter_grade(
            self.section.course_offering,
            calculated_letter_grade
        ).get_the_upper_letter_grade()
        if upper_letter_grade:
            return upper_letter_grade.letter_grade

    def is_an_auto_promotion_case(self):
        auto_grade_promotion_difference = self.section.course_offering.auto_grade_promotion_delta

        if auto_grade_promotion_difference:
            diff = self.get_difference_to_next_letter_grade()
            if diff is not None and diff <= auto_grade_promotion_difference:
                return True

    def is_a_borderline_case(self):
        letter_grade_promotion_borderline = self.section.course_offering.grade_promotion_borderline
        if letter_grade_promotion_borderline is None:
            return False
        else:
            diff = self.get_difference_to_next_letter_grade()
            if diff is not None and diff <= letter_grade_promotion_borderline:
                return True

    def is_eligible_for_letter_grade_promotion(self):
        if self.is_an_auto_promotion_case():
            return self.get_next_promotable_letter_grade()

        letter_grade_promotion_borderline = self.section.course_offering.grade_promotion_borderline

        if letter_grade_promotion_borderline:
            if not self.is_a_borderline_case():
                return False

        calculated_letter_grade = self.calculated_letter_grade()
        if calculated_letter_grade:
            grade_in_promotion_criterion = self.get_grade_in_letter_grade_promotion_criterion()
            criterion = self.section.course_offering.get_letter_grade_promotion_criterion()
            if grade_in_promotion_criterion and criterion:
                criterion_percentage_grade = grade_in_promotion_criterion * self.get_total_weights() / criterion.weight
                criterion_letter_grade = LetterGrade.calculate_letter_grade_for_a_total(self.section.course_offering,
                                                                                        criterion_percentage_grade)
                if criterion_letter_grade:
                    criterion_comparison = LetterGrade.compare_letter_grades(self.section.course_offering,
                                                                             criterion_letter_grade.letter_grade,
                                                                             calculated_letter_grade)
                    if criterion_comparison > 0:
                        return self.get_next_promotable_letter_grade()

    def promotion_type(self):
        if self.is_an_auto_promotion_case():
            return _('Total {total} is within auto promotion difference').format(total=self.calculated_total())
        else:
            return _('{grade_criterion} out of {promotion_criterion}').format(
                grade_criterion=self.get_grade_in_letter_grade_promotion_criterion(),
                promotion_criterion=self.section.course_offering.get_letter_grade_promotion_criterion().weight,
            )

    def was_promoted(self):
        return self.comment.startswith('Letter grade got promoted from')

    @staticmethod
    def test_method(course_offering_pk):
        enrollments = Enrollment.objects.filter(section__course_offering__pk=course_offering_pk)

        for enrollment in enrollments:
            eligible = enrollment.is_eligible_for_letter_grade_promotion()
            if eligible:
                print('{} {} {} --> {} ---- because of: {}'.format(
                    enrollment.student.university_id,
                    enrollment.calculated_total(),
                    enrollment.calculated_letter_grade(),
                    eligible,
                    enrollment.get_grade_in_letter_grade_promotion_criterion()
                ))

    @staticmethod
    def test_method2(course_offering_pk):
        enrollments = Enrollment.objects.filter(section__course_offering__pk=course_offering_pk)

        course_offering = CourseOffering.objects.get(pk=course_offering_pk)
        # print(course_offering.letter_grade_promotion_borderline)

        for enrollment in enrollments:
            borderline = enrollment.is_a_borderline_case()
            grade_instance = LetterGrade.get_letter_grade(enrollment.section.course_offering, enrollment.calculated_letter_grade())
            if borderline:
                print('{} {} --> {} OOORRR {} ??? {}'.format(
                    enrollment.student.university_id,
                    enrollment.calculated_total(),
                    grade_instance,
                    grade_instance.get_the_upper_letter_grade(),
                    borderline,
                ))
