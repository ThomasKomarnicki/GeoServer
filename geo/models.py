from django.db import models
from random import randint
import hashlib
import math
from geopy.distance import vincenty

EARTH_CIRCUMFERENCE = 40.075 * 1000000
DISTANCE_RANGES = [78271.484375, 156542.96875, 313085.9375, 626171.875, 1252343.75, 2504687.5, 5009375.0, 10018750.0, 20037500.0]


class User(models.Model):
    email = models.EmailField(null=True)
    other_identifier = models.CharField(max_length=50, null=True)
    google_auth_id = models.CharField(max_length=50,null=True, blank=True)
    current_location = models.IntegerField()
    guessed_locations = models.CommaSeparatedIntegerField(max_length=64000, null=True, blank=True)
    auth_token = models.CharField(max_length=256)
    total_score = models.IntegerField(default=0) # representative of progression / level

    def __unicode__(self):

        return 'id: '+str(self.id)+', email: '+str(self.email)

    def get_next_location(self):
        # TODO
        already_guessed_locations = str(self.guessed_locations).split(',')
        return self._get_random_location(already_guessed_locations)

    def _get_random_location(self, already_guessed_locations):
        possible_locations = Location.objects.exclude(users__id=self.id)
        already_guessed_locations = already_guessed_locations[:-1]
        # print already_guessed_locations
        if 'None' not in already_guessed_locations:
            for guessed_location_id in already_guessed_locations:
                # if guessed_location_id is not None and guessed_location_id is not 'None':
                # print "excluding "+str(guessed_location_id)
                possible_locations = possible_locations.exclude(id=guessed_location_id)

        # possible_locations = possible_locations.all()
        # print "get_random_locations: possible locations"
        # string = ""
        # for possible_location in possible_locations:
        #     string += str(possible_location.id)+","
        # print string

        count = possible_locations.count()
        if count == 0:
            possible_locations = Location.objects.exclude(users__id=self.id) # user guessed all possible locations
            count = possible_locations.count()

        random_index = randint(0, count - 1)

        return possible_locations[random_index]

    '''
        scores are between 0 - 100
    '''
    def get_progression_level(self):
        return int(self.total_score / 100)

        # count = Location.objects.all().count()
        # random_index = randint(0, count - 1)


        # if str(random_index) in already_guessed_locations: # TODO needs testing
        #     return self._get_random_location(already_guessed_locations)
        # return Location.objects.all()[random_index]


    def save_location_guess(self, location_guess):
        location_guess.save()
        if not self.guessed_locations:
            self.guessed_locations = str(self.current_location) + ','
        else:
            self.guessed_locations += str(self.current_location) + ','
        self.current_location = self.get_next_location().id
        self.total_score += location_guess.score
        self.save()

    def save(self, **kwargs):
        if self.email:
            self.other_identifier = None
        if self.other_identifier:
            self.email = None

        if Location.objects.all().count() == 0:
            self.current_location = 2
        elif not self.current_location:
            self.current_location = self.get_next_location().id

        hash_object = str(self.email) + str(self.other_identifier)
        self.auth_token = hashlib.sha256(hash_object).hexdigest()

        # if self.guessed_locations:
        #     self.guessed_locations += str(self.current_location) + ','
        # else:
        #     self.guessed_locations = str(self.current_location) + ','

        super(User, self).save(**kwargs)
    

class Location(models.Model):
    # user = models.ForeignKey(User, null=True)
    users = models.ManyToManyField(User)
    lat = models.DecimalField(max_digits=20, decimal_places=17)
    lon = models.DecimalField(max_digits=20, decimal_places=17)
    date_added = models.DateTimeField(auto_now=True)
    # average_guess_distance = models.IntegerField(default=0)
    # best_guess_distance = models.IntegerField(default=0)

    def __unicode__(self):
        return "\"location\":{\"id\":"+str(self.id)+"\"lat\":"+str(self.lat)+", \"lon\":"+str(+self.lon)+"}"

    # @staticmethod
    # def get_new_location(user_id):
    #     user = User.objects.query(id=user_id).get()
    #     location = Location.get_next_location(user)
    #     user.current_location = location.id
    #     return location

    def update_location(self, location_guess):
        if location_guess.distance > self.best_guess_distance:
            self.best_guess_distance = location_guess.distance

        total = 0
        location_guesses = LocationGuess.objects.filter(location=self).all()

        for location_guess in location_guesses:
            total = total + location_guess.distance

        count = location_guesses.count()
        if count == 0:
            count = 1

        self.average_guess_distance = total / count


class LocationGuess(models.Model):
    user = models.ForeignKey(User, null=True)
    location = models.ForeignKey(Location)
    # guess lat and lon
    lat = models.DecimalField(max_digits=20, decimal_places=17)
    lon = models.DecimalField(max_digits=20, decimal_places=17)
    score = models.IntegerField()
    distance = models.IntegerField()

    def __unicode__(self):
        return "user: "+str(self.user.id)+", location = "+str(self.location.id)\
               + "lat lon =" + str(self.lat) + " " + str(self.lon)

    def save(self,**kwargs):
        if not self.distance:
            self.distance = vincenty((float(self.location.lat),float(self.location.lon)),(float(self.lat),float(self.lon))).meters
        # TODO determine score
        self.score = determine_score(self.distance)

        super(LocationGuess, self).save(**kwargs)
        # TODO calculate distance between location and location guess lat lon


def determine_score(distance):
    if distance > EARTH_CIRCUMFERENCE / 2:
        return 1  # this should be an error

    distance_ranges = []
    range_count = 10
    for x in range(1, range_count):
        distance_ranges.append(EARTH_CIRCUMFERENCE / math.pow(2,x))

    distance_ranges.reverse()

    # print distance_ranges

    score_range_index = 0

    for i, distance_max in enumerate(distance_ranges):
        if distance < distance_max:
            score_range_index = i
            break

    # print "score_range_index: "+str(score_range_index)

    score_base = ((range_count-1) - score_range_index) * 10
    lower_bound = 0
    if score_range_index != 0:
        lower_bound = distance_ranges[score_range_index - 1]

    dist_range_diff = distance_ranges[score_range_index] - lower_bound
    # print "dist_range_diff: " + str(dist_range_diff)
    dist_score_diff = distance - lower_bound
    # print "dist_score_diff: "+ str(dist_score_diff)

    percent_of_range = 1 - (dist_score_diff / dist_range_diff)
    # print "percent_of_range: "+str(percent_of_range)

    return math.ceil((score_base + (percent_of_range * float(10))) * (float(10)/float(range_count)))



    # def __unicode__(self):
    #     return self.location+", \"location_guess\":{\"lat\":"+self.lat+", \"lon\":"+self.lon+"}"