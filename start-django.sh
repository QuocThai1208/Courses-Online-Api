cd /home/truong/Courses-Online-Api
source venv/bin/activate
exec gunicorn --workers 3 --bind 160.25.81.159:8080 coursesapp.wsgi:application