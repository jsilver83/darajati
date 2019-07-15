from datetime import datetime

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, F
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from attendance.models import ScheduledPeriod, AttendanceInstance
from enrollment.models import Section, Enrollment, Student, CourseOffering, Instructor
from enrollment.utils import get_local_datetime_format
from .test_banner_data import class_rhasta


def get_format_section_code(course_code, section_code):
    return '{}-{}'.format(course_code, section_code)


class Synchronization(object):

    def __init__(self, course_offering, current_user, commit=False, first_week_mode=False):
        # TODO: course offering already passed (FIX)
        self.course_offering = CourseOffering.get_course_offering(course_offering)
        self.current_user = current_user
        self.commit = commit
        self.first_week_mode = first_week_mode
        if not self.course_offering:
            raise ValueError(_('Make sure provided Course Offering is a valid one'))

        self.course_code = self.course_offering.course.code
        self.semester_code = self.course_offering.semester.code

        # set global variables to be used
        self.roster_information = self.get_roster_information()
        self.sections = self.course_offering.sections.all()
        self.non_created_sections = []
        self.changed_sections = []
        self.result = None
        self.section = None
        self.crns = []
        self.student = None
        self.none = None
        self.new_enrollments = []
        self.current_enrollments = []
        self.old_enrollments = []
        self.inactive_enrollment = []
        self.all_sections = []
        self.enrollment = None
        self.dropped_enrollments = self.get_enrollments().filter(active=True)
        # instructor
        self.instructor = None
        self.faculty_period = None

        # Periods
        self.current_day = None
        self.period = None
        self.non_created_periods = []
        self.periods_with_issues = []

    def get_roster_information(self):
        """
        This will call banner-api to get students enrollment to a the assigned course offering
        :return: list of enrollments
        """
        try:
            url = settings.ROSTER_WEB_SERVICE + self.semester_code + '/' + self.course_code
            response = requests.get(url, auth=(settings.BANNER_API_USER, settings.BANNER_API_PASSWORD))
            response = response.json()
            return response.get('data')
        except:
            # TODO: verify it works
            # webservice unreachable for some reason
            raise ValueError(
                _('There is an issue with the connection to the Registrar system. Class roster can NOT be '
                  'fetched at the moment for {} and {}. Kindly contact the system admin or try again later'
                  .format(self.semester_code, self.course_code))
            )

    def get_section_faculties(self, section):
        """
        This will call banner-api to get faculty that are assigned to this given section
        :return: list of
        """
        try:
            url = settings.FACULTY_WEB_SERVICE + self.semester_code + '/' + section.crn
            response = requests.get(url, auth=(settings.BANNER_API_USER, settings.BANNER_API_PASSWORD))
            response = response.json()
            return response.get('data')
        except:
            # TODO: verify it works
            # webservice unreachable for some reason
            raise ValueError(
                _('There is an issue with the connection to the Registrar system. Scheduled periods '
                  'listing can NOT be fetched at the moment. Kindly contact the system admin or try again '
                  'later'))

    def get_enrollments(self):
        """
        :return:
        """
        return Enrollment.objects.filter(section__course_offering=self.course_offering)

    def roaster_initiation(self):
        """
        This is the main enrollment assignment it has the main loop that most of other
        functions will be ran into.
        :return: none
        """

        for index, self.result in enumerate(self.roster_information):
            # if self.first_week_mode:
            self.create_or_activate_sections()
            self.create_or_get_student()
            self.assign_or_change_enrollment()

        self.is_inactive_enrollment()
        if self.commit:
            self.commit_roaster_changes()

    def is_inactive_enrollment(self):
        for dropped_enrollment in self.dropped_enrollments:
            dropped_enrollment.active = False
            dropped_enrollment.comment = 'Dropped with no letter grade'
            dropped_enrollment.letter_grade = 'Dropped'
            dropped_enrollment.updated_by = self.current_user
            self.inactive_enrollment.append(dropped_enrollment)

    def create_or_activate_sections(self):
        """
        :return:
        """
        section_code = get_format_section_code(self.course_code, self.result['sec'])
        if not Section.is_section_exists_in_course_offering(self.course_offering, section_code) and \
                self.result['crn'] not in self.crns:
            self.section = Section(
                course_offering=self.course_offering,
                code=section_code,
                crn=self.result['crn'],
                active=True
            )
            self.all_sections.append(self.section)
            self.non_created_sections.append(self.section)
            self.crns.append(self.result['crn'])

        else:
            if self.result['crn'] in self.crns:
                return
            self.section = Section.objects.get(
                course_offering__exact=self.course_offering,
                code__exact=section_code,
                crn=self.result['crn']
            )
            if not self.section.active and self.section.crn not in self.crns:
                self.section.active = True
                self.all_sections.append(self.section)
                self.changed_sections.append(self.section)
                self.crns.append(self.section.crn)

    def create_or_get_student(self):
        """
        :return:
        """
        self.student, created = Student.objects.get_or_create(
            university_id=self.result['stu_id']
        )
        self.student.government_id = self.result['stu_id']
        self.student.english_name = self.result['name_en']
        self.student.arabic_name = self.result['name_ar']
        self.student.mobile = self.result['mobile']
        self.student.personal_email = self.result['email']
        self.student.active = True
        self.student.save()

    def assign_or_change_enrollment(self):
        """
        :return:
        """
        self.dropped_enrollments = self.dropped_enrollments.exclude(
            section=self.section,
            student=self.student
        )
        if self.commit:
            self.section.save()
        if not Enrollment.is_enrollment_exists(self.student, self.section):
            self.enrollment = Enrollment(
                section=self.section,
                student=self.student,
                updated_by=self.current_user,
                register_date=get_local_datetime_format(self.result['reg_date']),
                letter_grade=self.result['grade']
            )
            current_old_enrollments = Enrollment.objects.filter(
                student=self.student,
                section__course_offering=self.course_offering,
            )

            if current_old_enrollments:
                for old_enrollment in current_old_enrollments:
                    old_enrollment.comment = 'Moved to other section {}'.format(self.section)
                    old_enrollment.letter_grade = 'MOVED'
                    old_enrollment.updated_by = self.current_user
                    old_enrollment.active = False
                    self.old_enrollments.append(old_enrollment)

            if self.check_if_enrollment_has_inactive_letter_grade() and self.enrollment.active:
                self.enrollment.comment = 'Dropped with grade {}'.format(str(self.result['grade']).lower())
                self.enrollment.updated_by = self.current_user
                self.enrollment.active = False
                self.inactive_enrollment.append(self.enrollment)
            else:
                self.new_enrollments.append(self.enrollment)

        else:
            self.enrollment = Enrollment.objects.get(
                student=self.student,
                section=self.section
            )

            current_old_enrollments = Enrollment.objects.filter(
                student=self.student,
                section__course_offering=self.course_offering,
                active=True
            ).exclude(pk=self.enrollment.pk)

            for old_enrollment in current_old_enrollments:
                old_enrollment.comment = 'Moved to other section {}'.format(self.section)
                old_enrollment.letter_grade = 'MOVED'
                old_enrollment.updated_by = self.current_user
                old_enrollment.active = False
                self.old_enrollments.append(old_enrollment)

            self.enrollment.letter_grade = self.result['grade']

            # Case 1 When enrollment is active and has no letter grade
            # than the registrar update the letter grade with one of the 5 letter grades
            # ['w', 'wp', 'wf', 'ic', 'dn'] than deactivate the student
            if self.check_if_enrollment_has_inactive_letter_grade() and self.enrollment.active:
                self.enrollment.active = False
                self.enrollment.comment = 'Dropped with grade {}'.format(str(self.result['grade']).lower())
                self.enrollment.updated_by = self.current_user
                self.inactive_enrollment.append(self.enrollment)

            # Case 2 if student was deactivated and he got changed back to active by
            # the registrar this means student do not have a letter grade from the 5
            # ['w', 'wp', 'wf', 'ic', 'dn'] so he should be activated
            elif not self.check_if_enrollment_has_inactive_letter_grade() and not self.enrollment.active:
                self.enrollment.active = True
                self.current_enrollments.append(self.enrollment)

    def check_if_enrollment_has_inactive_letter_grade(self):
        """
        :return:
        """
        current_letter_grade = str(self.enrollment.letter_grade).lower()
        letter_grades = ['w', 'wp', 'wf', 'ic', 'dn']
        return True if current_letter_grade in letter_grades else False

    def commit_roaster_changes(self):
        with transaction.atomic():
            # Enrollment
            for new_enrollment in self.new_enrollments:
                new_enrollment.save()

            for current_enrollment in self.current_enrollments:
                current_enrollment.save()

            for moved_enrollment in self.old_enrollments:
                moved_enrollment.save()

            for enrollment in self.inactive_enrollment:
                enrollment.save()

    def faculty_initiation(self):
        """
        :return:
        """
        for self.section in self.sections:
            faculties_periods = self.get_section_faculties(self.section)
            for self.faculty_period in faculties_periods:
                if not self.faculty_period['email'] and not self.faculty_period['user']:
                    continue
                self.create_or_get_instructor()
                self.create_or_get_periods()

        if self.commit:
            self.commit_faculties_periods()

    def create_or_get_instructor(self):
        """
        :return:
        """
        user, created = User.objects.get_or_create(username=self.faculty_period['user'])
        self.instructor, created = Instructor.objects.get_or_create(
            user=user,
            university_id=self.faculty_period['fac_id']
        )
        self.instructor.government_id = self.faculty_period['fac_id']
        self.instructor.english_name = self.faculty_period['name']
        self.instructor.arabic_name = self.faculty_period['name']
        self.instructor.personal_email = self.faculty_period['email']
        self.instructor.active = True
        self.instructor.save()

    def create_or_get_periods(self):
        """
        :return:
        """
        # ENGLEP there is something called virtual section this has to be handled.
        if self.faculty_period['class_days'] and \
                self.faculty_period['room'] and \
                self.faculty_period['activity']:
            for day in map(str, self.faculty_period['class_days']):
                self.current_day = self.get_period_current_day(day)
                start_time = self.get_period_start_time()
                end_time = self.get_period_end_time()
                if not ScheduledPeriod.is_period_exists(self.section, self.instructor, self.current_day, start_time,
                                                        end_time):
                    self.period = ScheduledPeriod(
                        section=self.section,
                        instructor_assigned=self.instructor,
                        day=self.current_day,
                        title=self.faculty_period['activity'],
                        start_time=start_time,
                        end_time=end_time,
                        location=self.faculty_period['bldg'] + ' ' + self.faculty_period['room'],
                    )
                    self.non_created_periods.append(self.period)
        else:
            if self.section not in self.periods_with_issues:
                self.periods_with_issues.append(self.section)

    def get_period_current_day(self, day):
        if day == 'U':
            return ScheduledPeriod.Days.SUNDAY
        if day == 'M':
            return ScheduledPeriod.Days.MONDAY
        if day == 'T':
            return ScheduledPeriod.Days.TUESDAY
        if day == 'W':
            return ScheduledPeriod.Days.WEDNESDAY
        if day == 'R':
            return ScheduledPeriod.Days.THURSDAY

    def get_period_start_time(self):
        start_time = list(map(str, self.faculty_period['start_time']))
        start_time = start_time[0] + start_time[1] + ':' + start_time[2] + start_time[3]
        return start_time

    def get_period_end_time(self):
        end_time = list(map(str, self.faculty_period['end_time']))
        end_time = end_time[0] + end_time[1] + ':' + end_time[2] + end_time[3]
        return end_time

    def commit_faculties_periods(self):
        with transaction.atomic():
            for new_period in self.non_created_periods:
                new_period.save()

    def sections_report(self):
        report = []
        for new_section in self.non_created_sections:
            report.append(
                {'section': new_section, 'code': 'CREATE', 'message': 'New section to be created.'}
            )
        for changed_section in self.changed_sections:
            report.append(
                {'section': changed_section, 'code': 'CHANGED', 'message': 'section has been changed.'}
            )
        return report

    def enrollments_report(self):
        report = []
        for new_enrollment in self.new_enrollments:
            report.append(
                {'enrollment': new_enrollment, 'code': 'CREATE', 'message': 'New enrollment to be created.'}
            )
        for old_enrollment in self.old_enrollments:
            report.append(
                {'enrollment': old_enrollment, 'code': 'CHANGED', 'message': 'Enrollment has been changed.'}
            )
        for current_enrollment in self.current_enrollments:
            report.append(
                {'enrollment': current_enrollment, 'code': 'CHANGED', 'message': 'Enrollment has been changed.'}
            )
        for inactive_enrollment in self.inactive_enrollment:
            report.append(
                {'enrollment': inactive_enrollment, 'code': 'INACTIVE',
                 'message': 'Enrollment will be set to inactive.'}
            )
        return report

    def faculties_periods_report(self):
        report = []
        for non_created_period in self.non_created_periods:
            report.append(
                {'period': non_created_period, 'code': 'CREATE', 'message': 'Period to be created.'}
            )
        for period_with_issue in self.periods_with_issues:
            report.append(
                {'period': period_with_issue, 'code': 'MI-VS',
                 'message': 'This period has missing information or it belongs to virtual section'}
            )
        return report


def get_class_roster_from_banner(course_offering):
    """
    :return: list of enrollments from banner through api
    """
    course_code = course_offering.course.code
    semester_code = course_offering.semester.code
    try:
        url = settings.ROSTER_WEB_SERVICE + semester_code + '/' + course_code
        response = requests.get(url, auth=(settings.BANNER_API_USER, settings.BANNER_API_PASSWORD))
        response = response.json()
        return response.get('data')
    except:
        # TODO: fix this
        # webservice unreachable for some reason
        raise ValueError(
            _('There is an issue with the connection to the Registrar system. Class roster can NOT be '
              'fetched at the moment for {} and {}. Kindly contact the system admin or try again later'
              .format(semester_code, course_code))
        )


def get_section_scheduled_periods(course_offering, section_crn):
    """
    :return: list of scheduled periods (from banner through api) of a given section
    """
    semester_code = course_offering.semester.code
    try:
        url = settings.FACULTY_WEB_SERVICE + semester_code + '/' + section_crn
        response = requests.get(url, auth=(settings.BANNER_API_USER, settings.BANNER_API_PASSWORD))
        response = response.json()
        return response.get('data')
    except:
        # TODO: verify it works
        # webservice unreachable for some reason
        raise ValueError(
            _('There is an issue with the connection to the Registrar system. Scheduled periods '
              'listing can NOT be fetched at the moment. Kindly contact the system admin or try again '
              'later'))


def make_hashable(list_of_dicts):
    return {frozenset(row.items()) for row in list_of_dicts}


def get_student_record(student_university_id, enrollments_in_banner):
    return next((s for s in enrollments_in_banner if s["stu_id"] == student_university_id), None)


def get_or_create_student(student_university_id, enrollments_in_banner, students_to_be_updated, existing_students_list):
    for student in existing_students_list:
        if student_university_id == student.university_id:
            return student

    student_record = get_student_record(student_university_id, enrollments_in_banner)

    student, created = Student.objects.get_or_create(university_id=student_university_id)

    if created:
        student.arabic_name = student_record.get('name_ar')
        student.english_name = student_record.get('name_en')
        student.mobile = student_record.get('mobile')
        student.personal_email = student_record.get('email')
        student.active = True
        students_to_be_updated.append(student)
    return student


def get_section_by_crn(crn, course_offering, fetched_sections, sections_to_be_created):
    for section in fetched_sections:  # Try to fetch it from previous fetched sections
        if section.crn == crn and section.course_offering == course_offering:
            return section
    for section in sections_to_be_created:  # Try to fetch it from sections to be created
        if section.crn == crn and section.course_offering == course_offering:
            return section
    try:
        section = Section.objects.get(crn=crn, course_offering=course_offering)
        fetched_sections.append(section)
        return section
    except:
        pass


def update_sections_pks(enrollments_or_periods, sections_to_be_created):
    for enrollment_or_period in enrollments_or_periods:
        for section in sections_to_be_created:
            if enrollment_or_period.section.crn == section.crn and enrollment_or_period.section.course_offering == section.course_offering:
                enrollment_or_period.section = section
                break


inactive_letter_grades = ['w', 'wp', 'wf', 'ic', 'dn']


def get_student_status_by_letter_grade(letter_grade):
    return False if letter_grade in inactive_letter_grades else True


def get_day_from_shortcut_char(shortcut_day_car):
    if shortcut_day_car == 'U':
        return ScheduledPeriod.Days.SUNDAY
    if shortcut_day_car == 'M':
        return ScheduledPeriod.Days.MONDAY
    if shortcut_day_car == 'T':
        return ScheduledPeriod.Days.TUESDAY
    if shortcut_day_car == 'W':
        return ScheduledPeriod.Days.WEDNESDAY
    if shortcut_day_car == 'R':
        return ScheduledPeriod.Days.THURSDAY


def get_period_location(building, room):
    return '%s %s' % (building, room)


def get_teacher_record(teacher_user_id, all_scheduled_periods_banner):
    for period in all_scheduled_periods_banner:
        if period["user"] == teacher_user_id:
            return {
                'fac_id': period.get('fac_id'),
                'user': period.get('user'),
                'email': period.get('email'),
                'name': period.get('name'),
            }


def get_or_create_teacher(teacher_user_id, all_scheduled_periods_banner, teachers_to_be_updated):
    teacher_record = get_teacher_record(teacher_user_id, all_scheduled_periods_banner)

    user, created = User.objects.get_or_create(username=teacher_user_id)

    teacher, created = Instructor.objects.get_or_create(user=user)

    if created:
        teacher.english_name = teacher_record.get('name')
        teacher.university_id = teacher_record.get('fac_id')
        teacher.personal_email = teacher_record.get('email')
        teacher.active = True
        teachers_to_be_updated.append(teacher)
    return teacher


def update_period_info(darajati_period, banner_period, all_scheduled_periods_banner,
                       all_scheduled_periods_darajati, periods_to_be_updated, teachers_to_be_updated,
                       periods_changes_report):
    period_to_be_updated = ScheduledPeriod.objects.get(pk=darajati_period['pk'])
    period_to_be_updated.instructor_assigned = get_or_create_teacher(banner_period['user'],
                                                                     all_scheduled_periods_banner,
                                                                     teachers_to_be_updated)
    period_to_be_updated.location = get_period_location(banner_period['bldg'],
                                                        banner_period['room'])
    period_to_be_updated.title = banner_period['activity']

    periods_to_be_updated.append(period_to_be_updated)
    all_scheduled_periods_darajati.remove(darajati_period)

    periods_changes_report.append(
        {
            'code': 'UPDATE PERIOD',
            'message': '%s (%s - %s) [%s], taught by (%s), for section %s will be created' %
                       (period_to_be_updated.day,
                        period_to_be_updated.start_time,
                        period_to_be_updated.end_time, banner_period['activity'],
                        banner_period['user'], period_to_be_updated.section.code,),
        }
    )


def resolve_duplicated_periods(master_period, duplicated_periods, attendance_instances_to_be_updated):
    master_period_obj = ScheduledPeriod.objects.get(pk=master_period['pk'])
    for period in duplicated_periods:
        period_obj = ScheduledPeriod.objects.get(pk=period['pk'])
        if period_obj.attendance_dates.count():
            for attendance_instance in period_obj.attendance_dates.all():
                attendance_instance.period = master_period_obj
                attendance_instances_to_be_updated.append(attendance_instance)


def synchronization(course_offering_pk, current_user, commit=False, first_week_mode=False):
    course_offering = get_object_or_404(CourseOffering, pk=course_offering_pk)

    class_roster = get_class_roster_from_banner(course_offering)

    serious_issues = []

    sections_changes_report = []
    sections_to_be_created = []
    sections_to_be_updated = []
    fetched_sections = []

    periods_changes_report = []
    teachers_to_be_updated = []
    periods_to_be_created = []
    periods_to_be_updated = []
    attendance_instances_to_be_updated = []
    periods_to_be_deleted = []
    virtual_periods = []  # for some periods in ENGLEP

    if first_week_mode:

        # region sync sections
        sections_in_banner = [{'code': get_format_section_code(course_offering.course.code, d['sec']),
                               'crn': d['crn']} for d in class_roster]

        # used set/frozenset to get distinct list of sections from the list of enrollments in banner
        unique_sections_in_banner = [dict(x) for x in set(frozenset(d.items()) for d in sections_in_banner)]

        # needed only crn's distinct list to use it in the query afterwards to get all active sections in the system
        unique_sections_crns_in_banner = [d['crn'] for d in unique_sections_in_banner]
        already_existing_sections = course_offering.sections.filter(
            crn__in=unique_sections_crns_in_banner,
            active=True,
        ).values('code', 'crn')

        missing_sections = [dict(i) for i in (make_hashable(unique_sections_in_banner) -
                                              make_hashable(already_existing_sections))]

        sections_to_be_deactivated = [dict(i) for i in (make_hashable(already_existing_sections) -
                                                        make_hashable(unique_sections_in_banner))]

        sections_to_be_reactivated = []
        if missing_sections:
            missing_sections_crns = [d['crn'] for d in missing_sections]
            missing_sections_that_already_exists_but_inactive = course_offering.sections.filter(
                crn__in=missing_sections_crns,
                active=False,
            )
            sections_to_be_reactivated = list(missing_sections_that_already_exists_but_inactive)
            temp2 = missing_sections_that_already_exists_but_inactive.values('crn', 'code')
            missing_sections = [x for x in missing_sections if x not in temp2]

        for section in missing_sections:
            sections_changes_report.append(
                {
                    'code': 'NEW SECTION',
                    'message': '%s (CRN: %s) is a new section that was NOT created before in Darajati' %
                               (section.get('code'), section.get('crn')),
                }
            )
            sections_to_be_created.append(
                Section(crn=section.get('crn'), code=section.get('code'), course_offering=course_offering)
            )

        for section in sections_to_be_deactivated:
            sections_changes_report.append(
                {
                    'code': 'REACTIVATE SECTION',
                    'message': '%s (CRN: %s) was inactive in Darajati and is going to reactivated' %
                               (section.get('code'), section.get('crn')),
                }
            )
            section_to_be_deactivated = Section.objects.get(crn=section.get('code'), course_offering=course_offering)
            section_to_be_deactivated.active = False
            sections_to_be_updated.append(section_to_be_deactivated)

        for section in sections_to_be_reactivated:
            sections_changes_report.append(
                {
                    'code': 'REACTIVATE SECTION',
                    'message': '%s (CRN: %s) was inactive in Darajati and is going to reactivated' %
                               (section.code, section.crn),
                }
            )
            section_to_be_reactivated = Section.objects.get(crn=section.crn, course_offering=course_offering)
            section_to_be_reactivated.active = False
            sections_to_be_updated.append(section_to_be_reactivated)

        # endregion sync sections

        # region sync sections' scheduled periods
        
        # TODO: add an endpoint in banner-api to get all periods using only course_offering
        all_scheduled_periods_banner = []
        for crn in unique_sections_crns_in_banner:
            all_scheduled_periods_banner += get_section_scheduled_periods(course_offering, crn)

        all_scheduled_periods_darajati = list(ScheduledPeriod.objects.filter(
            section__course_offering=course_offering
        ).select_related('instructor_assigned', 'section').values('pk', 'section__crn',
                                                                  'instructor_assigned__user__username',
                                                                  'day', 'start_time', 'end_time', 'title', 'location'))

        count_of_duplicated_periods_that_will_be_deleted = 0
        for banner_period in all_scheduled_periods_banner:

            if banner_period['class_days'] and \
                    banner_period['room'] and \
                    banner_period['activity']:
                for day in map(get_day_from_shortcut_char, banner_period['class_days']):
                    start_time = datetime.strptime(banner_period['start_time'], "%H%M").time()
                    end_time = datetime.strptime(banner_period['end_time'], "%H%M").time()

                    matching_periods = list(filter(lambda period: period['section__crn'] == banner_period['crn'] and
                                                                  period['day'] == day and
                                                                  period['start_time'] == start_time and
                                                                  period['end_time'] == end_time,
                                                   all_scheduled_periods_darajati))

                    first_match = None
                    if not matching_periods:
                        the_section = get_section_by_crn(banner_period['crn'], course_offering, fetched_sections,
                                                         sections_to_be_created)
                        new_period = ScheduledPeriod()
                        new_period.section = the_section
                        new_period.instructor_assigned = get_or_create_teacher(banner_period['user'],
                                                                               all_scheduled_periods_banner,
                                                                               teachers_to_be_updated)
                        new_period.start_time = start_time
                        new_period.end_time = end_time
                        new_period.day = day
                        new_period.title = banner_period['activity']
                        new_period.location = get_period_location(banner_period['bldg'], banner_period['room'])

                        # TODO: fix showing all enrollments as serious issues when initial population because no
                        #  sections are created yet
                        if the_section:
                            periods_to_be_created.append(new_period)

                            verb = 'got' if commit else 'will be'
                            periods_changes_report.append(
                                {
                                    'code': 'NEW PERIOD',
                                    'message': '%s (%s - %s) [%s], taught by (%s), for section %s %s created' %
                                               (day, start_time, end_time, banner_period['activity'],
                                                banner_period['user'], the_section.code, verb),
                                }
                            )
                        else:
                            serious_issues.append(
                                {
                                    'urgency': 'URGENT',
                                    'code': 'MISSING SECTION',
                                    'message': 'Period (%s, %s - %s) could NOT be created because section crn %s is not'
                                               ' created yet' % (day, start_time, end_time, banner_period['crn']),
                                    'object': new_period,
                                }
                            )

                    elif len(matching_periods) == 1:  # only one period is (semi) matching
                        first_match = matching_periods[0]

                        if first_match['instructor_assigned__user__username'] == banner_period['user'] and first_match[
                            'title'] == banner_period['activity'] and first_match['location'] == get_period_location(
                            banner_period['bldg'], banner_period['room']):
                            pass  # perfect match: no need to do anything

                        else:
                            # some info got updated in registrar system and needs to be updated in darajati too
                            update_period_info(first_match, banner_period,
                                               all_scheduled_periods_banner, all_scheduled_periods_darajati,
                                               periods_to_be_updated, teachers_to_be_updated, periods_changes_report)

                    elif len(matching_periods) > 1:
                        # Important Case: multiple periods are (semi) matching; so we have data replication
                        # that needs to be resolved so that attendances of replicated periods are NOT lost
                        for period in matching_periods:
                            if period['instructor_assigned__user__username'] == banner_period['user'] and \
                                    period['title'] == banner_period['activity'] and \
                                    period['location'] == get_period_location(banner_period['bldg'],
                                                                              banner_period['room']):
                                first_match = period

                        if first_match:
                            matching_periods.remove(first_match)
                            resolve_duplicated_periods(first_match, matching_periods,
                                                       attendance_instances_to_be_updated)
                        else:
                            update_period_info(matching_periods[0], banner_period,
                                               all_scheduled_periods_banner, all_scheduled_periods_darajati,
                                               periods_to_be_updated, teachers_to_be_updated, periods_changes_report)
                            resolve_duplicated_periods(matching_periods[0], matching_periods,
                                                       attendance_instances_to_be_updated)
                            matching_periods.remove(matching_periods[0])

                        for p in matching_periods:
                            count_of_duplicated_periods_that_will_be_deleted += 1
                            periods_to_be_deleted.append(p)
                            all_scheduled_periods_darajati.remove(p)
            else:
                virtual_periods.append(banner_period)
                periods_changes_report.append(
                    {
                        'code': 'VIRTUAL PERIOD',
                        'message': 'Period for section (CRN: %s), taught by (%s), is a virtual period and will NOT be'
                                   ' created' % (banner_period['crn'], banner_period['user'],),
                    }
                )

        if count_of_duplicated_periods_that_will_be_deleted:
            periods_changes_report.append(
                {
                    'code': 'DUPLICATE PERIODS',
                    'message': '%s periods will be deleted because they are duplicated' %
                               count_of_duplicated_periods_that_will_be_deleted,
                }
            )

        # print(periods_changes_report)
        # print(teachers_to_be_updated)
        # print(periods_to_be_created)
        # print(periods_to_be_updated)
        # print(periods_to_be_deleted)
        # print(attendance_instances_to_be_updated)
        # print(virtual_periods)
        # endregion

    # region sync enrollments
    enrollments_in_banner = [{'university_id': d['stu_id'],
                              'crn': d['crn'],
                              'grade': (str(d['grade']).lower() if d['grade'] else None)}
                             for d in class_roster]

    existing_students_list = list(Student.objects.filter(
        university_id__in=Enrollment.objects.filter(section__course_offering=course_offering).values('student__university_id')
    ))

    # TODO: include select related
    existing_enrollments = Enrollment.objects.annotate(
        grade=Lower('letter_grade'),
        crn=F('section__crn'),
        university_id=F('student__university_id'),
    ).filter(
        Q(section__course_offering=course_offering) &
        (Q(active=True) |
         (Q(active=False) & Q(grade__in=inactive_letter_grades)))
    ).values('university_id', 'crn', 'grade')

    existing_dropped_enrollments_wo_grade = Enrollment.objects.annotate(
        grade=Lower('letter_grade'),
        crn=F('section__crn'),
        university_id=F('student__university_id'),
    ).filter(active=False).exclude(grade__in=inactive_letter_grades).values(
        'university_id', 'crn', 'grade'
    )

    enrollments_to_be_created = []
    enrollments_to_be_updated = []
    students_to_be_updated = []
    enrollments_changes_report = []

    hashed_enrollments_in_banner = make_hashable(enrollments_in_banner)
    hashed_existing_enrollments = make_hashable(existing_enrollments)

    enrollments_banner_minus_darajati = [dict(i) for i in (hashed_enrollments_in_banner - hashed_existing_enrollments)]
    enrollments_darajati_minus_banner = [dict(i) for i in (hashed_existing_enrollments - hashed_enrollments_in_banner)]

    for enrollment in enrollments_banner_minus_darajati:

        # region CASE 0: new student
        found_currently_active = list(filter(
            lambda student: student['university_id'] == enrollment['university_id'], enrollments_darajati_minus_banner))

        found_currently_inactive = list(filter(
            lambda student: student['university_id'] == enrollment['university_id'],
            existing_dropped_enrollments_wo_grade))

        if not found_currently_active and not found_currently_inactive:
            new_section = get_section_by_crn(enrollment['crn'], course_offering, fetched_sections,
                                             sections_to_be_created)
            new_enrollment = Enrollment()
            new_enrollment.student = get_or_create_student(enrollment['university_id'],
                                                           class_roster, students_to_be_updated, existing_students_list)
            new_enrollment.register_date = get_student_record(enrollment['university_id'],
                                                              class_roster).get('register_date')
            new_enrollment.letter_grade = enrollment['grade']
            new_enrollment.active = get_student_status_by_letter_grade(enrollment['grade'])
            new_enrollment.updated_by = current_user
            new_enrollment.section = new_section
            if new_section:
                enrollments_to_be_created.append(new_enrollment)
                verb = 'got' if commit else 'will be'
                enrollments_changes_report.append(
                    {
                        'code': 'NEW',
                        'message': '%s %s created' % (enrollment['university_id'], verb),
                    }
                )
            else:
                serious_issues.append(
                    {
                        'urgency': 'URGENT',
                        'code': 'MISSING SECTION',
                        'message': '%s could NOT be created because section crn %s is not created yet' % (
                            enrollment['university_id'], enrollment['crn']),
                        'object': new_enrollment,
                    }
                )
        # endregion

        # region CASE 1: student dropped without grade before but got reactivated by registrar again
        found_currently_active = list(filter(
            lambda student: student['university_id'] == enrollment['university_id'], enrollments_darajati_minus_banner))

        if not found_currently_active:
            reactivated = list(filter(
                lambda student: student['university_id'] == enrollment['university_id'],
                existing_dropped_enrollments_wo_grade))

            if reactivated:
                print(enrollment['university_id'])
                enrollment_to_be_reactivated = Enrollment.objects.select_related('student', 'section').get(
                    student__university_id=enrollment['university_id'],
                    section__course_offering=course_offering,
                )

                enrollment_to_be_reactivated.active = True
                enrollment_to_be_reactivated.comment = 'Student dropped without grade before but got reactivated ' \
                                                       'again by registrars'
                enrollment_to_be_reactivated.letter_grade = enrollment['grade']
                enrollment_to_be_reactivated.register_date = get_student_record(enrollment['university_id'],
                                                                                class_roster
                                                                                ).get('register_date')
                enrollment_to_be_reactivated.updated_by = current_user
                enrollments_to_be_updated.append(enrollment_to_be_reactivated)
                enrollments_changes_report.append(
                    {
                        'code': 'REACTIVATED',
                        'message': '%s dropped without grade before but got reactivated again by registrars' %
                                   enrollment['university_id'],
                    }
                )
        # endregion

        # region CASE 2: student moved to a different section in the same course
        moved = list(filter(
            lambda student: student['university_id'] == enrollment['university_id'] and student['crn'] != enrollment[
                'crn'], enrollments_darajati_minus_banner))

        if moved:
            moved_enrollment = Enrollment.objects.select_related('student', 'section').get(
                student__university_id=enrollment['university_id'],
                section__course_offering=course_offering,
            )
            new_section = get_section_by_crn(enrollment['crn'], course_offering, fetched_sections,
                                             sections_to_be_created)
            moved_enrollment.active = False
            moved_enrollment.comment = 'Moved to another section (%s)' % str(new_section)
            moved_enrollment.updated_by = current_user
            moved_enrollment.letter_grade = 'MOVED'
            enrollments_to_be_updated.append(moved_enrollment)

            moving_enrollment = Enrollment()
            moving_enrollment.student = moved_enrollment.student
            moving_enrollment.section = new_section
            moving_enrollment.updated_by = current_user
            moving_enrollment.letter_grade = enrollment['grade']
            moving_enrollment.active = get_student_status_by_letter_grade(enrollment['grade'])
            moving_enrollment.register_date = get_student_record(enrollment['university_id'],
                                                                 class_roster).get('register_date')
            moving_enrollment.comment = 'Moved from another section (%s)' % str(moved_enrollment.section)

            if new_section:
                enrollments_to_be_created.append(moving_enrollment)
                enrollments_changes_report.append(
                    {
                        'code': 'MOVED TO SECTION',
                        'message': '%s got moved to section %s (CRN: %s)' % (
                            enrollment['university_id'],
                            new_section.code,
                            enrollment['crn'],
                        )
                    }
                )
            else:
                serious_issues.append(
                    {
                        'urgency': 'URGENT',
                        'code': 'MISSING SECTION',
                        'message': '%s could NOT be created because section crn %s is not created yet' % (
                            enrollment['university_id'], enrollment['crn']),
                        'object': moving_enrollment,
                    }
                )

        # endregion

        # region CASE 3: student changed grade or dropped with grade in ['w', 'wp', 'wf', 'ic', 'dn']
        changed_grade = list(filter(
            lambda student: student['university_id'] == enrollment['university_id'] and student['crn'] == enrollment[
                'crn'], enrollments_darajati_minus_banner))

        if changed_grade:
            enrollment_with_grade_to_be_changed = Enrollment.objects.get(
                student__university_id=enrollment['university_id'],
                section__course_offering=course_offering,
            )
            old_grade = enrollment_with_grade_to_be_changed.letter_grade
            enrollment_with_grade_to_be_changed.active = get_student_status_by_letter_grade(enrollment['grade'])
            enrollment_with_grade_to_be_changed.updated_by = current_user
            enrollment_with_grade_to_be_changed.letter_grade = enrollment['grade']
            enrollments_to_be_updated.append(enrollment_with_grade_to_be_changed)
            enrollments_changes_report.append(
                {
                    'code': 'LETTER GRADE CHANGED',
                    'message': '%s letter grade got changed from %s to %s' % (
                        enrollment['university_id'],
                        old_grade,
                        enrollment['grade'],
                    )
                }
            )
        # endregion

    # region CASE 4: student dropped without grade
    for enrollment in enrollments_darajati_minus_banner:
        match = list(filter(
            lambda student: student['university_id'] == enrollment['university_id'], enrollments_banner_minus_darajati))

        if not match:
            enrollment_to_be_dropped = Enrollment.objects.get(student__university_id=enrollment['university_id'],
                                                              section__course_offering=course_offering)
            enrollment_to_be_dropped.active = False
            enrollment_to_be_dropped.comment = 'Student dropped the course without grade'
            enrollment_to_be_dropped.letter_grade = 'DROPPED'
            enrollment_to_be_dropped.updated_by = current_user
            enrollments_to_be_updated.append(enrollment_to_be_dropped)

            enrollments_changes_report.append(
                {
                    'code': 'DROPPED WITHOUT GRADE',
                    'message': '%s dropped the course without grade' % enrollment['university_id']
                }
            )
    # endregion

    # print(enrollments_changes_report)

    # print(students_to_be_updated)
    # print(serious_issues)

    # endregion sync enrollments

    # This needs to be done even if commit is False since records of these students have been created with minimal data.
    # The only downside to this approach is storage utilization...
    # The alternative is to delete them if commit is False but performance-wise, it is worse since it will require more
    # trips to the DB
    if first_week_mode:
        with transaction.atomic():
            Student.objects.bulk_update(students_to_be_updated,
                                        ['arabic_name', 'english_name', 'mobile', 'personal_email'], batch_size=100)
            Instructor.objects.bulk_update(teachers_to_be_updated,
                                           ['english_name', 'university_id', 'personal_email'], batch_size=100)

    if commit:
        with transaction.atomic():
            # CREATE
            Section.objects.bulk_create(sections_to_be_created, batch_size=100)

            update_sections_pks(periods_to_be_created, sections_to_be_created)
            ScheduledPeriod.objects.bulk_create(periods_to_be_created, batch_size=100)

            update_sections_pks(enrollments_to_be_created, sections_to_be_created)
            Enrollment.objects.bulk_create(enrollments_to_be_created, batch_size=100)

            # UPDATE
            AttendanceInstance.objects.bulk_update(attendance_instances_to_be_updated, ['period'], batch_size=100)
            ScheduledPeriod.objects.bulk_update(periods_to_be_updated,
                                                ['instructor_assigned', 'location', 'title'], batch_size=100)
            Enrollment.objects.bulk_update(enrollments_to_be_updated,
                                           ['active', 'comment', 'letter_grade', 'register_date'], batch_size=100)

            # DELETE
            for period in periods_to_be_deleted:
                ScheduledPeriod.objects.filter(pk=period.get('pk', 0)).delete()

    return [enrollments_changes_report, sections_changes_report, periods_changes_report, serious_issues]
