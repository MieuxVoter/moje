This is a django application for launching a majority judgment experiment.


# Installation

The code is assuming you are using `python > 3.5` and `django > 2.0`.

1. Install dependancies:

    pip install django django-extensions numpy matplotlib
    
1. Copy `keys.json` to `keys.local.json` and update parameters. To create a secret key, you can execute the script `./new_private_key.py` and copy the given key.

2. [Connect to your database](https://docs.djangoproject.com/en/2.0/ref/databases/).

3. For deployment to production, always think to the [django checklist](https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/).

# Run server

`python manage.py runserver`
