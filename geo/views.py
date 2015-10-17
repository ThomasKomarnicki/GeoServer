from models import Location, LocationGuess, User, EARTH_CIRCUMFERENCE
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
from geopy.distance import vincenty
from rest_framework.serializers import ValidationError

LAT_LNG_DIF = 0.01  # ~1110 meters at the equator



class LocationViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    serializer_class = LocationSerializer
    queryset = Location.objects.all()

    def create(self, request):

        if 'user' in request.data:
            user_id = request.data['user']
            del request.data['user']
        else:
            return Response(data={"error": "user not in data field"}, status=400)
        serializer = self.get_serializer(data=request.data)

        # if not all required fields are in the data return an error
        if not all(name in serializer.initial_data for name in ['lat', 'lon']):
            return Response(data={"error": "lat lon not in data"}, status=400)

        # user_id = serializer.initial_data['user']

        auth_token = request.query_params.get('auth_token', None)
        if not _is_valid_auth_token(auth_token, user_id):
            return Response(status=403)

        if not User.objects.filter(id=user_id).exists():
            return Response(data={"error": "not a valid user"}, status=400)

        # if not serializer.is_valid():
        #     return Response(data={"error": "serializer didn't validate"}, status=400)
        # serializer.date_added = timezone.now()
        # if not serializer.is_valid():
        #     return Response(data={"error": "invalid data"}, status=400)
        return _save_location(request.data, user_id)

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


def _save_location(request_data, user_id):
    # request_data['date_added'] = timezone.now() # added as default in serializer
    serializer = LocationSerializer(data=request_data)
    if not serializer.is_valid():
        print "location not valid"
        return Response({'error':'location not valid'},status=400)

    lat = float(request_data['lat'])
    lon = float(request_data['lon'])
    # filter by range of +- LAT_LNG_DIF
    close_locations = Location.objects.filter(lat__range=(lat-LAT_LNG_DIF,lat+LAT_LNG_DIF))\
        .filter(lon__range=(lon-LAT_LNG_DIF, lon+LAT_LNG_DIF)).all()

    # keep locations that are less than 100 meters away
    close_locations_list = []
    for location in close_locations:
        distance = vincenty((float(location.lat),float(location.lon)),(lat,lon)).meters
        # print "location "+str(location) + " is " + str(distance) + " meters from the new location " + str(lat) + ", " + str(lon)
        if distance < 100:
            close_locations_list.append(location)
        elif distance < 500 and location.id == user_id:
            #don't add similar location for user
            return Response({'error':'location is too close to another location'},status=400)

    # close_locations_list = [location for location in close_locations if not vincenty((float(location.lat),float(location.lon)),(lat,lon)).meters < 100]

    close_location = _find_closest_location(close_locations_list,lat,lon)
    if close_location:
        # print "close location found"
        close_location.users.add(User.objects.get(id=user_id))
        # print "adding user " + str(user_id) + " to location " +str(close_location.id)
        close_location.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # only add location if not too close to any other locations
    # print "not close location"
    location = serializer.save()
    location.users.add(User.objects.get(id=user_id))
    location.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)



def _find_closest_location(close_locations, lat, lon):
    closest = None
    closest_diff = 1

    if len(close_locations) == 0:
        return None

    for location in close_locations:
        diff = (lat - float(location.lat)) + (lon - float(location.lon))
        if diff < closest_diff:
            closest = location
            closest_diff = diff

    return closest


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

        response_data = {'new_location': location_serializer.data, 'location_guess_result':serializer.data}
        try:
            return Response(response_data, status=status.HTTP_201_CREATED)
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

    def retrieve(self, request, pk):
        user_id = pk
        auth_token = request.query_params.get('auth_token', None)
        if not _is_valid_auth_token(auth_token,user_id):
            return Response(status=403)

        user = User.objects.get(id=pk);
        serializer = UserSerializer(user)

        data = serializer.data
        del data['auth_token']
        del data['email']
        del data['other_identifier']

        return Response(data, status=status.HTTP_200_OK)



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
            # try:
            serializer.is_valid(raise_exception=True)
            # except ValidationError as e:
            #     print e

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
    def location_guesses(self, request,  pk=None):
        page = request.query_params.get('page',None)
        location_guesses = LocationGuess.objects.filter(user__id=pk).order_by('id').reverse()
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
        try:
            user = User.objects.get(id=pk)
        except:
            return Response({'error':'no user with id '+str(pk)},status=400)
        locations = Location.objects.filter(users=user).order_by('id').reverse()
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

    @detail_route(methods=['get'], url_path='profile_stats')
    def profile_stats(self, request, pk=None):
        if not User.objects.filter(id=pk).exists():
            return Response({'error': 'user does not exist'}, status=400)

        auth_token = request.query_params.get('auth_token', None)
        if not _is_valid_auth_token(auth_token, pk):
            return Response(data=403)

        user = User.objects.get(id=pk)
        # best guess
        best_guess = -1
        best_guess_location = None
        for location_guess in LocationGuess.objects.filter(user_id=user.id).all():
            if location_guess.distance < best_guess or best_guess == -1:
                best_guess = location_guess.distance
                best_guess_location = location_guess
        # best_guess = LocationGuess.objects.filter(user_id=user.id).aggregate(Min('distance'))
        # best_guess = best_guess['distance__min']


        # hardest location to guess, highest average distances
        users_locations = Location.objects.filter(users__id=user.id)

        # print LocationGuess.objects.all()

        hardest_location = None
        hardest_location_distance = 0
        for location in users_locations:
            # if not hardest_location:
            #     hardest_location = location
            # else:
            avg = LocationGuess.objects.filter(location=location.id).aggregate(Avg('distance'))['distance__avg']
            print "hard location avg: " + str(avg)
            if avg and avg > hardest_location_distance:
                hardest_location = location
                hardest_location_distance = avg


        # easiest location to guess, lowest average distances
        easiest_location = None
        easiest_location_distance = EARTH_CIRCUMFERENCE
        for location in users_locations:
            # if not easiest_location:
            #     easiest_location = location
            # else:
            avg = LocationGuess.objects.filter(location=location.id).aggregate(Avg('distance'))['distance__avg']
            print "easy location avg: " + str(avg)
            if avg and avg < easiest_location_distance:
                easiest_location = location
                easiest_location_distance = avg
        if easiest_location_distance == EARTH_CIRCUMFERENCE:
            easiest_location_distance = -1

        # level
        level = user.get_progression_level()
        # total number of location guesses
        location_guess_number = LocationGuess.objects.filter(user_id=user.id).count()
        # total number of locations
        locations_number = Location.objects.filter(users__id=user.id).count()

        if hardest_location:
            hardest_location = LocationSerializer(hardest_location).data
        if easiest_location:
            easiest_location = LocationSerializer(easiest_location).data
        if best_guess_location:
            best_guess_location = LocationSerializer(Location.objects.get(id=best_guess_location.location.id)).data
        data = {
            'best_guess': best_guess,
            'best_guess_location': best_guess_location,
            'hardest_location': hardest_location,
            'hardest_location_avg': hardest_location_distance,
            'easiest_location': easiest_location,
            'easiest_location_avg': easiest_location_distance,
            'level': level,
            'location_guess_count': location_guess_number,
            'location_count': locations_number
        }
        print data
        print "\n\n"
        return Response(data, status=200)

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


@api_view(['GET'])
def slideshow_info(request):
    data = {
        'url_prefix': '/static/slide_show_images/',
        'portrait_images': [
            '1221.png',
            '1448.png',
            '1852.png',
            '1934.png',
            '2321.png',
            '5302.png',
            '6056.png',
            '7005.png',
            '7007.png',
        ],
        'landscape_images': [
            '1221_land.png',
            '1448_land.png',
            '1852_land.png',
            '1934_land.png',
            '2321_land.png',
            '5302_land.png',
            '6056_land.png',
            '7005_land.png',
            '7007_land.png',
        ],

    }

    return Response(data, status=200)
