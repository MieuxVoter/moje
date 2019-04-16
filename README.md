Moje is an application for [MajOrity JudgmEnt](https://en.wikipedia.org/wiki/Majority_judgment).
It is supposed to be used as a middleware between a front-end and a server used for storing votes.
It can also serve a basic front-end.



# Installation

The code is assuming you are using `python >= 3.6` and `django > 2.0`.

1. Install dependancies:

    pip install -r requirements.txt

2. Update parameters by creating a new configuration file. In `config/`, the YAML file with the highest number is used in priority.
To create a secret key, you can execute the script `./scripts/new_private_key.py` and copy the given key.

3. [Connect to your database](https://docs.djangoproject.com/en/2.0/ref/databases/).

4. Compile translations:

    django-admin compilemessages

For deployment to production, always think to the [django checklist](https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/).

# Run server

`./manage.py runserver`


