# accounts/signals.py
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings
from .models import Role, User

@receiver(post_save, sender=User)
def sync_perms_on_user_save(sender, instance, created, **kwargs):
    instance.sync_role_permissions()

@receiver(m2m_changed, sender=Role.permissions.through)
def sync_perms_on_role_change(sender, instance, action, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        for user in instance.users.all():
            user.sync_role_permissions()

@receiver(m2m_changed, sender=User.extra_permissions.through)
def sync_on_extra_perms_change(sender, instance, action, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        instance.sync_role_permissions()

