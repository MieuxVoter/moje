from django.http import HttpResponse
from election.tools import *
from django.views.decorators.csrf import csrf_exempt
from subprocess import call
import uuid as _uuid
import json
from django.conf import settings
from slugify import slugify
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.core import serializers
from ws.serialize import *
from pathlib import Path
from datetime import datetime, date


@csrf_exempt
def election_create(request):

    if request.method != 'POST':
        return HttpResponse(status=403)

    # Enregistre si l'élection est anonyme ou non
    is_anonymous = True
    try:
        if 'anonymous' in request.POST and request.POST['anonymous'] and request.POST['anonymous'] != "":
            if request.POST['anonymous'] == 'false':
                is_anonymous = False
            else:
                is_anonymous = True
    except ValueError:
        return HttpResponse(status=403)

    election = Election.objects.create(is_anonymous=is_anonymous)

    try:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if not user:
            return HttpResponse(status=403)

    except ValueError:
        return HttpResponse(status=403)

    # Nom de l'élection
    election.name = request.POST['name']

    # Description de l'élection
    election.note = request.POST['note']

    election.state = Election.DRAFT

    # Enregistrement de la date de début et date de fin programmé de l'élection
    try:
        if 'start_election_date' in request.POST and request.POST['start_election_date'] and request.POST['start_election_date'] != "":
            election.start = request.POST['start_election_date']

        if 'end_election_date' in request.POST and request.POST['end_election_date'] and request.POST['end_election_date'] != "":
            election.end = request.POST['end_election_date']
    except ValueError:
        return HttpResponse(status=403)

    # Enregistrement de l'uuid
    uuid = str(_uuid.uuid4())
    election.belenios_uuid = uuid
    election.save()

    # Candidats de l'élection
    candidates_json = json.loads(request.POST['candidates'])
    candidates = []

    # Jugements de l'élection
    grades_json = json.loads(request.POST['grades'])
    grades = []

    # Votants de l'élection
    voters = request.POST.getlist('voters')

    # étape 2 On setup le superviseur
    Supervisor.objects.create(user=user, election=election)

    # étape 3 On enregistre les jugements
    for grade_json in grades_json:
        grade = Grade.objects.create()
        grade.name = grade_json['value']
        grade.code = grade_json['value']
        grade.election = election
        grade.save()
        grades.append(grade_json['value'])

    # étape 4 On enregistre les candidats
    for candidate_json in candidates_json:
        candidate = Candidate.objects.create()
        candidate.label = candidate_json['value']
        candidate.election = election
        candidate.save()
        candidates.append(candidate_json['value'])

    number_of_voter = len(voters)

    try:
        # étape 5 on créé les fichiers de l'élection
        belenios_moje_folder = settings.BELENIOS_PATH

        election.belenios_uuid = uuid
        exec_cmd('mkdir ' + belenios_moje_folder + uuid)

        print_debug('Create election file')
        print_debug('--------')
        # print_debug(election)
        print_debug(grades)
        print_debug(candidates)
        print_debug('--------')
        is_created = create_election_file(election, grades, candidates, belenios_moje_folder + uuid)
        if is_created:
            election.state = Election.START
            election.save()

        print_debug('Common options')
        uuid_cmd = '--uuid ' + uuid
        group_cmd = '--group ' + belenios_moje_folder + 'groups/default.json'

        # credential authority generate credentials
        # l 'autorité d' identification génére des informations d'identification
        if number_of_voter < 0:
            print_debug('Generate credentials')
            exec_cmd(
                'belenios-tool credgen ' + uuid_cmd + ' ' + group_cmd + ' --dir ' + belenios_moje_folder + uuid + ' --count ' + str(
                    number_of_voter))

            exec_cmd(
                'mv ' + belenios_moje_folder + uuid + '/*.pubcreds ' + belenios_moje_folder + uuid + '/public_creds.txt')
            exec_cmd(
                'mv ' + belenios_moje_folder + uuid + '/*.privcreds ' + belenios_moje_folder + uuid + '/private_creds.txt')

        # keypair generation for trustee
        # génération de clé pour le.s dépositaire.s
        print_debug('Generate trustee keys')
        exec_cmd('belenios-tool trustee-keygen ' + group_cmd)
        exec_cmd('cat *.pubkey > public_keys.jsons')

        print_debug('Generate election parameters')
        exec_cmd('belenios-tool mkelection ' + uuid_cmd + ' ' + group_cmd + ' --template ' +
                 belenios_moje_folder + uuid + '/questions.json')

        exec_cmd('mv *.privkey ' + belenios_moje_folder + uuid)
        exec_cmd('mv *.pubkey ' + belenios_moje_folder + uuid)
        exec_cmd('mv *.jsons ' + belenios_moje_folder + uuid)
        exec_cmd('mv election.json ' + belenios_moje_folder + uuid)

        print_debug('election id :' + str(election.id))

        print_debug("UUID : '" + uuid + "'")

        send_mail(
            'L\'élection à bien été créée',
            'Voici le lien de pour suivre l\'élection : ' + settings.URL_ELECTION_DETAIL + str(election.belenios_uuid),
            settings.BELENIOS_MAIL_CONTACT,
            [user.email],
            fail_silently=False,
        )

    except ValueError:
        # TODO: Log error
        return HttpResponse(status=500)

    # étape 6 On envoie les informations aux votants
    if number_of_voter < 0:
        text_file = open(belenios_moje_folder + uuid + '/private_creds.txt', "r")
        key_list = text_file.read().split('\n')
        print_debug('contenu du fichier de private_creds : ')
        print_debug(key_list)
        count = 0
        for voter_str in voters:
            key_id, key = key_list[count].split()
            print_debug('votant / id / clé : ')
            print_debug(voter_str + ' / ' + key_id + ' / ' + key)
            exec_cmd('echo "' + key_id + ' ' + key + '" > ' + belenios_moje_folder + uuid + '/' + key + '.txt')
            try:
                user = User.objects.get(
                    email=voter_str
                )
                print_debug(user)
            except User.DoesNotExist:
                user = User(email=voter_str, username=voter_str)
                user.save()

            # on relie l'utilisateur au vote
            submit_election_to_voter(voter_str, user.id, key, election.belenios_uuid)
            # TODO sauvegarder l'id de la private key pour récupérer la key et la renvoyé si besoin
            voter = Voter.objects.create(user=user, election=election)
            # TODO corriger bug intégrité BDD duplicate key
            voter.save()
            count += 1

    auto_close_election()

    return JsonResponse({'id_election': str(election.id)})


@csrf_exempt
def election_information(request):
    auto_close_election()
    if request.method != 'POST':
        return HttpResponse(status=403)

    try:
        election_uuid = None
        voter_key = None
        if 'id_election' in request.POST and request.POST['id_election'] and request.POST['id_election'] != "":
            election_uuid = request.POST['id_election']
        if 'voter_key' in request.POST and request.POST['voter_key'] and request.POST['voter_key'] != "":
            voter_key = request.POST['voter_key']

        election = Election.objects.get(belenios_uuid=str(election_uuid))
        grades = Grade.objects.filter(election=election)
        grades_serializer = OnlyGradeSerializer(grades, many=True)

        candidates = Candidate.objects.filter(election=election)
        candidates_serializer = OnlyCandidateSerializer(candidates, many=True)


        try:
            belenios_moje_folder = settings.BELENIOS_PATH
            exec_cmd('grep -q "' + voter_key + '" "' + belenios_moje_folder + election_uuid + '/private_creds.txt"')
            return JsonResponse(
                {
                    'id_election': str(election.id),
                    'candidates': json.dumps(candidates_serializer.data),
                    'ballot_name': str(election.name),
                    'ballot_note': str(election.note),
                    'grades': json.dumps(grades_serializer.data)
                    # 'id_election': str(election.id),
                    # 'candidates': str(candidates.label),
                    # 'ballot_name': str(election.name),
                    # 'ballot_note': str(election.note),
                    # 'grades': str(grades.name),
                    # 'rates': str(grades.name)
                }
            )
        except ValueError:
            return HttpResponse(status=403)

    except ValueError:
        # TODO: Log error
        return HttpResponse(status=500)


@csrf_exempt
def election_detail(request):


    if request.method != 'POST':
        return HttpResponse(status=403)

    try:
        election_uuid = None
        if 'id_election' in request.POST and request.POST['id_election'] and request.POST['id_election'] != "":
            election_uuid = request.POST['id_election']

        election = Election.objects.get(belenios_uuid=str(election_uuid))

        file_path = settings.BELENIOS_PATH + election.belenios_uuid + '/private_creds.txt'
        file = Path(file_path)
        if file.is_file():
            number_voter = sum(1 for line in open(file_path))
            number_ballot = Voter.objects.filter(election=election, ballot__isnull=False).count()
        else:
            number_voter = 0
            number_ballot = 0

        try:
            return JsonResponse(
                {
                    'id_election': str(election.id),
                    'ballot_name': str(election.name),
                    'ballot_note': str(election.note),
                    'number_voter': str(number_voter),
                    'number_ballot': str(number_ballot)
                }
            )
        except ValueError:
            return HttpResponse(status=403)

    except ValueError:
        # TODO: Log error
        return HttpResponse(status=500)


@csrf_exempt
def election_voter_add(request):
    if request.method != 'POST':
        return HttpResponse(status=403)

    try:
        id_election = None
        email = None
        if 'id_election' in request.POST and request.POST['id_election'] and request.POST['id_election'] != "":
            id_election = request.POST['id_election']
        if 'email' in request.POST and request.POST['email'] and request.POST['email'] != "":
            email = request.POST['email']

        print_debug(request.POST)

        if id_election is not None and email is not None:
            election = Election.objects.get(id=id_election)
            belenios_moje_folder = settings.BELENIOS_PATH
            uuid = election.belenios_uuid
            print_debug(uuid)
            uuid_cmd = '--uuid ' + uuid
            group_cmd = '--group ' + belenios_moje_folder + 'groups/default.json'

            # credential authority generate credentials
            # l 'autorité d' identification génére des informations d'identification
            print_debug('Generate credentials')
            print_debug(
                'belenios-tool credgen ' + uuid_cmd + ' ' + group_cmd + ' --dir ' + belenios_moje_folder + uuid + ' --count 1')
            exec_cmd(
                'belenios-tool credgen ' + uuid_cmd + ' ' + group_cmd + ' --dir ' + belenios_moje_folder + uuid + ' --count 1')

            exec_cmd(
                'cat ' + belenios_moje_folder + uuid + '/*.pubcreds > ' + belenios_moje_folder + uuid + '/public_creds.txt')
            exec_cmd(
                'cat ' + belenios_moje_folder + uuid + '/*.privcreds > ' + belenios_moje_folder + uuid + '/private_creds.txt')

            print_debug('voter add :' + email)
            print_debug("UUID : '" + uuid + "'")

            text_file = open(belenios_moje_folder + uuid + '/private_creds.txt', "r")
            key_list = text_file.read().split('\n')

            key_id, key = key_list[len(key_list) - 2].split()
            print_debug('votant / id / clé : ')
            print_debug(email + ' / ' + key_id + ' / ' + key)
            try:
                user = User.objects.get(
                    email=email
                )
                print_debug(user)
            except User.DoesNotExist:
                user = User(email=email, username=email)
                user.save()
            # on relie l'utilisateur au vote
            submit_election_to_voter(email, user.id, key, election.belenios_uuid)
            # TODO sauvegarder l'id de la private key pour récupérer la key et la renvoyé si besoin
            voter = Voter.objects.create(user=user, election=election)
            # TODO corriger bug intégrité BDD duplicate key
            voter.save()
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=403)

    except ValueError:
        # TODO: Log error
        return HttpResponse(status=500)

    return HttpResponse(status=201)


@csrf_exempt
def vote_create(request):
    if request.method == 'POST':
        print_debug(request.method)

        # La clé doit être présente
        if 'private_key' in request.POST and request.POST['private_key'] and request.POST['private_key'] != "":
            # On vérifie que la private key existe
            # TODO vérifier que la private key existe
            # On vérifie que l'élection existe
            try:
                election = Election.objects.get(id=request.POST['id_election'])
                print_debug('uuid de l\'élection : ' + election.belenios_uuid)
            except Election.DoesNotExist:
                return HttpResponse(status=403)

            # Récupération du chemin physique de l'élection
            election_path = str(settings.BELENIOS_PATH) + str(election.belenios_uuid)

            # Création du fichier de vote sur le serveur Belenios
            vote = request.POST['vote']
            vote_path = create_user_vote_file(vote, election_path + '/')
            print_debug(vote_path)
            print_debug('Récupération du vote')
            exec_cmd('belenios-tool vote --dir ' + str(election_path) +
                     ' --privcred <(echo "' + str(request.POST['private_key']) + '") --ballot ' + vote_path
                     + ' >> ' + str(election_path) + '/ballots.jsons')

            # Récupération de l'utilisateur pour lui envoyer un mail et stocker son vote si élection non anonyme
            user = User.objects.get(id=request.POST['voter_id'])
            if user:
                send_mail(
                    'Vote pris en compte',
                    'Votre vote à bien été pris en compte',
                    settings.BELENIOS_MAIL_CONTACT,
                    [user.email],
                    fail_silently=False,
                )

            # Enregistrement du vote si l'élection n'est pas anonymisée
            if user:
                if not election.is_anonymous:
                    voter = Voter.objects.get(user=user, election=election)
                    voter.ballot = vote
                    voter.save()
                else:
                    voter = Voter.objects.get(user=user, election=election)
                    voter.ballot = '[private]'
                    voter.save()

            #except election.DoesNotExist:
            #    return HttpResponse(status=500)

            return HttpResponse(status=201)

    return HttpResponse(status=405)


@csrf_exempt
def close_election(request):
    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if not user:
            return HttpResponse(status=403)

        try:
            election = Election.objects.get(id=request.POST['id_election'])
            print_debug('uuid de l\'élection : ' + election.belenios_uuid)
        except election.DoesNotExist:
            return HttpResponse(status=403)

        if not Supervisor.objects.get(user=user, election=election):
            return HttpResponse(status=403)

        # Récupération du chemin physique de l'élection
        election_path = str(settings.BELENIOS_PATH) + str(election.belenios_uuid) + '/'

        print_debug('Cloture de l\'élection : ')
        exec_cmd('for u in ' + election_path + '*.privkey; do\n' +
                 'belenios-tool decrypt --dir ' + election_path + ' --privkey $u\n' +
                 'echo >&2\n' +
                 'done > ' + election_path + 'partial_decryptions.tmp\n' +
                 'mv ' + election_path + 'partial_decryptions.tmp ' + election_path + 'partial_decryptions.jsons')

        exec_cmd('belenios-tool validate --dir ' + election_path)

        exec_cmd('belenios-tool verify --dir ' + election_path)

        get_election_result(election)
        election.state = Election.OVER
        election.save()

        voter_list = Voter.objects.filter(election=election)
        for voter in voter_list:
            send_mail(
                'Cloture du vote ' + election.name + '. ',
                'Voici le lien pour consulter les résultats : ' + settings.URL_ELECTION_RESULT + str(
                    election.belenios_uuid),
                settings.BELENIOS_MAIL_CONTACT,
                [voter.user.email],
                fail_silently=False,
            )

        results = GradeResult.objects.filter(election=election)
        serializer = GradeResultSerializer(results, many=True)

        return JsonResponse({'results': serializer.data}, safe=False)

    return HttpResponse(status=405)


@csrf_exempt
def delete_election(request):
    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if not user:
            return HttpResponse(status=403)

        try:
            election = Election.objects.get(id=request.POST['id_election'])
            print_debug('uuid de l\'élection : ' + election.belenios_uuid)
        except election.DoesNotExist:
            return HttpResponse(status=403)

        if not Supervisor.objects.get(user=user, election=election):
            return HttpResponse(status=403)

        election.state = Election.DRAFT
        election.save()

        return HttpResponse(status=200)

    return HttpResponse(status=405)


@csrf_exempt
def supervisor_election_list(request):
    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if not user:
            return HttpResponse(status=403)

        json_list = []
        election_objects = Supervisor.objects.filter(user=user)
        for election_object in election_objects:
            serializer = ElectionSerializer(election_object.election, many=False)
            print_debug(serializer.data)
            json_list.append({'election': serializer.data})

        return JsonResponse(json_list, safe=False)

    return HttpResponse(status=405)


@csrf_exempt
def supervisor_election_result(request):
    if request.method == 'POST':

        id_election = request.POST['id_election']

        election = Election.objects.get(id=id_election)
        if election.state != Election.OVER:
            return JsonResponse({'results': None}, safe=False)

        results = GradeResult.objects.filter(election=election)
        serializer = GradeResultSerializer(results, many=True)
        print_debug({'results': serializer.data})

        return JsonResponse({'results': serializer.data}, safe=False)

    return HttpResponse(status=405)


def get_election_result(election):
    json_result_path = str(settings.BELENIOS_PATH) + str(election.belenios_uuid) + '/result.json'

    with open(json_result_path) as json_result_file:
        json_results = json.load(json_result_file)
        print_debug(json_results)

        index = 0
        # TODO : si aucun vote il y a une erreur car division par 0
        for result in json_results['result']:
            percentage_1 = safe_div(result[0], (result[0] + result[1] + result[2] + result[3] + result[4])) * 100
            percentage_2 = safe_div(result[1], (result[0] + result[1] + result[2] + result[3] + result[4])) * 100
            percentage_3 = safe_div(result[2], (result[0] + result[1] + result[2] + result[3] + result[4])) * 100
            percentage_4 = safe_div(result[3], (result[0] + result[1] + result[2] + result[3] + result[4])) * 100
            percentage_5 = safe_div(result[4], (result[0] + result[1] + result[2] + result[3] + result[4])) * 100

            grade_1 = Grade.objects.get(election=election, code="Excellent")
            grade_result_1 = GradeResult()
            grade_result_1.election = election
            grade_result_1.grade = grade_1
            grade_result_1.candidate = Candidate.objects.filter(election=election)[index]
            grade_result_1.result = percentage_1
            grade_result_1.save()

            grade_2 = Grade.objects.get(election=election, code="Bien")
            grade_result_2 = GradeResult()
            grade_result_2.election = election
            grade_result_2.grade = grade_2
            grade_result_2.candidate = Candidate.objects.filter(election=election)[index]
            grade_result_2.result = percentage_2
            grade_result_2.save()

            grade_3 = Grade.objects.get(election=election, code="Passable")
            grade_result_3 = GradeResult()
            grade_result_3.election = election
            grade_result_3.grade = grade_3
            grade_result_3.candidate = Candidate.objects.filter(election=election)[index]
            grade_result_3.result = percentage_3
            grade_result_3.save()

            grade_4 = Grade.objects.get(election=election, code="Insuffisant")
            grade_result_4 = GradeResult()
            grade_result_4.election = election
            grade_result_4.grade = grade_4
            grade_result_4.candidate = Candidate.objects.filter(election=election)[index]
            grade_result_4.result = percentage_4
            grade_result_4.save()

            grade_5 = Grade.objects.get(election=election, code="A rejeter")
            grade_result_5 = GradeResult()
            grade_result_5.election = election
            grade_result_5.grade = grade_5
            grade_result_5.candidate = Candidate.objects.filter(election=election)[index]
            grade_result_5.result = percentage_5
            grade_result_5.save()

            index += 1


def safe_div(x, y):
    if y == 0:
        return 0
    return x/y


def exec_cmd(cmd, shell=True):
    print_debug(cmd)
    result_cmd = call(cmd, shell=True, executable="/bin/bash")
    if result_cmd != 0:
        raise ValueError('invalid command: ' + cmd)


def submit_election_to_voter(email, user_id, key, belenios_uuid):
    send_mail(
        'Voter pour l\'election',
        'Voici le lien de pour voter : ' + settings.URL_BALLOT + str(belenios_uuid) + '/' + str(key) + '/' + str(user_id),
        settings.BELENIOS_MAIL_CONTACT,
        [email],
        fail_silently=False,
    )


def create_election_file(election, answers, candidates, folder):
    try:
        questions = []

        for candidate in candidates:
            questions.append({
                'answers': answers,
                'min': 1,
                'max': 1,
                'question': candidate
            })

        data = {
            'description': election.note,
            'name': election.name,
            'questions': questions
        }

        file_path_name = folder + '/questions.json'
        with open(file_path_name, 'w') as fp:
            json.dump(data, fp)

        # Création du fichier de vote vide
        open("ballots.jsons", "w+")

    except ValueError:
        return ValueError

    return True


def create_user_vote_file(data, folder):
    try:
        file_path_name = folder + str(_uuid.uuid4()) + '.vote'
        print_debug('Nom du fichier de vote : ')
        print_debug(file_path_name)
        with open(file_path_name, 'w') as fp:
            fp.write(str(data))

    except ValueError:
        return ValueError

    return file_path_name


def auto_close_election():
    try:
        elections = Election.objects.filter(state=Election.START, end__isnull=False)

        for election in elections:
            print_debug(election.end)
            print_debug("-----")
            print_debug(date.today())
            if election.end > date.today():
                print_debug('pas clos')
            else:
                print_debug('a clore')

            try:
                print_debug('uuid de l\'élection : ' + election.belenios_uuid)

                # Récupération du chemin physique de l'élection
                election_path = str(settings.BELENIOS_PATH) + str(election.belenios_uuid) + '/'

                voter_list = Voter.objects.filter(election=election)
                for voter in voter_list:
                    send_mail(
                        'Cloture du vote ' + election.name + '. ',
                        'Voici le lien pour consulter les résultats : ' + settings.URL_ELECTION_RESULT + str(election.belenios_uuid),
                        settings.BELENIOS_MAIL_CONTACT,
                        [voter.user.email],
                        fail_silently=False,
                    )

                print_debug('Cloture de l\'élection : ')
                exec_cmd('for u in ' + election_path + '*.privkey; do\n' +
                         'belenios-tool decrypt --dir ' + election_path + ' --privkey $u\n' +
                         'echo >&2\n' +
                         'done > ' + election_path + 'partial_decryptions.tmp\n' +
                         'mv ' + election_path + 'partial_decryptions.tmp ' + election_path + 'partial_decryptions.jsons')

                exec_cmd('belenios-tool validate --dir ' + election_path)

                exec_cmd('belenios-tool verify --dir ' + election_path)

                get_election_result(election)
                election.state = Election.OVER
                election.save()
            except ValueError:
                # TODO log
                continue

    except ValueError:
        return ValueError



def print_debug(msg):
    if getattr(settings, "DEBUG", None):
        print(msg)
    return True
