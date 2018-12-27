from rest_framework import serializers


class ElectionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    note = serializers.CharField()
    start = serializers.DateField()
    end = serializers.DateField()
    state = serializers.CharField()


class CandidateSerializer(serializers.Serializer):
    election = ElectionSerializer()
    label = serializers.CharField()
    description = serializers.CharField()
    program = serializers.CharField()


class GradeSerializer(serializers.Serializer):
    election = ElectionSerializer()
    name = serializers.CharField()
    code = serializers.CharField()


class GradeResultSerializer(serializers.Serializer):
    candidate_str = serializers.CharField() 
    grade_str = serializers.CharField()
    result = serializers.FloatField()


class OnlyCandidateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    label = serializers.CharField()

class OnlyGradeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
