from django import template

from enrollment.models import Coordinator, Instructor

register = template.Library()


@register.inclusion_tag('_user_menu.html', takes_context=True)
def user_menu(context):
    user = context['request'].user

    if user.is_authenticated:
        # TODO: Add a user group called 'Admins' and include it in the condition below
        can_see_admin_controls = user.is_superuser

        if hasattr(user, 'instructor'):
            is_coordinator = Coordinator.is_active_coordinator(user.instructor)
            user_full_name = str(user.instructor)
        else:
            is_coordinator = False
            user_full_name = '%s %s' % (user.first_name, user.last_name)

        can_give_excuses = Instructor.can_give_excuses(user)

        return {
            'user': user,
            'user_full_name': user_full_name,
            'can_see_admin_controls': can_see_admin_controls,
            'is_coordinator': is_coordinator,
            'can_give_excuses': can_give_excuses,
        }
