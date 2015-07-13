from models import Location, LocationGuess, User
from rest_framework import serializers
from django.db import models
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    other_identifier = serializers.CharField(required=False,max_length=50)
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
                serializers.ValidationError("invalid email" ,1)

        if 'email' in data and 'other_identifier' in data:
            serializers.ValidationError("no identifiers provided", 2)

        elif 'email' not in data:
            pass # user other identifier

        elif User.objects.filter(email=data['email']).exists():
            serializers.ValidationError("user with email exists", 3)




        return data

class LocationSerializer(serializers.ModelSerializer):

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    average_guess_distance = serializers.IntegerField(required=False)
    best_guess_distance = serializers.IntegerField(required=False)
    lat = serializers.DecimalField(max_value=90, min_value=-90, max_digits=15, decimal_places=8)
    lon = serializers.DecimalField(max_value=180, min_value=-180, max_digits=15, decimal_places=8)

    class Meta:
        model = Location
        fields = ('lat', 'lon', 'user', 'average_guess_distance', 'best_guess_distance')


class LocationGuessSerializer(serializers.ModelSerializer):

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    # user = UserSerializer()
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    # location = LocationSerializer()
    lat = serializers.DecimalField(max_value=90, min_value=-90, max_digits=15, decimal_places=8)
    lon = serializers.DecimalField(max_value=180, min_value=-180, max_digits=15, decimal_places=8)

    class Meta:
        model = LocationGuess
        fields = ('user', 'location', 'lat', 'lon')

