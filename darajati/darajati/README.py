"""
Never Forget these key points when making methods within a model class:
# disclaimer:  This is what i do understand - malnajdi
"""
# @staticmethod
# You can think of them as methods that can be accessed without the need
# of an instance of the same class and it do not accept self nor cls.
#
# Normal methods
# Can only be called with an object instance of the same class, and it accept self.
#
# @property
# usually used for display or apply a new way of presenting values of an instance of the class
# something like returning the full_name where you will combine the 3 fields you have
# first_name, middle_name and last_name


# Class
class People(object):

    @staticmethod
    def get_all_members_of_ictc():
        return People.objects.filter(department='ICTC')

    def check_member_of_ictc(self):
        if self.department == 'ICTC':
            return True
        return False

    @property
    def get_member_full_name(self):
        return self.first_name + " " + self.middle_name + " " + self.last_name
# Usage

People.get_all_members_of_ictc()  # This will return a list of people belong to ICTC
member = People.objects.get(username='malnajdi')  # get the instance of this username
member.check_member_of_ictc()  # True
member.get_member_full_name  # Mohammed Yousef Alnajdi

