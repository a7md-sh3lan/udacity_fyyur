#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
# implement Genre Model and Relations
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String(120)))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    description = db.Column(db.String(500), default='')
    seeking_talent = db.Column(db.Boolean, default=False)
    website = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    # add show relation
    artists = db.relationship('Show', back_populates='venue')
    def info(self):
      return{
        'id': self.id,
        'name': self.name,
        'genres': self.genres,
        'address': self.address,
        'city': self.city,
        'state': self.state,
        'phone': self.phone,
        'website': self.website,
        'facebook_link': self.facebook_link,
        'seeking_talent': self.seeking_talent,
        'seeking_description': self.description,
        'image_link': self.image_link
      }

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String(120)))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500)) 
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500), default='')
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    # add show relation
    venues = db.relationship('Show', back_populates='artist')
    def info(self):
      return{
        'id': self.id,
        'name': self.name,
        'genres': self.genres,
        'city': self.city,
        'state': self.state,
        'phone': self.phone,
        'website': self.website,
        'facebook_link': self.facebook_link,
        'seeking_venue': self.seeking_venue,
        'seeking_description': self.seeking_description,
        'image_link': self.image_link
      }
# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'),nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'),nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    artist = db.relationship('Artist',back_populates='venues')
    venue = db.relationship('Venue',back_populates='artists')
    def info(self):
      return{
        'venue_id': self.venue_id,
        'venue_name': self.venue.name,
        'artist_id': self.artist_id,
        'artist_name': self.artist.name,
        'artist_image': self.artist.image_link,
        'start_time': str(self.start_time)
      }
    def artist_show(self):
      return {
        'artist_id': self.artist_id,
        'artist_name': self.artist.name,
        'artist_image_link': self.artist.image_link,
        'start_time': str(self.start_time)
      }
    def venue_show(self):
      return {
        'venue_id': self.venue_id,
        'venue_name': self.venue.name,
        'venue_image_link': self.venue.image_link,
        'start_time': str(self.start_time)
      }
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  venues = db.session.query(Venue.city,Venue.state).group_by(Venue.city,Venue.state).all()
  result = []
  current_time = datetime.utcnow()
  for venue in venues: 
    city_name = venue[0]
    city_state = venue[1]
    q = db.session.query(Venue).filter(Venue.city == city_name, Venue.state == city_state)
    group = {
      "city": city_name,
      "state": city_state,
      "venues": []
    }
    venues = q.all()
    for venue in venues: 
      group['venues'].append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_show': len(Venue.query.join(Show).filter(venue.id == Show.venue_id,Show.start_time > current_time).all())
      })    
    result.append(group)     
  return render_template('pages/venues.html', areas=result)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term=request.form.get('search_term', '')
  current_time = datetime.utcnow()
  venues = Venue.query.filter(Venue.name.ilike('%'+search_term+'%')).all()
  response={
    "count": len(venues),
    "data":[]
  }
  for venue in venues:
    response['data'].append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(Venue.query.join(Show).filter(venue.id == Show.venue_id,Show.start_time > current_time).all()),
    })
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  current_time = datetime.utcnow()
  target_venue = Venue.query.filter_by(id=venue_id).all()  
  data = list(map(Venue.info, target_venue))[0]
  past_shows = Show.query.join(Venue).join(Artist).filter(venue_id == Show.venue_id,Show.start_time <= current_time).all()
  upcoming_shows = Show.query.join(Venue).join(Artist).filter(venue_id == Show.venue_id,Show.start_time > current_time).all()
  data['past_shows'] = list(map(Show.artist_show, past_shows)) 
  data['upcoming_shows'] = list(map(Show.artist_show, upcoming_shows)) 
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  print(request.form.getlist('genres'), request.form['seeking_talent'])
  try: 
    the_new_venue = Venue(
              name=request.form['name'],
              address=request.form['address'],
              city=request.form['city'],
              state=request.form['state'],
              phone=request.form['phone'],
              image_link=request.form['image_link'],
              facebook_link=request.form['facebook_link'],
              description=request.form['seeking_description'],
              seeking_talent='seeking_talent' in request.form,
              website=request.form['website'],
              genres=request.form.getlist('genres'),             
          )

    db.session.add(the_new_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be created.')
    #see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  print(venue_id)
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash('Venue with id' + venue_id + ' was successfully deleted!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue with id' + venue_id + ' could not be deleted.')
  finally: 
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  # return None
  return redirect(url_for('venues'))
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists =  Artist.query.all()
  data = []
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name,
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term=request.form.get('search_term', '')
  current_time = datetime.utcnow()
  artists = Artist.query.filter(Artist.name.ilike('%'+search_term+'%')).all()
  response={
      "count": len(artists),
      "data":[]
    }
  for artist in artists:
    response['data'].append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(Artist.query.join(Show).filter(artist.id == Show.artist_id, Show.start_time > current_time).all())
    })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  current_time = datetime.utcnow()
  target_artist = Artist.query.filter_by(id=artist_id).all()  
  data = list(map(Artist.info, target_artist))[0]
  past_shows = Show.query.join(Venue).join(Artist).filter(artist_id == Show.artist_id,Show.start_time <= current_time).all()
  upcoming_shows = Show.query.join(Venue).join(Artist).filter(artist_id == Show.artist_id,Show.start_time > current_time).all()
  data['past_shows'] = list(map(Show.venue_show, past_shows)) 
  data['upcoming_shows'] = list(map(Show.venue_show, upcoming_shows)) 
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  target_artist = Artist.query.filter_by(id=artist_id).all()  
  artist = list(map(Artist.info, target_artist))[0]
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist= Artist.query.get(artist_id)
  form = ArtistForm(request.form)
  if form.validate():
    try:   
      if request.form['name'] != '': artist.name=request.form['name'] 
      if request.form['city'] != '': artist.city=request.form['city'] 
      if request.form['state'] != '': artist.state=request.form['state'] 
      if request.form['phone'] != '': artist.phone=request.form['phone'] 
      if request.form.getlist('genres') != '': artist.genres=request.form.getlist('genres')      
      if request.form['image_link'] != '': artist.image_link=request.form['image_link'] 
      artist.seeking_venue='seeking_venue' in request.form
      if request.form['seeking_description'] != '': artist.seeking_description=request.form['seeking_description'] 
      if request.form['facebook_link'] != '': artist.facebook_link=request.form['facebook_link'] 
      if request.form['website'] != '': artist.website=request.form['website'] 
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully edited!')
    except:
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + request.form['name']  + ' could not be edited.')
      print(sys.exc_info())
      db.session.rollback()  
    finally:
      db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  target_venue = Venue.query.filter_by(id=venue_id).all()  
  venue = list(map(Venue.info, target_venue))[0]
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue= Venue.query.get(venue_id)
  form = VenueForm(request.form)
  if form.validate():
    try:   
      if request.form['name'] != '': venue.name=request.form['name'] 
      if request.form['address'] != '': venue.address=request.form['address']
      if request.form['city'] != '': venue.city=request.form['city'] 
      if request.form['state'] != '': venue.state=request.form['state'] 
      if request.form['phone'] != '': venue.phone=request.form['phone'] 
      if request.form.getlist('genres') != '': venue.genres=request.form.getlist('genres')      
      if request.form['image_link'] != '': venue.image_link=request.form['image_link'] 
      venue.seeking_talent='seeking_talent' in request.form
      if request.form['seeking_description'] != '': venue.description=request.form['seeking_description'] 
      if request.form['facebook_link'] != '': venue.facebook_link=request.form['facebook_link'] 
      if request.form['website'] != '': venue.website=request.form['website'] 
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully edited!')
    except:
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()  
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  form = ArtistForm(request.form)
  try: 
    the_new_artist = Artist(
              name=request.form['name'],
              city=request.form['city'],
              state=request.form['state'],
              phone=request.form['phone'],
              genres=request.form.getlist('genres'),     
              image_link=request.form['image_link'],
              seeking_venue= 'seeking_venue' in request.form,
              seeking_description=request.form['seeking_description'],
              facebook_link=request.form['facebook_link'],
              website=request.form['website'],
          )
    db.session.add(the_new_artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + request.form['name']  + ' could not be listed.')
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  shows = Show.query.join(Venue).join(Artist).all()
  data = list(map(Show.info, shows))
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  form = ShowForm(request.form)
  print(request.form, "hhhh", form.validate())
  try: 
    the_new_show = Show(
              venue_id=request.form['venue_id'],
              artist_id=request.form['artist_id'],
              start_time=request.form['start_time'],          
          )
    #Venue.insert(new_venue)
    db.session.add(the_new_show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
