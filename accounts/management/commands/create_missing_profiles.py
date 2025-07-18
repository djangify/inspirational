# accounts/management/commands/create_missing_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile

class Command(BaseCommand):
    help = 'Creates UserProfile objects for users who do not have one'

    def handle(self, *args, **kwargs):
        users_without_profiles = []
        
        # Find users without profiles
        for user in User.objects.all():
            try:
                # Just checking if this raises an exception
                user.profile
            except User.profile.RelatedObjectDoesNotExist:
                users_without_profiles.append(user)
        
        # Create profiles for users who don't have one
        profiles_created = 0
        for user in users_without_profiles:
            UserProfile.objects.create(user=user)
            profiles_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {profiles_created} missing user profiles'
            )
        )
        