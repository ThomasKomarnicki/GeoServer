from models import Location, LocationGuess, User
from rest_framework import serializers
from django.db import models
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Avg, Min
from django.utils import timezone


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    other_identifier = serializers.CharField(required=False,max_length=50)
    google_auth_id = models.CharField(max_length=50, null=True)
    current_location = serializers.IntegerField(required=False)
    guessed_locations = serializers.CharField(required=False)
    level = serializers.Field(source='get_progression_level', read_only=True)

    class Meta:
        model = User
    #     fields = ('email', 'other_identifier', 'current_location', 'guessed_locations')

    def validate(self, data):

        print "validating user"

        if 'email' in data:
            try:
                validate_email(data['email'])
            except ValidationError:
                serializers.ValidationError("invalid email")

        # if 'email' in data and 'other_identifier' in data:
        #     serializers.ValidationError("no identifiers provided")

        elif 'email' not in data and 'other_identifier' not in data:
            serializers.ValidationError("must provide email or other identifier")

        elif User.objects.filter(email=data['email']).exists():
            serializers.ValidationError("user with email exists")

        return data


class LocationSerializer(serializers.ModelSerializer):

    average_guess_distance = serializers.ReadOnlyField(source='_get_average')
    best_guess_distance = serializers.ReadOnlyField(source='_get_best')
    lat = serializers.DecimalField(max_value=90, min_value=-90, max_digits=20, decimal_places=17)
    lon = serializers.DecimalField(max_value=180, min_value=-180, max_digits=20, decimal_places=17)
    date_added = serializers.DateTimeField(default=timezone.now())
    id = serializers.ReadOnlyField()

    class Meta:
        model = Location
        fields = ('lat', 'lon', 'average_guess_distance', 'best_guess_distance', 'date_added', 'id')

    def _get_average(self):
        return LocationGuess.objects.aggregate(Avg('distance'))

    def _get_best(self):
        return Location.objects.all().aggregate(Min('distance'))


class LocationField(serializers.PrimaryKeyRelatedField):

    def to_representation(self, value):
        location = self.queryset.get(id=value.pk)
        return LocationSerializer(location).data



class LocationGuessSerializer(serializers.ModelSerializer):

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    # user = UserSerializer()
    # location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    location = LocationField(queryset=Location.objects.all())
    lat = serializers.DecimalField(max_value=90, min_value=-90, max_digits=20, decimal_places=17)
    lon = serializers.DecimalField(max_value=180, min_value=-180, max_digits=20, decimal_places=17)
    score = serializers.IntegerField(read_only=True)

    class Meta:
        model = LocationGuess
        fields = ('user', 'location', 'lat', 'lon','score')

