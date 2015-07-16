from models import Location, LocationGuess, User
from geo.serializers import UserSerializer, LocationSerializer, LocationGuessSerializer
from django.http import HttpResponse
from rest_framework import viewsets

from rest_framework.response import Response
from rest_framework import mixins, status
from rest_framework.decorators import *
from rest_framework import serializers


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
        if not Location.objects.filter(id=user_id).exists():
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
        serializer = self.get_serializer(location_guesses,many=True)
        # print serializer

        return Response(serializer.data, status=200)
