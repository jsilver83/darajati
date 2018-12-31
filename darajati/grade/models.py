from decimal import *

from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import Sum, Count
from django.db.models import Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from simple_history.models import HistoricalRecords

from enrollment.utils import to_string, now, today
from .utils import display_average_of_value
from darajati.utils import decimal

User = settings.AUTH_USER_MODEL


class GradeFragment(models.Model):
    class GradesBoundaries:
        OBJECTIVE = 'OBJECTIVE'
        SUBJECTIVE_BOUNDED = 'SUBJECTIVE_BOUNDED'
        SUBJECTIVE_BOUNDED_FIXED = 'SUBJECTIVE_BOUNDED_FIXED'
        SUBJECTIVE_FREE = 'SUBJECTIVE_FREE'
        SUBJECTIVE_MARKING = 'SUBJECTIVE_MARKING'

        @classmethod
        def choices(cls):
            return (
                (cls.OBJECTIVE, _('Objective')),
                (cls.SUBJECTIVE_BOUNDED, _('Subjective bound')),
                (cls.SUBJECTIVE_BOUNDED_FIXED, _('Subjective bound Fixed')),
                (cls.SUBJECTIVE_FREE, _('Subjective Free')),
                (cls.SUBJECTIVE_MARKING, _('Subjective Marking')),
            )

    course_offering = models.ForeignKey(
        'enrollment.CourseOffering',
        on_delete=models.CASCADE,
        related_name="GradeFragment",
        null=True,
        blank=False
    )
    section = models.ForeignKey(
        'enrollment.Section',
        on_delete=models.CASCADE,
        related_name="GradeFragment",
        null=True,
        blank=True)
    category = models.CharField(
        _('Category'),
        max_length=100,
        null=True,
        blank=False,
        help_text='Categories are like: Quiz, Midterm, Final Exam etc..'
    )
    description = models.CharField(
        _('Description'), max_length=100,
        null=True,
        blank=False
    )
    weight = models.DecimalField(
        _('Weight'),
        null=True,
        blank=False,
        default=0.0,
        max_digits=settings.MAX_DIGITS,
        decimal_places=settings.MAX_DECIMAL_POINT
    )
    entry_start_date = models.DateTimeField(
        _('Allowed entry start date'),
        null=True,
        blank=False,
        help_text=_('Set the entry date and time to allow instructor to enter grades')
    )
    entry_end_date = models.DateTimeField(
        _('Allowed entry end date'),
        null=True,
        blank=False,
        help_text=_('Set the entry date and time to allow instructor to enter grades')
    )
    order = models.PositiveSmallIntegerField(
        _('Display Order'),
        null=True,
        blank=False,
        help_text=_('The order of which grade break down should show up first')
    )
    show_teacher_report = models.BooleanField(
        _('Show in Teacher Report'),
        null=False,
        blank=False,
        default=True,
        help_text=_('This flag will control whether teachers are be able to see grades of this fragment '
                    'in darajati or in BI')
    )
    show_student_report = models.BooleanField(
        _('Show in Student Report'),
        null=False,
        blank=False,
        default=True
    )
    boundary_type = models.CharField(
        _('Boundary Type'), max_length=24,
        choices=GradesBoundaries.choices(),
        null=True,
        blank=False,
        default=GradesBoundaries.SUBJECTIVE_FREE)
    boundary_range_upper = models.DecimalField(
        _('Boundary Range Upper'), null=True, blank=True,
        help_text=_(
            'When the type is subjective and it is not free, give a positive range'),
        max_digits=settings.MAX_DIGITS,
        decimal_places=settings.MAX_DECIMAL_POINT
    )
    boundary_range_lower = models.DecimalField(
        _('Boundary Range Lower'),
        null=True,
        blank=True,
        help_text=_('When the type is subjective and it is not free, give a negative range'),
        max_digits=settings.MAX_DIGITS,
        decimal_places=settings.MAX_DECIMAL_POINT
    )
    boundary_fixed_average = models.DecimalField(
        _('Boundary Fixed Average'),
        null=True,
        blank=True,
        max_digits=settings.MAX_DIGITS,
        decimal_places=settings.MAX_DECIMAL_POINT
    )
    allow_change = models.BooleanField(
        _('Allow Change After Submission'),
        null=False,
        blank=False,
        default=True
    )
    student_total_grading = models.BooleanField(
        _('Calculate In Student Grading?'),
        default=False,
        help_text=_('If this is checked, It will be calculated in the total mark')
    )
    entry_in_percentages = models.BooleanField(
        _('Entry in Percentages'),
        null=False,
        blank=True,
        default=False,
        help_text=_('Checked when the course entered grades are in %')
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='GradeFragment',
        null=True,
        blank=True
    )
    updated_on = models.DateTimeField(
        _('Updated On'),
        auto_now=True,
        null=True,
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return to_string(self.course_offering, self.category, self.description)

    @staticmethod
    def get_grade_fragment(grade_fragment_id):
        """
        :param grade_fragment_id: an integer number 
        :return: a GradeFragment instance if exists else None
        """
        return get_object_or_404(GradeFragment, pk=grade_fragment_id)

    @staticmethod
    def get_section_grade_fragments(section):
        """
        :param section: a section instance 
        :return: list of grade fragments instances of a section or if the section is coordinated return 
        a list of that coordinated course
        """
        if section.course_offering.coordinated:
            return GradeFragment.objects.filter(course_offering=section.course_offering)
        return GradeFragment.objects.filter(section=section.id)

    @staticmethod
    def get_all_fragments_choices():
        # FIXME: to only return grade fragments of the current active semesters.
        """
        :return: dic of id and value of all grade fragments. 
        """
        return GradeFragment.objects.all().annotate(
            value=Concat(
                'course_offering__course__code',
                Value(' '), 'description',
                output_field=models.CharField()
            )
        ).values_list('id', 'value')

    def get_fragment_boundary(self, section):
        """
        :param section: 
        :return: a string to present the boundary of subjective fragment 
        """
        boundary_range_lower = self.boundary_range_lower or 0
        boundary_range_upper = self.boundary_range_upper or 0
        boundary_fixed_average = self.boundary_fixed_average or 0

        if self.boundary_type == self.GradesBoundaries.SUBJECTIVE_BOUNDED:
            average = StudentGrade.get_section_objective_average(
                section,
                self
            )
            if average:
                lower = average - boundary_range_lower
                upper = average + boundary_range_upper
                if self.entry_in_percentages:
                    return 'This section average should be between ' + str(lower) + '% and ' + str(upper) + '%'
                return 'This section average should be between ' + str(lower) + ' and ' + str(upper)
        if self.boundary_type == self.GradesBoundaries.SUBJECTIVE_BOUNDED_FIXED:
            lower = boundary_fixed_average - boundary_range_lower
            upper = boundary_fixed_average + boundary_range_upper
            if self.entry_in_percentages:
                return 'This section average should be between ' + str(lower) + '% and ' + str(upper) + '%'
            return 'This section average should be between ' + str(lower) + ' and ' + str(upper)

    def is_entry_allowed_for_instructor(self, section, instructor):
        """
        :return: True if the teacher is  trying to access a grade fragment grades within the allowed time
        """
        try:
            entry_allowed = self.entry_start_date <= now() <= self.entry_end_date
            if not entry_allowed:
                return section.is_coordinator_section(instructor)
            return entry_allowed
        except GradeFragment.DoesNotExist:
            pass

    def is_change_allowed_for_instructor(self, section, instructor):
        """
        :return: True if the teacher is a coordinator or allow_change is enabled in the fragment
        """
        try:
            if not self.allow_change:
                return section.is_coordinator_section(instructor)
            return self.allow_change
        except GradeFragment.DoesNotExist:
            pass

    def is_viewable_for_instructor(self, section, instructor):
        """
        :return: True if the teacher is able to see the fragment grades in reports
        """
        if not self.show_teacher_report:
            return section.is_coordinator_section(instructor)
        return self.show_teacher_report

    @property
    def allow_subjective_marking(self):
        """
        :return: True if boundary_type is SUBJECTIVE_MARKING
        """
        return self.boundary_type == self.GradesBoundaries.SUBJECTIVE_MARKING

    def get_section_average(self, section):
        return StudentGrade.get_section_average(
            section, self
        )

    @property
    def get_weight(self):
        """
        :return: if entry is in % return out of 100% else return the actual weight 
        """
        if self.entry_in_percentages:
            return '100%'
        return self.weight

    @property
    def short_name(self):
        return '%s - %s' %(self.category, self.description)


class LetterGrade(models.Model):
    course_offering = models.ForeignKey('enrollment.CourseOffering', on_delete=models.CASCADE,
                                        related_name="letter_grades", null=True,
                                        blank=False)
    section = models.ForeignKey('enrollment.Section', on_delete=models.CASCADE, related_name="letter_grades", null=True, blank=True)
    letter_grade = models.CharField(_('Letter Grade'), max_length=5, null=True, blank=False)
    cut_off_point = models.DecimalField(_('Cut off Point'), null=True, blank=False, default=0.0,
                                        max_digits=settings.MAX_DIGITS,
                                        decimal_places=settings.MAX_DECIMAL_POINT)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='letter_grade', null=True, blank=True)
    updated_on = models.DateTimeField(_('Updated On'), auto_now=True, null=True, )

    # TODO: Ordering of letter grade

    def __str__(self):
        return to_string(self.course_offering, self.section, self.letter_grade)


class StudentGrade(models.Model):
    enrollment = models.ForeignKey(
        'enrollment.Enrollment',
        on_delete=models.CASCADE,
        related_name="grades",
        null=True,
        blank=False
    )
    grade_fragment = models.ForeignKey(
        GradeFragment,
        on_delete=models.CASCADE,
        related_name="grades",
        null=True,
        blank=False
    )
    grade_quantity = models.DecimalField(
        _('Student Grade Quantity'),
        null=True,
        blank=False,
        decimal_places=settings.MAX_DECIMAL_POINT,
        max_digits=settings.MAX_DIGITS
    )
    remarks = models.CharField(_('Instructor Remarks'), max_length=100, null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(_('Updated On'), auto_now=True, null=True, )

    history = HistoricalRecords()

    class Meta:
        unique_together = ('enrollment', 'grade_fragment')

    def __str__(self):
        return to_string(self.grade_fragment, self.remarks)

    @staticmethod
    def get_section_grades(section_id, grade_fragment_id):
        """
        :param section_id: 
        :param grade_fragment_id: 
        :return: get a list of grades from a section for a grade fragment - Only for active enrollments 
        """
        return StudentGrade.objects.filter(
            enrollment__section=section_id,
            grade_fragment=grade_fragment_id,
            enrollment__active=True
        )

    @staticmethod
    def get_section_average(section, grade_fragment):
        """
        :param section: 
        :param grade_fragment: 
        :return: get section average of a given grade fragment 
        """
        grades = StudentGrade.objects.filter(
            grade_fragment=grade_fragment,
            enrollment__section=section,
            # grade_fragment__student_total_grading=True,
            enrollment__active=True
        ).exclude(grade_quantity=None).values().aggregate(
            sum=Sum('grade_quantity'),
            count=Count('id'),
        )
        if grades['sum']:
            section_average = Decimal(grades['sum'] / grades['count'])
            if grade_fragment.entry_in_percentages:
                section_average = section_average * 100 / grade_fragment.weight
            section_average = section_average
            return section_average if not grades['sum'] is None else 0
        return 0

    # TODO: rework and use view
    @staticmethod
    def get_section_objective_average(section, grade_fragment):
        """
        :param section: 
        :param grade_fragment: 
        :return: section average of all objective grade fragment 
        """
        list_of_averages = []
        total_weight = 0

        fragments = GradeFragment.objects.filter(
            course_offering=section.course_offering,
            boundary_type=GradeFragment.GradesBoundaries.OBJECTIVE,
            student_total_grading=True,
        )

        for fragment in fragments:
            grades = StudentGrade.objects.filter(
                grade_fragment=fragment,
                enrollment__section=section,
                grade_fragment__student_total_grading=True,
                enrollment__active=True
            ).exclude(grade_quantity=None).values().aggregate(
                sum=Sum('grade_quantity'),
                count=Count('id'),
            )

            if grades['sum']:
                total_weight += fragment.weight
                section_average = Decimal(grades['sum'] / grades['count'])
                list_of_averages.append(section_average)

        total_average = Decimal(0)
        for average in list_of_averages:
            total_average += average
        if total_average:
            average = total_average / total_weight
            average = average * 100
            return decimal(average)
        return 0

    @staticmethod
    def get_course_average(section, grade_fragment):
        """        
        :param section: 
        :param grade_fragment: 
        :return: course average for all sections of this grade fragment 
        """
        if section.course_offering.coordinated:
            grades = StudentGrade.objects.filter(
                grade_fragment=grade_fragment,
                grade_fragment__course_offering=section.course_offering,
                grade_fragment__student_total_grading=True,
                enrollment__active=True
            ).exclude(grade_quantity=None).values().aggregate(
                sum=Sum('grade_quantity'),
                count=Count('id'),
            )

            if grades['sum']:
                course_average = Decimal(grades['sum'] / grades['count'])
                if grade_fragment.entry_in_percentages:
                    course_average = course_average * 100 / grade_fragment.weight
                course_average = round(course_average, 2)
                return course_average if not grades['sum'] is None else 0
            return 0
        return False

    @staticmethod
    def get_student_old_grade(fragment, student_id):
        """
        :param fragment: 
        :param student_id: 
        :return:  get the current grade of a student for a grade fragment
        """
        return StudentGrade.objects.get(
            grade_fragment=fragment,
            enrollment__student__university_id__exact=student_id,
            enrollment__active=True
        )

    @staticmethod
    def is_student_grade_exists(fragment, student_id):
        """
        :param fragment: 
        :param student_id: 
        :return: True if student grade do exists else False 
        """
        return StudentGrade.objects.filter(
            grade_fragment=fragment,
            enrollment__student__university_id__exact=student_id,
            enrollment__active=True,
        ).exists()

    # FIXME: Oh oh no, Make me your priority to fix me i really look unpleasant method, others will make fun of me.
    @staticmethod
    def import_grades_by_admin(lines, fragment, current_user, commit=False):
        changes_list = []
        same_list = []
        students_objects = []
        errors = []
        for line in lines.splitlines():
            line = str(line)
            lines_length = len(line.split())
            student_id = None
            new_grade = None
            remark = ""
            if line and lines_length >= 2:
                student_id = line.split()[0]
                new_grade = line.split()[1]
                if lines_length >= 3:
                    for word in line.split()[2:]:
                        remark += " " + word
                part = str(new_grade).partition('.')
                if part[1]:
                    if not part[0].isnumeric() and not part[2].isnumeric():
                        errors.append(
                            {'line': line, 'id': student_id, 'status': _('grade ' + str(new_grade) + ' is invalid'),
                             'code': 'invalid_grade'})
                        continue
                else:
                    if not str(new_grade).isnumeric():
                        errors.append(
                            {'line': line, 'id': student_id, 'status': _('grade ' + str(new_grade) + ' is invalid'),
                             'code': 'invalid_grade'})
                        continue

                if not StudentGrade.is_student_grade_exists(fragment, student_id):
                    errors.append(
                        {'line': line, 'id': student_id, 'status': _('Student ID record not found'),
                         'code': 'no_student'})
                    continue

                grade_object = StudentGrade.get_student_old_grade(fragment, student_id)
                if fragment.entry_in_percentages:
                    percent_new_grade = Decimal(new_grade)
                    new_grade = (grade_object.grade_fragment.weight / 100) * Decimal(new_grade)
                    not_same_grade = new_grade != grade_object.grade_quantity
                    old_percent_grade = None
                    if grade_object.grade_quantity is not None:
                        old_percent_grade = (grade_object.grade_quantity * 100 / grade_object.grade_fragment.weight)

                    if not_same_grade:
                        if Decimal(100) >= percent_new_grade >= Decimal(0.00) and not_same_grade:
                            changes_list.append({'id': student_id,
                                                 'old_grade': old_percent_grade,
                                                 'new_grade': percent_new_grade,
                                                 'status': _(
                                                     'change grade from {} to {}'.format(grade_object.grade_quantity,
                                                                                         new_grade)),
                                                 'code': 'new_grade',
                                                 'remark': remark})
                            students_objects.append(
                                {'grade_object': grade_object, 'new_grade': new_grade, 'remark': remark})
                        else:
                            errors.append({'line': line,
                                           'id': student_id,
                                           'old_grade': old_percent_grade,
                                           'new_grade': percent_new_grade,
                                           'status': _('grade should be between 0 and 100'),
                                           'code': 'invalid_grade'})
                            continue
                    else:
                        same_list.append({'id': student_id,
                                          'old_grade': old_percent_grade,
                                          'new_grade': percent_new_grade,
                                          'status': _(
                                              'same grade from {} to {}'.format(str(grade_object.grade_quantity),
                                                                                new_grade)),
                                          'code': 'same_grade'})
                if not fragment.entry_in_percentages:
                    new_grade = round(Decimal(new_grade), 2)
                    not_same_grade = new_grade != grade_object.grade_quantity
                    if not_same_grade:
                        if grade_object.grade_fragment.weight >= new_grade >= Decimal(0.00):
                            changes_list.append({'id': student_id,
                                                 'old_grade': grade_object.grade_quantity,
                                                 'new_grade': new_grade,
                                                 'status': _(
                                                     'change grade from {} to {}'.format(
                                                         str(grade_object.grade_quantity),
                                                         new_grade)),
                                                 'code': 'new_grade',
                                                 'remark': remark})
                            students_objects.append(
                                {'grade_object': grade_object, 'new_grade': new_grade, 'remark': remark})
                        else:
                            errors.append({'line': line,
                                           'id': student_id,
                                           'old_grade': grade_object.grade_quantity,
                                           'new_grade': new_grade,
                                           'status': _('grade should be between 0 and {}'.format(
                                               str(grade_object.grade_fragment.weight))),
                                           'code': 'invalid_grade'})
                            continue
                    else:
                        same_list.append({'id': student_id,
                                          'old_grade': grade_object.grade_quantity,
                                          'new_grade': new_grade,
                                          'status': _(
                                              'same grade from {} to {}'.format(str(grade_object.grade_quantity),
                                                                                new_grade)),
                                          'code': 'same_grade'})
            else:
                errors.append(
                    {'line': line, 'status': _('There is something wrong in this line'), 'code': 'invalid_line'})

        if commit:
            with transaction.atomic():
                for item in students_objects:
                    item['grade_object'].grade_quantity = item['new_grade']
                    item['grade_object'].remarks = item['remark']
                    item['grade_object'].updated_by = current_user
                    item['grade_object'].updated_on = today()
                    item['grade_object'].save()

        return changes_list, errors

    @property
    def display_percent_grade(self):
        if self.grade_quantity and self.grade_fragment.entry_in_percentages:
            return round((self.grade_quantity * 100) / self.grade_fragment.weight, 2)

        return self.grade_quantity

    @staticmethod
    def display_section_average(section, grade_fragment):
        """
        :param section: 
        :param grade_fragment: 
        :return: get section average of a given grade fragment 
        """
        # TODO: refactor to use only 1 grades function in all averages functions
        grades = StudentGrade.objects.filter(
            grade_fragment=grade_fragment,
            enrollment__section=section,
            # grade_fragment__student_total_grading=True,
            enrollment__active=True
        ).exclude(grade_quantity=None).values().aggregate(
            sum=Sum('grade_quantity'),
            count=Count('id'),
        )
        if grades['sum']:
            section_average = Decimal(grades['sum'] / grades['count'])
            section_average_percent = section_average * 100 / grade_fragment.weight
            display_average = '{}, ({}%)'.format(decimal(section_average), decimal(section_average_percent))
            return display_average if not grades['sum'] is None else ''
        return ''

    @staticmethod
    def display_course_average(section, grade_fragment):
        """        
                :param section: 
                :param grade_fragment: 
                :return: course average for all sections of this grade fragment 
                """
        if section.course_offering.coordinated:
            grades = StudentGrade.objects.filter(
                grade_fragment=grade_fragment,
                grade_fragment__course_offering=section.course_offering,
                grade_fragment__student_total_grading=True,
                enrollment__active=True
            ).exclude(grade_quantity=None).values().aggregate(
                sum=Sum('grade_quantity'),
                count=Count('id'),
            )

            if grades['sum']:
                section_average = Decimal(grades['sum'] / grades['count'])
                section_average_percent = section_average * 100 / grade_fragment.weight
                display_average = '{}, ({}%)'.format(decimal(section_average), decimal(section_average_percent))
                return display_average if not grades['sum'] is None else ''
        return ''


# NOTE: followed this guide: https://blog.rescale.com/using-database-views-in-django-orm/
class SectionsAveragesView(models.Model):
    semester = models.ForeignKey('enrollment.Semester', on_delete=models.DO_NOTHING)
    semester_code = models.CharField(max_length=20)
    course = models.ForeignKey('enrollment.Course', on_delete=models.DO_NOTHING)
    course_code = models.CharField(max_length=20)
    section = models.OneToOneField('enrollment.Section', on_delete=models.DO_NOTHING, related_name='average',
                                   primary_key=True)
    grade_fragment = models.ForeignKey('grade.GradeFragment', on_delete=models.DO_NOTHING)
    boundary_type = models.CharField(max_length=24)
    category = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=10, decimal_places=4)
    grades_average = models.DecimalField(max_digits=10, decimal_places=4)
    grades_average_percentage = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        managed = False
        db_table = 'grade_sectionsaveragesview'

    def __str__(self):
        if self.grade_fragment.entry_in_percentages:
            return str(decimal(self.grades_average_percentage)) + '%'
        else:
            return str(decimal(self.grades_average))


# NOTE: followed this guide: https://blog.rescale.com/using-database-views-in-django-orm/
class CoursesAveragesView(models.Model):
    id = models.BigIntegerField(primary_key=True)
    course_offering = models.ForeignKey('enrollment.CourseOffering', on_delete=models.DO_NOTHING)
    semester = models.ForeignKey('enrollment.Semester', on_delete=models.DO_NOTHING)
    semester_code = models.CharField(max_length=20)
    course = models.ForeignKey('enrollment.Course', on_delete=models.DO_NOTHING)
    course_code = models.CharField(max_length=20)
    grade_fragment = models.ForeignKey('grade.GradeFragment', on_delete=models.DO_NOTHING)
    boundary_type = models.CharField(max_length=24)
    category = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=10, decimal_places=4)
    grades_average = models.DecimalField(max_digits=10, decimal_places=4)
    grades_average_percentage = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        managed = False
        db_table = 'grade_coursesaveragesview'

    def __str__(self):
        if self.grade_fragment.entry_in_percentages:
            return str(decimal(self.grades_average_percentage)) + '%'
        else:
            return str(decimal(self.grades_average))


# NOTE: followed this guide: https://blog.rescale.com/using-database-views-in-django-orm/
class SectionsObjectiveAveragesView(models.Model):
    semester = models.ForeignKey('enrollment.Semester', on_delete=models.DO_NOTHING)
    semester_code = models.CharField(max_length=20)
    course = models.ForeignKey('enrollment.Course', on_delete=models.DO_NOTHING)
    course_code = models.CharField(max_length=20)
    section = models.OneToOneField('enrollment.Section', on_delete=models.DO_NOTHING, related_name='objective_average',
                                   primary_key=True)
    weights_sum = models.DecimalField(max_digits=10, decimal_places=4)
    grades_objective_average = models.DecimalField(max_digits=10, decimal_places=4)
    grades_objective_average_percentage = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        managed = False
        db_table = 'grade_sectionsobjaveragesview'

    def __str__(self):
        return str(decimal(self.grades_objective_average_percentage)) + '%'
