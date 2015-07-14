__author__ = 'clem'

from django import template

register = template.Library()

@register.simple_tag
def fullname(user):
	return "%s %s" % (user.first_name, user.last_name)