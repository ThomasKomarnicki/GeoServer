from geo.views import Location, User, LocationGuess
from django.db.models.aggregates import Count
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from serializers import LocationSerializer, LocationGuessSerializer, UserSerializer
from geo_server import confidential


class GeoTestCases(TestCase):

    def setUp(self):

        # assumes user with id == 2

        set_up_database()

    def test_geo(self):
        # need to be redone for auth tokens
        # self._test_create_user()
        # self._test_location_guess()
        user = User.objects.order_by('?').first()
        # self._test_location_guess({"user": user.id, "location": user.current_location, "lat": 10, "lon": 10})
        # self._test_location_guess({"user": 569549945, "location": user.current_location, "lat": 10, "lon": 10})
        # self._test_location_guess({"user": user.id, "location": 958597597, "lat": 10, "lon": 10})
        # self._test_location_guess({"user": user.id, "location": user.current_location, "lat": 200, "lon": 200})
        # self._test_location_guess({})

        print "done testing location guesses:"
        print LocationGuess.objects.all()

        # need to be refactored for auth tokens
        # self._test_add_location({"user": user.id, "lat": 10, "lon": 10})
        # self._test_add_location({"user": user.id, "lat": 200, "lon": 200})
        # self._test_add_location({})

        self._test_get_location()

        self._test_get_location_guesses(user)

        self._test_get_location_details(Location.objects.order_by('?').first())

        self.test_locations_to_near_locations()

    def _test_create_user(self):
        client = APIClient()

        response = client.post('/users/', {"email": "emailtest1@gmail.com"}, format='json')
        # print response

        self.assertTrue(User.objects.filter(email='emailtest1@gmail.com').exists())

        user = User.objects.filter(email='emailtest1@gmail.com').get()
        self._assert_created_user(user)


        response = client.post('/users/', {"other_identifier": "jklasfklfakdlfeaeoemcvbeg"})

        self.assertTrue(User.objects.filter(other_identifier='jklasfklfakdlfeaeoemcvbeg').exists())

        user = User.objects.filter(other_identifier='jklasfklfakdlfeaeoemcvbeg').get()
        self._assert_created_user(user)

        # self._test_location_guess_for_user()

    def _test_google_auth(self):
        auth_token = confidential.google_auth_token

        client = APIClient()
        request = client.post('user/google_auth/',data={'auth_token':auth_token})

        self.assertEqual(request.status_cod, status.HTTP_200_OK)
        serializer = UserSerializer(data=request.data)
        self.assertTrue(serializer.is_valid(raise_exception=False))

    def _test_location_guess(self, data):
        client = APIClient()

        serializer = LocationGuessSerializer(data=data)
        valid = serializer.is_valid(raise_exception=False)

        if valid:
            user = User.objects.get(id=data['user'])
            last_current_location = user.current_location

        response = client.post('/locationGuess/', data, format='json')

        if valid:
            self.assertTrue(response.status_code, status.HTTP_201_CREATED)
            user = User.objects.get(id=user.id)

            self.assertNotEqual(last_current_location, int(user.current_location))

            self.assertTrue(LocationGuess.objects.filter(user__id=user.id).exists())
            print LocationGuess.objects.all()

        else:
            self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error',response.data)

    def _test_add_location(self, data):
        client = APIClient()

        serializer = LocationSerializer(data=data)
        valid = serializer.is_valid(raise_exception=False)

        if valid:
            user = User.objects.get(id=data['user'])
            user_locations_count = Location.objects.filter(users__id=user.id).count()


        response = client.post('/locations/', data, format='json')

        if valid:
            self.assertTrue(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(Location.objects.filter(users__id=user.id).count() == (user_locations_count + 1))

        else:
            self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)

    def _test_get_location(self):

        request = self.client.get('/locations/'+str(Location.objects.order_by('?').first().id)+"/")
        # print request.status_code

        self.assertTrue(request.status_code == 200)

    def _test_get_location_details(self, location):

        request = self.client.get('/locations/'+str(location.id)+'/details/')
        data = request.data
        # print data
        self.assertEqual(str(location.lat), str(data['place']['lat']))
        self.assertEqual(str(location.lon), str(data['place']['lon']))
        self.assertTrue('location_guesses' in data)

    def _test_get_location_guesses(self, user):
        print "all location guesses:"
        for location_guess in LocationGuess.objects.all():
            print location_guess
        request = self.client.get('/users/'+str(user.id)+'/locationGuesses/')
        print "location guesses for user:"
        print request

    # bypass view create location test
    def _test_location_guess_for_user(self):
        user = User.objects.order_by('?').first()
        # print "test_location_guess_for_user"
        # print user
        last_current_location = user.current_location
        # print "getting current_user_location "+str(user.current_location)
        # print Location.objects.all()
        current_user_location = Location.objects.get(id=user.current_location)

        for i in range(0, 10):
            location_guess = self._create_location_guess(current_user_location, user)
            user.save_location_guess(location_guess)

            location = Location.objects.get(id=user.current_location)
            # print "got new location id = "+str(location.id)
            # print "user:"
            # print user

            self.assertIsNotNone(location)  # valid location returned
            self.assertNotEqual(location.user.id, user.id)  # location is not user's location
            self.assertIn(str(last_current_location)+',', user.guessed_locations) #last_current_location in user guesses
            # self.assertNotIn(str(location.id)+',', user.guessed_locations)  # new location id not already in guessed_locations
            self.assertNotRegexpMatches(user.guessed_locations, r','+str(location.id)+',')

            last_current_location = user.current_location

    def _create_location_guess(self, location, user, index=1):
        location_guess = LocationGuess.objects.create(user=user, location=location, lat=10, lon=10)

        self.assertIsNotNone(location_guess)

        return location_guess

    def _assert_created_user(self, user):
        self.assertTrue(Location.objects.filter(id=user.current_location).exists())
        self.assertTrue(user.email or user.other_identifier)


    def test_locations_to_near_locations(self):
        import views
        user = User.objects.all().first()
        # original_location = Location.objects.create(lat=27.900911, lon=-82.660154)
        data = {'lat':27.900911, 'lon':-82.660154}
        views._save_location(data, user.id)
        original_location = Location.objects.all().reverse().first()
        # original_location.users.add(user)
        # original_location.save()

        users = User.objects.all()
        # data = {'lat':70.00, 'lon':70.00}
        # views._save_location(data, users[3].id)

        data = {'lat':27.901040, 'lon':-82.660318}
        views._save_location(data, users[1].id)
        data = {'lat':27.900767, 'lon':-82.659999}
        views._save_location(data, users[2].id)
        data = {'lat':27.901145, 'lon':-82.660417}
        views._save_location(data, users[3].id)

        data = {'lat': 27.903030, 'lon': -82.662390} # a little more than 100 meters
        views._save_location(data, users[4].id)

        ids_of_users = []
        print "original location id = "+ str(original_location.id)
        self.assertTrue(Location.objects.get(id=original_location.id).users.count() == 4)
        print "number of users for original location = "+ str(Location.objects.get(id=original_location.id).users.count())
        for user in Location.objects.get(id=original_location.id).users.all():
            ids_of_users.append(user.id)

        self.assertTrue(users[1].id in ids_of_users)
        self.assertTrue(users[2].id in ids_of_users)
        self.assertTrue(users[3].id in ids_of_users)

        self.assertTrue(users[4].id not in ids_of_users)

        # test duplicate users aren't added
        data = {'lat':27.901040, 'lon':-82.660318}
        views._save_location(data, users[1].id)
        data = {'lat':27.900767, 'lon':-82.659999}
        views._save_location(data, users[2].id)

        self.assertTrue(Location.objects.get(id=original_location.id).users.count() == 4)

        # similar location was submitted, should be withtin ~ 100 - 500 meters
        # so it should be too close to user[4]'s other location
        data = {'lat': 27.903030, 'lon': -82.662390} # a little more than 100 meters
        response = views._save_location(data, users[4].id)
        self.assertTrue(response.status_code == 400)



def set_up_database():
    count = User.objects.aggregate(count=Count('id'))['count']
    while count < 5:
        user = User.objects.create(email='test'+str(count)+'@gmail.com')
        # print "Creating User with id = "+str(user.id)
        count += 1

    count = Location.objects.aggregate(count=Count('id'))['count']

    while count < 50:
        # print "creating Location "+str(count)
        location = Location.objects.create(lat=count, lon=count)
        location.users.add(User.objects.order_by('?').first())
        count += 1
