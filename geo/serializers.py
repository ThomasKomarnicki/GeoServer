from models import Location, LocationGuess, User
from rest_framework import serializers
from django.db import models
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Avg, Min

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    other_identifier = serializers.CharField(required=False,max_length=50)
    google_auth_id = models.CharField(max_length=50, null=True)
    current_location = serializers.IntegerField(required=False)
    guessed_locations = serializers.CharField(required=False)

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

    # user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    # average_guess_distance = serializers.IntegerField(required=False)
    # best_guess_distance = serializers.IntegerField(required=False)
    average_guess_distance = serializers.ReadOnlyField(source='_get_average')
    best_guess_distance = serializers.ReadOnlyField(source='_get_best')
    lat = serializers.DecimalField(max_value=90, min_value=-90, max_digits=20, decimal_places=17)
    lon = serializers.DecimalField(max_value=180, min_value=-180, max_digits=20, decimal_places=17)
    date_added = serializers.DateField()

    class Meta:
        model = Location
        # fields = ('lat', 'lon', 'user', 'average_guess_distance', 'best_guess_distance')

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

    class Meta:
        model = LocationGuess
        fields = ('user', 'location', 'lat', 'lon')

