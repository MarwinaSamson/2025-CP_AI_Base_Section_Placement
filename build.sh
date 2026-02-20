#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser and profile from environment variables (if set)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
from admin_app.models import UserProfile
import os

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

user, created = User.objects.get_or_create(username=username, defaults={'email': email, 'is_superuser': True, 'is_staff': True})
if created:
    user.set_password(password)
    user.save()
    print('Superuser created!')
else:
    print('Superuser already exists.')

# Create UserProfile if needed
profile, profile_created = UserProfile.objects.get_or_create(user=user, defaults={'user_type': 'admin'})
if profile_created:
    print('Admin profile created!')
else:
    print('Admin profile already exists.')
EOF
fi
