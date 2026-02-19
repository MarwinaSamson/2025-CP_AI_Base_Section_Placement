web: gunicorn section_placement_system.wsgi --timeout 120 --workers 1 --threads 2 --log-file -
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
