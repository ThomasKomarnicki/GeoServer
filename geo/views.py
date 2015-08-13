from models import Location, LocationGuess, User
from geo.serializers import UserSerializer, LocationSerializer, LocationGuessSerializer
from django.http import HttpResponse
from rest_framework import viewsets

from rest_framework.response import Response
from rest_framework import mixins, status
from rest_framework.decorators import *
from oauth2client import client, crypt
from django.db.models import Avg, Min
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone



class LocationViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    serializer_class = LocationSerializer
    queryset = Location.objects.all()

    def create(self, request):

        if 'user' in request.data:
            user_id = request.data['user']
            del request.data['user']
        else:
            return Response(data={"error": "invalid data"}, status=400)
        serializer = self.get_serializer(data=request.data)

        # if not all required fields are in the data return an error
        if not all(name in serializer.initial_data for name in ['user', 'lat', 'lon']):
            return Response(data={"error": "invalid data"}, status=400)

        # user_id = serializer.initial_data['user']

        auth_token = request.query_params.get('auth_token', None)
        if not _is_valid_auth_token(auth_token, user_id):
            return Response(status=403)

        if not User.objects.filter(id=user_id).exists():
            return Response(data={"error": "not a valid user"}, status=400)

        if not serializer.is_valid():
            return Response(data={"error": "invalid data"}, status=400)

        return _save_location(request.data,user_id)

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

        # if not all required fields are in the data return an error
        if not all(name in serializer.initial_data for name in ['user', 'location', 'lat', 'lon']):
            return Response(data={"error": "invalid data"}, status=400)


        user_id = serializer.initial_data['user']
        auth_token = request.query_params.get('auth_token', None)
        if not _is_valid_auth_token(auth_token,user_id):
            return Response(status=403)

        location_id = serializer.initial_data['location']

        # if not user_id:
        #     return Response(data={"error": "user id not supplied"},status=400)
        if not User.objects.filter(id=user_id).exists():
            return Response(data={"error": "not a valid user"}, status=400)

        # if not location_id:
        #     return Response(data={"error": "location id not supplied"}, status=400)
        if not Location.objects.filter(id=location_id).exists():
            return Response(data={"error": "not a valid location"}, status=400)

        if not serializer.is_valid():
            return Response(data={"error": "invalid data"}, status=400)

        location_guess = serializer.save()

        user = User.objects.get(id=user_id)
        user.save_location_guess(location_guess)
        location_serializer = LocationSerializer(Location.objects.get(id=user.current_location))
        try:
            return Response(location_serializer.data, status=status.HTTP_201_CREATED)
        except:
            return HttpResponse(status=404)


class UserViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        data = request.data

        # right now only takes in other_identifier
        if 'other_identifier' in data:
            if not _is_valid_identifier(data['other_identifier']):
                return HttpResponse(status=400, content={"error": "invalid identifier"})

            if User.objects.filter(other_identifier=data['other_identifier']).exists():
                print "user with identifier exists, returning that user"
                user = User.objects.get(other_identifier=data['other_identifier']);
                user.save()
                serializer = UserSerializer(user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                user = User(other_identifier=data['other_identifier'])
                user.save()
                serializer = UserSerializer(user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
             return HttpResponse(status=400, content={"error": "no identifier"})

    def google_auth(self, request):
        data = request.data

        if 'auth_token' not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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
            user.save()
        else:
            serializer = self.get_serializer(data={'google_auth_id': userid, 'email': idinfo['email']})
            serializer.is_valid()
            user = serializer.save()

        serializer = UserSerializer(user)
        return Response(serializer.data,status=200)


    #using POST to /locationGuess/ instead
    @detail_route(methods=['post'], url_path='guess')
    def guess(self, request, pk=None):
        auth_token = request.query_params.get('auth_token', None)

        serializer = LocationGuessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not _is_valid_auth_token(auth_token, pk):
            return Response(data=403)

        serializer.save()

        location = Location.get_new_location(pk)
        location_serializer = LocationSerializer(location)
        return Response(data=location_serializer.data, status=200)

    @detail_route(methods=['get'], url_path='locationGuesses')
    def locationGuesses(self, request,  pk=None):
        page = request.query_params.get('page',None)
        location_guesses = LocationGuess.objects.filter(user__id=pk).reverse().all()
        try:
            paginator = Paginator(location_guesses,20)
            location_guesses = paginator.page(page)
        except PageNotAnInteger:
            return Response({'error':'page is not an integer'},status=400)
        except EmptyPage:
            return Response([],status=200)
        serializer = LocationGuessSerializer(location_guesses, many=True)

        return Response(serializer.data, status=200)

    @detail_route(methods=['get'], url_path='locations')
    def locations(self, request,  pk=None):
        locations = Location.objects.filter(user__id=pk).reverse().all()
        page = request.query_params.get('page',None)
        try:
            paginator = Paginator(locations,20)
            locations = paginator.page(page)
        except PageNotAnInteger:
            return Response({'error':'page is not an integer'},status=400)
        except EmptyPage:
            return Response([],status=200)

        serializer = LocationSerializer(locations, many=True)

        return Response(serializer.data, status=200)

def _is_valid_identifier(identifier):
    try:
        int(identifier,16)
    except ValueError:
        return False

    return True


def _is_valid_auth_token(auth_token,user_id):
    try:
        user = User.objects.get(id=user_id)
        return user.auth_token == auth_token
    except:
        return False


def _save_location(request_data, user_id):
    request_data['date_added'] = timezone.now()
    serializer = LocationSerializer(data=request_data)
    if not serializer.is_valid():
        print "location not valid"
        return Response({'error':'location not valid'},status=400)

    lat = float(request_data['lat'])
    lon = float(request_data['lon'])
    close_locations = Location.objects.filter(lat__range=(lat-.001,lat+.001)).filter(lon__range=(lon-.001,lon+0.001)).all()
    close_location = _find_closest_location(close_locations,lat,lon)
    if close_location:
        print "close location found"
        close_location.users.add(User.objects.get(id=user_id))
        print "adding user " + str(user_id) + " to location " +str(close_location.id)
        close_location.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # only add location if not too close to any other locations
    print "not close location"
    location = serializer.save()
    location.users.add(User.objects.get(id=user_id))
    location.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)



def _find_closest_location(close_locations, lat, lon):
    closest = None
    closest_diff = 1

    if close_locations.count() == 0:
        return None

    for location in close_locations:
        diff = (lat - float(location.lat)) + (lon - float(location.lon))
        if diff < closest_diff:
            closest = location
            closest_diff = diff

    return closest
