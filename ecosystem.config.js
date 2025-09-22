
module.exports = {
    apps: [
        {
            name: "django-app",
            script: "gunicorn",
            args: "coursesapp.wsgi:application --bind 0.0.0.0:8080",
            // Đường dẫn Python trong virtualenv
            interpreter: "/home/truong/course-be/Courses-Online-Api/venv/bin/python3",
            cwd: "/home/truong/course-be/Courses-Online-Api",
            env: {
                DJANGO_SETTINGS_MODULE: "coursesapp.settings",
                PYTHONUNBUFFERED: "1"
            }
        }
    ]
};
