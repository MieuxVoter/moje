This is a VoTe with [Majority Judgment](https://en.wikipedia.org/wiki/Majority_judgment).


# Installation

The code is assuming you are using `python > 3.5` and `django > 2.0`.

1. Install dependancies:

    pip install -r requirements.txt

2. Copy `keys.json` to `keys.local.json` and update parameters. To create a secret key, you can execute the script `./new_private_key.py` and copy the given key.

3. [Connect to your database](https://docs.djangoproject.com/en/2.0/ref/databases/).

4. Compile translations:

    django-admin compilemessages

For deployment to production, always think to the [django checklist](https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/).

# Run server

`./manage.py runserver`
