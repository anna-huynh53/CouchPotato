from django.shortcuts import render
from .forms import SearchForm
from django.http import HttpResponseRedirect, HttpResponseNotFound
import json
import requests
from .models import Profile, Genre, Movie
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
import random


watchedList = []
toWatchList = []
listArray = [watchedList, toWatchList]

# Home page
def home(request):
    if request.session.get('loggedIn'):
        updateLists(request)
        print("===")
        #print("ITEM: "+ listArray[0][0].title)

    if request.method == 'POST':
        if 'logout' in request.POST:
            request.session['loggedIn'] = False
            logout(request)
            return render(request, '../templates/home.html', {"loggedIn": False, "lists": listArray})
        elif 'email' and 'username' in request.POST:
            try:
                user = User.objects.create_user(username=request.POST['username'], email=request.POST['email'],
                                                password=request.POST['password'])
                user.save()
                login(request, user)  # login
                print("Created account")  # debug print
                profile = user.profile
                request.session['username'] = user.username
                request.session['loggedIn'] = True
                request.session['email'] = user.email
                updateLists(request)
                return render(request, '../templates/home.html',
                              {"addStatus": "Account successfully created", "loggedIn": True, "lists": listArray})
            except IntegrityError as e:
                if 'UNIQUE contraint' in e.message:
                    print("Email/username already in use")
                    return render(request, '../templates/home.html', {"loggedIn": False, "lists": listArray})

        elif 'username_LI' and 'password_LI' in request.POST:
            user = authenticate(username=request.POST['username_LI'], password=request.POST['password_LI'])

            if user is None:
                print("Incorrect password");
                return render(request, '../templates/home.html', {"addStatus": "Incorrect password", "loggedIn": False, "lists": listArray})
            else:
                login(request, user)
                request.session['username'] = user.username
                request.session['email'] = user.email
                request.session['loggedIn'] = True
                updateLists(request)
                return render(request, '../templates/home.html', {"loggedIn": True, "lists": listArray})

        elif 'user' in request.POST:
            try:
                userAdded = User.objects.get(email=request.POST['user'])
                userAdded.save()
                try:
                    user = User.objects.get(email=request.session['email'])
                    user.save()
                    user.profile.friends.add(userAdded)
                    user.save()
                    if request.session['loggedIn']:
                        updateLists(request)
                    return render(request, '../templates/home.html',
                                  {"addStatus": "User Added!", "loggedIn": request.session['loggedIn'], "lists": listArray})
                except:
                    print("Some other error")
                    if request.session['loggedIn']:
                        updateLists(request)
                    return render(request, '../templates/home.html',
                                  {"addStatus": "Error", "loggedIn": request.session['loggedIn'], "lists": listArray})
            except:
                print("actual user does not exist")
                if request.session['loggedIn']:
                    updateLists(request)
                return render(request, '../templates/home.html',
                              {"addStatus": 'User Doesnt Exist!', "loggedIn": request.session['loggedIn'], "lists": listArray})

        else:
            form = SearchForm(request.POST)
            if form.is_valid():
                return HttpResponseRedirect('/results')

    else:  # GET method
        if request.session.get('loggedIn'):
            updateLists(request)
            content = request.session['email']
            user = User.objects.get(email=request.session.get('email'))
            user.save()
            watched = user.profile.watchedList.all()
            toWatch = user.profile.toWatchList.all()
            return render(request, '../templates/home.html',
                          {"addStatus": "Email", "watched": watched, "toWatch": toWatch,
                           "loggedIn": request.session['loggedIn'], "lists": listArray})
        else:
            content = 'Search'
            return render(request, '../templates/home.html', {"addStatus": "Email", "loggedIn": False, "lists": listArray})

    return render(request, '../templates/home.html', {"loggedIn": False, "lists": listArray})


# Personal lists (if this is still it's own page I'm not sure)
def lists(request):
    if request.session.get('loggedIn'):
        updateLists(request)
    if request.session.get('loggedIn'):
        currentUser = User.objects.get(email=request.session.get('email'))
        return render(request, '../templates/lists.html', {"currentUserRecord": currentUser, "bodyContent": "My List"})

        return render(request, '../templates/lists.html', {"bodyContent": "Error: Not logged in"})


# Search results
def results(request):
    if request.session.get('loggedIn'):
        updateLists(request)
    synced = False
    # If this is a search
    if request.method == 'POST':

        if 'movie' in request.POST:
            # if the user has clicked "add to my watched list"
            movie = request.POST.get("movie")
        # newMovie = Movie(title=movie.title, year=movie.year, imdbID=movie.imdbID)
        # newMovie.save()
        #
        # user = User.objects.get(email=request.session.get('email'))
        # user.watchedList.add(movie)
        # user.save()
        else:
            movie_query = request.POST.get('search')  # gets query from POST data

        # Search movie by Genre
        if False:  # With current way drop down menu is working, can find a way to find out which item is selected

            # Sync genres if haven't yet
            test = Genre.objects.all()  # check to see if db synced with Genres
            if not test:
                sync_genres()

            # Deal with search now
            movie_query = str(movie_query).lower().capitalize().rstrip()

            try:
                genre = Genre.objects.get(name=movie_query)
                url = "https://api.themoviedb.org/3/discover/movie?api_key=cc4b67c52acb514bdf4931f" \
                      "7cedfd12b&language=en-US&with_genres=" + genre.tmdbID
            except:
                url = "https://api.themoviedb.org/3/discover/movie?api_key=cc4b67c52acb514bdf4931" \
                      "f7cedfd12b&language=en-US&with_genres=0"

                payload = "{}"
                headers = {'content-type': 'application/json'}

                response = requests.request("GET", url, data=payload, headers=headers)
                content = json.loads(response.text)
                raw_items = content["results"]

                class Movie:
                    def __init__(self, title, year, ID, poster):
                        self.title = title
                        self.year = year
                        self.tmdbID = ID
                        self.poster = poster

                        movies = []

                        for item in raw_items:
                            movies.append(Movie(item['title'], item['release_date'], item['id'], item['poster_path']))

                            return render(request, '../templates/movieResults_genre.html',
                                          {"query": movies, "searchTyped": movie_query})

                            # search by movie title
    else:
        url = 'http://www.omdbapi.com/?s=' + movie_query
        response = requests.get(url)
        content = json.loads(response.text)
        raw_items = content["Search"]

        class Movie:
            def __init__(self, title, year, ID, poster):
                self.title = title
                self.year = year
                self.imdbID = ID
                self.poster = poster

                movies = []

            # TODO make item some kind of object which includes imdbID so when clicked, it can link to more detailed info
            for item in raw_items:
                movies.append(Movie(item["Title"], item["Year"], item["imdbID"], item["Poster"]))

        # TODO rename query
        return render(request, '../templates/movieResults.html', {"query": movies, "searchTyped": movie_query})


# Personal lists (if this is still it's own page I'm not sure)
def lists(request):
    if request.session.get('loggedIn'):
        currentUser = User.objects.get(email=request.session.get('email'))
        return render(request, '../templates/lists.html', {"currentUserRecord": currentUser, "bodyContent": "My List"})

    return render(request, '../templates/lists.html', {"bodyContent": "Error: Not logged in"})


# Search results
def results(request):
    if request.session.get('loggedIn'):
        updateLists(request)
    synced = False
    # If this is a search
    if request.method == 'POST':

        if 'movie' in request.POST:
            # if the user has clicked "add to my watched list"
            movie = request.POST.get("movie")
            # newMovie = Movie(title=movie.title, year=movie.year, imdbID=movie.imdbID)
            # newMovie.save()
            #
            # user = User.objects.get(email=request.session.get('email'))
            # user.watchedList.add(movie)
            # user.save()
        else:
            movie_query = request.POST.get('search')  # gets query from POST data

        # Search movie by Genre
        if False:  # With current way drop down menu is working, can find a way to find out which item is selected

            # Sync genres if haven't yet
            test = Genre.objects.all()  # check to see if db synced with Genres
            if not test:
                sync_genres()

            # Deal with search now
            movie_query = str(movie_query).lower().capitalize().rstrip()

            try:
                genre = Genre.objects.get(name=movie_query)
                url = "https://api.themoviedb.org/3/discover/movie?api_key=cc4b67c52acb514bdf4931f" \
                      "7cedfd12b&language=en-US&with_genres=" + genre.tmdbID
            except:
                url = "https://api.themoviedb.org/3/discover/movie?api_key=cc4b67c52acb514bdf4931" \
                      "f7cedfd12b&language=en-US&with_genres=0"

            payload = "{}"
            headers = {'content-type': 'application/json'}

            response = requests.request("GET", url, data=payload, headers=headers)
            content = json.loads(response.text)
            raw_items = content["results"]

            class Movie:
                def __init__(self, title, year, ID, poster):
                    self.title = title
                    self.year = year
                    self.tmdbID = ID
                    self.poster = poster

            movies = []

            for item in raw_items:
                movies.append(Movie(item['title'], item['release_date'], item['id'], item['poster_path']))

            return render(request, '../templates/movieResults_genre.html',
                          {"query": movies, "searchTyped": movie_query, "lists": listArray})

        # search by movie title
        else:
            url = 'http://www.omdbapi.com/?s=' + movie_query
            response = requests.get(url)
            content = json.loads(response.text)
            raw_items = content["Search"]

            class Movie:
                def __init__(self, title, year, ID, poster):
                    self.title = title
                    self.year = year
                    self.imdbID = ID
                    self.poster = poster

            movies = []

            # TODO make item some kind of object which includes imdbID so when clicked, it can link to more detailed info
            for item in raw_items:
                movies.append(Movie(item["Title"], item["Year"], item["imdbID"], item["Poster"]))

        # TODO rename query
        return render(request, '../templates/movieResults.html', {"query": movies, "searchTyped": movie_query, "lists": listArray})


def movie(request):
    if request.session.get('loggedIn'):
        updateLists(request)

    if request.method == 'GET':
        url = 'http://www.omdbapi.com/?i=' + request.GET["id"] + "&plot=full&r=json"
        response = requests.get(url)
        content = json.loads(response.text)

        class FullMovie:
            def __init__(self, content):
                # there is almost certainly a less retarded way of doing this
                self.imdbID = content["imdbID"]
                self.title = content["Title"]
                self.year = content["Year"]
                self.rated = content["Rated"]
                self.released = content["Released"]
                self.runtime = content["Runtime"]
                self.genre = content["Genre"]
                self.director = content["Director"]
                self.writer = content["Writer"]
                self.actors = content["Actors"]
                self.plot = content["Plot"]
                self.language = content["Language"]
                self.country = content["Country"]
                self.poster = content["Poster"]
                self.metascore = content["Metascore"]
                self.imdbRating = content["imdbRating"]
                self.response = content["Response"]

        movieDict = FullMovie(content)

        try:
            movie = Movie.objects.get(imdbID=request.POST['movie'])
        except:

            newMovieRecord = Movie(
                imdbID=content['imdbID'],
                title=content['Title'],
                year=content['Year'],
                rated=content['Rated'],
                released=content['Released'],
                runtime=content['Runtime'],
                genre=content['Genre'],
                director=content['Director'],
                writer=content['Writer'],
                actors=content['Actors'],
                plot=content['Plot'],
                language=content['Language'],
                country=content['Country'],
                poster=content['Poster'],
                metascore=content['Metascore'],
                imdbRating=content['imdbRating'],
            )

            try:
                Movie.objects.get(imdbID=newMovieRecord.imdbID)
            except:
                newMovieRecord.save()

        return render(request, '../templates/movie.html', {"movie": movieDict, "lists": listArray})

    elif request.method == 'POST':

        if 'listAdd' in request.POST:
            print(request.POST['movie'])

            movie = Movie.objects.get(imdbID=request.POST['movie'])

            userObject = User.objects.get(username=request.session.get('username'))
            profile = Profile.objects.get(user=userObject)

            if request.POST['listAdd'] == 'watch':
                print("watch")
                profile.toWatchList.add(movie)

            else:
                print("watched")
                profile.watchedList.add(movie)

            return render(request, '../templates/movie.html', {"movie": movie, "lists": listArray})


        else:

            movie = request.POST['movie']

            try:
                movie = Movie.objects.get(imdbID=movie['imdbID'])
            except:

                newMovieRecord = Movie(
                    imdbID=movie['imdbID'],
                    title=movie['title'],
                    year=movie['year'],
                    rated=movie['rated'],
                    released=movie['released'],
                    runtime=movie['runtime'],
                    genre=movie['genre'],
                    director=movie['director'],
                    writer=movie['writer'],
                    actors=movie['actors'],
                    plot=movie['plot'],
                    language=movie['language'],
                    country=movie['country'],
                    poster=movie['poster'],
                    metascore=movie['metascore'],
                    imdbRating=movie['imdbRating'],
                )

                newMovieRecord.save()

            return render(request, '../templates/movie.html', {"movie": movie, "lists": listArray})


def friends(request):
    if request.session.get('loggedIn'):
        updateLists(request)
    error = False
    if request.session.get('loggedIn'):
        currentUser = User.objects.get(email=request.session.get('email'))
        if request.method == 'POST':
            if request.POST.get("Unfollow"):
                try:
                    to_delete = User.objects.get(email=request.POST.get('Unfollow'))
                    currentUser.profile.friends.remove(to_delete)
                    currentUser.save()
                except (KeyError, User.DoesNotExist):
                    print("")
            else:
                try:
                    to_add = User.objects.get(email=request.POST['add_friend'])
                    currentUser.profile.friends.add(to_add)
                    currentUser.save()
                except (KeyError, User.DoesNotExist):
                    error = True

        userFriends = currentUser.profile.friends.all()
        return render(request, '../templates/friends.html', {"friends": userFriends, 'error': error, "lists": listArray})

@login_required
def myProfile(request):
    updateLists(request)
    if request.method == 'GET':
        user = request.user
        print(user.username)
        return render(request, '../templates/myProfile.html', {"loggedIn": True, "username": user.username, "name": user.profile.name, "email": user.email, "birthday":user.profile.birthday, 
            "fav_movies":user.profile.fav, "genre":user.profile.fav_genre, "joined":user.profile.joined, "lists": listArray})

    return render(request, '../templates/home.html', {"loggedIn": False})

@login_required
def editProfile(request):
    updateLists(request)
    error = False

    if request.method == 'POST':
        user = request.user
        if request.POST.get('name'): user.profile.name = request.POST.get('name')
        if request.POST.get('fav'): user.profile.fav = request.POST.get('fav')
        if request.POST.get('date'): user.profile.birthday = request.POST.get('date')                        
        if request.POST.get('genre'): user.profile.fav_genre = request.POST.get('genre')
        user.profile.save()
        user.save()
        if request.POST.get('old_password'):
            user = authenticate(username=user.username, password=request.POST.get('old_password'))
            if user is not None:
                if request.POST.get('new_password') and request.POST.get('confirm_password'):
                    user.set_password(request.POST.get('new_password'))
                    user.save()
                    user = authenticate(username=user.username, password=request.POST.get('new_password'))
                    login(request, user)
                    print("Set new password successful")
                    print("Log in again")
            else:
                print("Wrong password. No changes are made")
                return render(request, '../templates/editProfile.html', {"loggedIn": True, "old_name": request.user.profile.name})

        if request.POST.get("delete"):
            try:
                to_delete = User.objects.get(email=request.POST.get('delete'))
                user.profile.friends.remove(to_delete)
                user.save()
            except (KeyError, User.DoesNotExist):
                print("")

        try:
        	friends = user.profile.friends.all()
        except:
            friends = [
                User(username="Mike", password="mike", email="mike@email.com", first_name="Mike", last_name="Tyson")]

        return HttpResponseRedirect('myProfile.html', {"username": user.username, "name": user.profile.name, "email": user.email, "birthday":user.profile.birthday, 
            "fav_movies":user.profile.fav, "genre":user.profile.fav_genre, "joined":user.profile.joined, "friends": friends, "lists": listArray})

    else:
        print("Still here")
        return render(request, '../templates/editProfile.html', {"loggedIn": True, "error": error, "old_name": request.user.profile.name, "lists": listArray})



def sync_genres():
    url = "https://api.themoviedb.org/3/genre/movie/list?api_key=cc4b67c52acb514bdf4931f7cedfd12b&language=en-US"

    payload = "{}"
    headers = {'content-type': 'application/json'}

    response = requests.request("GET", url, data=payload, headers=headers)
    content = json.loads(response.text)

    genres = content["genres"]

    for item in genres:
        genre = Genre(name=item['name'], tmdbID=str(item['id']))
        genre.save()


def randomMovies(request):
    if request.session.get('loggedIn'):
        updateLists(request)
    # gets a random movie from movies in the database
    n_movies = Movie.objects.count()
    m = Movie.objects.all()
    movies = []
    i = 0

    if n_movies:
        if n_movies < 12:
            num_rand = n_movies
        else:
            num_rand = 12

        while i < num_rand:
            rand_movie = m[random.randrange(0, n_movies)]
            if rand_movie in movies:
                continue

            movies.append(rand_movie)
            i += 1

            # slower and probably worse way of random movie, generates number between 1-4000000
            # and uses that number as an id
            '''movies = []
              i = 0
              while i < 4:
                  rand_n = random.randrange(1, 4000000)
                  url = "http://www.omdbapi.com/?i=tt" + str(rand_n) + "&plot=short&r=json"
                  response = requests.get(url)
                  content = json.loads(response.text)
                  class Movie:
                      def __init__(self, title, year, ID, poster):
                          self.title = title
                          self.year = year
                          self.imdbID = ID
                          self.poster = poster
                  # TODO make item some kind of object which includes imdbID so when clicked, it can link to more detailed info
                  try:
                      movies.append(Movie(content["Title"], content["Year"], content["imdbID"], content["Poster"]))
                  except:
                      continue
                  i += 1
              '''

    return render(request, '../templates/randomMovies.html', {"query": movies})


def randomTVShows(request):
    if request.session.get('loggedIn'):
        updateLists(request)

    movies = []

    a = Movie(title="The Simpsons", imdbID="tt0096697", year="1989-", poster="static/images/no_image.jpg")
    movies.append(a)
    a = Movie(title="How I Met Your Mother", imdbID="tt0096697", year="2005-2014", poster="https://images-na.ssl-images-amazon.com/images/M/MV5BMTA5MzAzNTcyNjZeQTJeQWpwZ15BbWU3MDUyMzE1MTk@._V1_SX300.jpg")
    movies.append(a)
    a = Movie(title="Family Guy", imdbID="tt0182576", year="1999-", poster="https://images-na.ssl-images-amazon.com/images/M/MV5BYmU1ZGRkNDMtODFiNy00ZjgyLWJlMzktY2MyNWJjODY4MTBmXkEyXkFqcGdeQXVyMzM4NjcxOTc@._V1_SX300.jpg")
    movies.append(a)
    a = Movie(title="Dexter", imdbID="tt0773262", year="2006-2013", poster="static/images/no_image.jpg")
    movies.append(a)
    a = Movie(title="American Dad", imdbID="tt0397306", year="2005-", poster="https://images-na.ssl-images-amazon.com/images/M/MV5BODQ0NTE3Mjg3N15BMl5BanBnXkFtZTcwNDY2MDMwNw@@._V1_SX300.jpg")
    movies.append(a)
    a = Movie(title="Supernatural", imdbID="tt0460681", year="2005-", poster="https://images-na.ssl-images-amazon.com/images/M/MV5BMTQ0Mzc1MzM4OV5BMl5BanBnXkFtZTgwNjUxOTg3NjE@._V1_SX300.jpg")
    movies.append(a)
    a = Movie(title="Game of Thrones", imdbID="tt0944947", year="2011-",
              poster="https://images-na.ssl-images-amazon.com/images/M/MV5BMjM5OTQ1MTY5Nl5BMl5BanBnXkFtZTgwMjM3NzMxODE@._V1_SX300.jpg")
    movies.append(a)
    a = Movie(title="CSI: Crime Scene Investigation", imdbID="tt0247082", year="2000-2015", poster="https://images-na.ssl-images-amazon.com/images/M/MV5BMTkyODgwMDMzNV5BMl5BanBnXkFtZTgwMTExOTMyMjE@._V1_SX300.jpg")
    movies.append(a)
    a = Movie(title="The 100", imdbID="tt2661044", year="2014-", poster="https://images-na.ssl-images-amazon.com/images/M/MV5BYWIzNDMwNGYtMjk5ZC00ZjA2LTg4ZDgtZmI5NDEzMzdkZTc5XkEyXkFqcGdeQXVyNDExMTIxMDc@._V1_SX300.jpg")
    movies.append(a)
    a = Movie(title="Ed, Edd, 'n' Eddy", imdbID="tt0184111", year="1999-2009",
              poster="https://images-na.ssl-images-amazon.com/images/M/MV5BMTQ1MzYwMjk0NV5BMl5BanBnXkFtZTgwMDQ4NDgwMzE@._V1_SX300.jpg")
    movies.append(a)
    a = Movie(title="Gilmore Girls", imdbID="tt0238784", year="2000-2007", poster="https://images-na.ssl-images-amazon.com/images/M/MV5BMTYyMjM4Mjc5MF5BMl5BanBnXkFtZTcwMTg1OTAzMQ@@._V1_SX300.jpg")
    movies.append(a)
    a = Movie(title="American Horror Story", imdbID="tt1844624", year="2011-", poster="https://images-na.ssl-images-amazon.com/images/M/MV5BMjI5NzQzNTcyMl5BMl5BanBnXkFtZTgwNjQ0MTYyMDI@._V1_SX300.jpg")
    movies.append(a)

    return render(request, '../templates/randomTVShows.html', {'query': movies})


def updateLists(request):
    print("updating lists")
    currentUser = User.objects.get(email=request.session['email'])
    profile = Profile.objects.get(user=currentUser)
    del toWatchList[:]
    del watchedList[:]
    for movie in profile.toWatchList.all():
        print("To" + movie.title)
        toWatchList.append(movie)
    for movie in profile.watchedList.all():
        print("W" + movie.title)
        watchedList.append(movie)
        listArray = [watchedList, toWatchList]

def recommendations(request):

    return render(request, '../templates/recommendations.html')

def chicken_nugget(request):

    return render(request, '../templates/chicken_nugget.html')

def listExample(request):

    return render(request, '../templates/listExample.html')

