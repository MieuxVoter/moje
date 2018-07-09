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



# Roadmap


1) Langue Français par défaut, avec le choix de la langue sur le côté (anglais), ce qui est super :-)

2) le language par défaut en Français (7 mentions):
Excellent, Très bien, Bien, Assez bien, Passable, Insuffisant, A Rejeter

3) Le language par défaut en anglais (7 mentions):
Outstanding, Excellent, Very Good, Good, Fair, Poor, To Reject

4) La question doit paraitre sur le bulletin moment de voter (j’ai pas vérifier si c’est le cas)

5) quand on vote, à défaut c’est en blanc, et quand on clique sur une mention, ca se colorie avec la couleur de la mention

6) les résultats affichent la mention majoritaire (coloré avec sa couleur), le total des notes au dessus, et le total en dessous

7) le logo de mieux voter (sur le coté gauche) et le lien vers MieuxVoter.fr activé!
