import os
import sys


def main():
    """
    Configure the environment for Django settings and execute the Django
    command-line utility for administrative tasks. This function sets the
    default settings module for the Django project, attempts to import the
    Django management module, and executes the command line with the
    provided arguments. Raises an ImportError if Django is not installed
    or not available in the environment.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mycloud.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
