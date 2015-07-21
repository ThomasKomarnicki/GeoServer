from models import Location, LocationGuess, User
from geo.serializers import UserSerializer, LocationSerializer, LocationGuessSerializer
from django.http import HttpResponse
from rest_framework import viewsets

from rest_framework.response import Response
from rest_framework import mixins, status
from rest_framework.decorators import *
from rest_framework import serializers
from oauth2client import client, crypt
from django.db.models import Avg, Min


class LocationViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    serializer_class = LocationSerializer
    queryset = Location.objects.all()

    # def get_queryset(self):
    #     queryset = Location.objects.all()
    #     location_id = self.request.query_params.get('id', None)
    #     if location_id is not None:
    #         queryset = queryset.filter(id=location_id)
    #     return queryset

    def create(self, request):

        serializer = self.get_serializer(data=request.data)

        # if not all required fields are in the data return an error
        if not all(name in serializer.initial_data for name in ['user', 'lat', 'lon']):
            return Response(data={"error": "invalid data"}, status=400)

        user_id = serializer.initial_data['user']

        if not User.objects.filter(id=user_id).exists():
            return Response(data={"error": "not a valid user"}, status=400)

        if not serializer.is_valid():
            return Response(data={"error": "invalid data"}, status=400)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # return all location guesses for location
    @detail_route(methods=['get'], url_path='details')
    def get_location_details(self, request, pk):

        if not Location.objects.filter(id=pk).exists():
            return Response({"error": "location doesn't exist"},status=404);

        location = Location.objects.get(id=pk)
        serializer = LocationSerializer(location)

        data = {'place': serializer.data}
        location_guesses = LocationGuess.objects.filter(location=location.id).all()
        guesses_serializer = LocationGuessSerializer(location_guesses, many=True)
        data['location_guesses'] = guesses_serializer.data

        distance_min = location_guesses.aggregate(Min('distance'))['distance__min']
        if not distance_min:
            distance_min = 0;
        data['best_distance'] = distance_min

        avg = location_guesses.aggregate(Avg('distance'))['distance__avg']
        if not avg:
            avg = 0
        data['average_distance'] = avg

        return Response(data, status=200);


class LocationGuessViewSet(mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           viewsets.GenericViewSet):

    queryset = LocationGuess.objects.all()
    serializer_class = LocationGuessSerializer

    def create(self, request):

        serializer = self.get_serializer(data=request.data)

        # print serializer

        # if not all required fields are in the data return an error
        if not all(name in serializer.initial_data for name in ['user', 'location', 'lat', 'lon']):
            return Response(data={"error": "invalid data"}, status=400)


        # print 1
        user_id = serializer.initial_data['user']
        location_id = serializer.initial_data['location']

        # print 2
        # if not user_id:
        #     return Response(data={"error": "user id not supplied"},status=400)
        if not User.objects.filter(id=user_id).exists():
            return Response(data={"error": "not a valid user"}, status=400)

        # if not location_id:
        #     return Response(data={"error": "location id not supplied"}, status=400)
        if not Location.objects.filter(id=location_id).exists():
            return Response(data={"error": "not a valid location"}, status=400)

        # print 3

        # print serializer.initial_data

        if not serializer.is_valid():
            return Response(data={"error": "invalid data"}, status=400)

        # print 4
        location_guess = serializer.save()

        # print "saving location guess"

        user = User.objects.get(id=user_id)
        user.save_location_guess(location_guess)
        location_serializer = LocationSerializer(Location.objects.get(id=user.current_location))
        try:
            # print "location being returned:"
            # print location_serializer
            return Response(location_serializer.data, status=status.HTTP_201_CREATED)
        except:
            return HttpResponse(status=404)


class UserViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        print "creating user"
        serializer = self.get_serializer(data=request.data)
        print "created serializer"
        try:
            print "serializer is valid = "+str(serializer.is_valid())
        except serializers.ValidationError as e:
            return HttpResponse(status=400, content="{error:}"+e.message)

        print "saving user"
        # response = mixins.CreateModelMixin.create(self, request)

        # print serializer

        serializer.save()

        response = Response(serializer.data, status=status.HTTP_201_CREATED)
        return response

    def google_auth(self, request):
        data = request.data

        if 'auth_token' not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # url = 'https://www.googleapis.com/oauth2/v3/tokeninfo?id_token='+str(data['auth_token'])
        # serialized_data = urllib2.urlopen(url).read()
        #
        # data = json.loads(serialized_data)
        # print data

        try:
            idinfo = client.verify_id_token(data['auth_token'], '92340928633-a2lv6k929j34994pjcfmpdm9a8kc9lme.apps.googleusercontent.com')
            # If multiple clients access the backend server:
            # if idinfo['aud'] not in [ANDROID_CLIENT_ID, IOS_CLIENT_ID, WEB_CLIENT_ID]:
            #     raise crypt.AppIdentityError("Unrecognized client.")
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise crypt.AppIdentityError("Wrong issuer.")
            # if idinfo['hd'] != APPS_DOMAIN_NAME:
            #     raise crypt.AppIdentityError("Wrong hosted domain.")
        except crypt.AppIdentityError as e:
            print e
            # Invalid token
        userid = idinfo['sub']

        if User.objects.filter(google_auth_id=userid).exists():
            user = User.objects.filter(google_auth_id=userid).get()
        else:
            serializer = self.get_serializer(data={'google_auth_id': userid, 'email': idinfo['email']})
            serializer.is_valid()
            user = serializer.save()

        serializer = UserSerializer(user)
        return Response(serializer.data,status=200)


    @detail_route(methods=['post'], url_path='guess')
    def guess(self, request, pk=None):
        serializer = LocationGuessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        location = Location.get_new_location(pk)
        location_serializer = LocationSerializer(location)
        return Response(data=location_serializer.data, status=200)

    @detail_route(methods=['get'], url_path='locationGuesses')
    def guess(self, request,  pk=None):
        location_guesses = LocationGuess.objects.filter(user__id=pk).all()
        serializer = LocationGuessSerializer(location_guesses, many=True)

        return Response(serializer.data, status=200)

    @detail_route(methods=['get'], url_path='locations')
    def guess(self, request,  pk=None):
        locations = Location.objects.filter(user__id=pk).all()
        serializer = LocationSerializer(locations, many=True)

        return Response(serializer.data, status=200)
