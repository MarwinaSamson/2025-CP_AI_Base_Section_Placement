web: gunicorn section_placement_system.wsgi --log-file -
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
