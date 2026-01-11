from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    # Create groups used by the project (roles)
    for name in ("operator", "admin"):
        Group.objects.get_or_create(name=name)
