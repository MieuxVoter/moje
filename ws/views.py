from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import authenticate
from election.tools import *
from django.core.mail import send_mail
import uuid as _uuid
from datetime import datetime, timedelta
from django.utils import timezone



@csrf_exempt
def sign_up(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username', False)
            password = request.POST.get('password', False)
            user = authenticate(username=username, password=password)

            if user is not None and user.is_active:
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=403)
        except ValueError:
            return HttpResponse(status=403)

    return HttpResponse(status=405)


@csrf_exempt
def log_in(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username', False)
            password = request.POST.get('password', False)
            user = authenticate(username=username, password=password)

            if user is not None and user.is_active:
                return JsonResponse({'authentication': 'success'})
            else:
                return HttpResponse(status=403)
        except ValueError:
            return HttpResponse(status=403)

    return HttpResponse(status=405)


@csrf_exempt
def sign_in(request):
    if request.method == 'POST':
        print_debug(request.POST)
        try:
            username = request.POST.get('username', False)
            password = request.POST.get('password', False)
            email = request.POST.get('email', False)

            try:
                user = User.objects.get(
                    email=email,
                    password=password
                )
                if user is not None and user.is_active:
                    return JsonResponse({'authentication': 'success'})
                else:
                    return HttpResponse(status=403)
            except User.DoesNotExist:
                try:
                    user = User(username=username, email=email, password=password)
                    user.save()
                except ValueError:
                    return JsonResponse({'authentication': 'already registred'})

            supervisor = Supervisor.objects.create(user=user)
            supervisor.save()

        except ValueError:
            return HttpResponse(status=403)

    return HttpResponse(status=201)


@csrf_exempt
def reset_password(request):
    if request.method == 'POST':
        try:
            email = request.POST.get('email', False)
            try:
                user = User.objects.get(
                    email=email
                )
                user.password_token = str(_uuid.uuid4())
                now = datetime.now()
                now_add_10 = now + timedelta(minutes=10)
                user.password_token_validity = now_add_10
                user.save()
                send_mail(
                    'Réinitialisation de mot de passe',
                    'Voici le lien pour réinitialiser le mot de passe : ' + settings.URL_NEW_PASSWORD + user.password_token,
                    settings.BELENIOS_MAIL_CONTACT,
                    [user.email],
                    fail_silently=False,
                )

            except User.DoesNotExist:
                return HttpResponse(status=403)

        except ValueError:
            return HttpResponse(status=403)

    return HttpResponse(status=200)


@csrf_exempt
def new_password(request):
    if request.method == 'POST':
        print_debug(request.POST)
        try:
            email = request.POST.get('email', False)
            password = request.POST.get('password', False)
            password_token = request.POST.get('password_token', False)

            try:
                user = User.objects.get(
                    email=email
                )
                if timezone.now() > user.password_token_validity and str(user.password_token) == str(password_token):
                    user.password = password
                    user.save()
            except User.DoesNotExist:
                return HttpResponse(status=403)

        except ValueError:
            return HttpResponse(status=403)

    return HttpResponse(status=200)


def print_debug(msg):
    if getattr(settings, "DEBUG", None):
        print(msg)
    return True
