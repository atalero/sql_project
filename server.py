#!/usr/bin/env python2.7
import re
names = set()
"""
Go to http://localhost:8111 in your browser.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
DATABASEURI = "postgresql://aft2120:xinandandres@35.231.44.137/proj1part2"

engine = create_engine(DATABASEURI)

engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass
#

@app.route('/start')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #
  #     # creates a <div> tag for each element in data
  #     # will print:
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)

  return render_template("index.html", **context) #SEND IN ALL THE ELEMENTS IN A DICTIONARY




#PAGES
@app.route('/dishes/<did>')
def dishes(did):
    elements = []

    #0
    names = g.conn.execute("SELECT dishes.dish_name FROM dishes WHERE dishes.did='{}'".format(did))

    names_list = []
    for result in names:
        names_list.append(result['dish_name'])  # can also be accessed using result[0]
    names.close()

    elements.append(names_list[0])

    #1
    ingredients = g.conn.execute("SELECT ingredients.name AS ingredients FROM ingredients INNER JOIN has_ingredients ON ingredients.iid=has_ingredients.iid WHERE has_ingredients.did='{}'".format(did))

    ingredients_list = []
    for result in ingredients:
        ingredients_list.append(result['ingredients'])  # can also be accessed using result[0]
    ingredients.close()

    elements.append(ingredients_list)


    #2
    food_types = g.conn.execute("SELECT DISTINCT food_types.name as dish_type from food_types, has_ingredients, has_categories WHERE has_ingredients.iid=has_categories.iid AND food_types.ftid=has_categories.ftid AND has_ingredients.did='{}'".format(did))

    food_types_list = []
    for result in food_types:
        food_types_list.append(result['dish_type'])  # can also be accessed using result[0]
    food_types.close()

    elements.append(food_types_list)


    return render_template("dishes.html",elements = elements)

@app.route('/party/<pid>/<current_user_uid>')
def party(pid,current_user_uid):
    elements = []
    #0
    attendees = g.conn.execute("SELECT people.name from people, attends WHERE people.uid=attends.uid AND attends.approved='Y' AND attends.pid='{}'".format(pid))

    attendees_list = []
    for result in attendees:
        attendees_list.append(result['name'])  # can also be accessed using result[0]
    attendees.close()

    elements.append(attendees_list)


    #1
    party_name = g.conn.execute("SELECT parties.name FROM parties WHERE parties.pid='{}'".format(pid))
    party_names = []

    for result in party_name:
        party_names.append(result['name'])
    party_name.close()
    elements.append(party_names[0])


    #2
    party_date = g.conn.execute("SELECT to_char(parties.start_time, 'Day, Month DD, YYYY  HH12:MI') AS date FROM parties WHERE parties.pid='{}'".format(pid))
    party_dates = []
    for result in party_date:
        party_dates.append(result['date'])
    party_date.close()
    elements.append(party_dates[0])

    #3
    party_host = g.conn.execute("SELECT people.name FROM people, parties WHERE parties.host=people.uid AND parties.pid='{}'".format(pid))
    party_hosts = []

    for result in party_host:
        party_hosts.append(result['name'])
    party_host.close()
    elements.append(party_hosts[0])

    #4
    party_city = g.conn.execute("SELECT people.current_city AS city FROM people, parties WHERE parties.host=people.uid AND parties.pid='{}'".format(pid))
    party_cities = []

    for result in party_city:
        party_cities.append(result['city'])
    party_city.close()
    elements.append(party_cities[0])

    #5
    waitlisted_attendees = g.conn.execute("SELECT people.name from people, attends WHERE people.uid=attends.uid AND attends.approved='P' AND attends.pid='{}'".format(pid))
    waitlisted_attendees_list = []

    for result in waitlisted_attendees:
        waitlisted_attendees_list.append(result['name'])
    waitlisted_attendees.close()
    elements.append(waitlisted_attendees_list)


    #6
    activities = g.conn.execute("SELECT activities.description AS activities from activities INNER JOIN contains ON contains.aid=activities.aid WHERE contains.pid='{}'".format(pid))
    activities_list = []

    for result in activities:
        activities_list.append(result['activities'])
    activities.close()

    elements.append(activities_list)

    elements.append(pid)#7
    elements.append(current_user_uid)#8

    return render_template("party.html",elements = elements)



@app.route('/user/<name>')
def user(name):
    #Get all the parties that the user is attending or has attended
    parties = g.conn.execute("select people.name,parties.name as party_name,to_char(parties.start_time, 'Day, Month DD, YYYY  HH12:MI') as time from attends,people,parties where attends.uid = people.uid and attends.pid = parties.pid and people.name = '{}' and attends.approved='Y'".format(name))

    parties_list = []
    for result in parties:
        parties_list.append((result['party_name'],result['time']))  # can also be accessed using result[0]
    parties.close()

    #Get all the parties that a user is hosting/has hosted and the date
    party_conn = g.conn.execute("SELECT parties.name as party_name, to_char(parties.start_time, 'Day, Month DD, YYYY  HH12:MI') as time FROM parties,people WHERE parties.host = people.uid and people.name='{}'".format(name))
    parties_hosted = []

    for result in party_conn:
        parties_hosted.append((result['party_name'],result['time']))
    party_conn.close()

    cook_conn = g.conn.execute("SELECT dishes.dish_name as dish_name FROM cooks, dishes,people WHERE cooks.did=dishes.did and cooks.uid = people.uid AND people.name='{}'".format(name))
    dish_names = []
    for result in cook_conn:
        dish_names.append(result['dish_name'])
    cook_conn.close()


    current_city = g.conn.execute("SELECT people.current_city AS city from people WHERE people.name='{}'".format(name))
    current_city_list = []
    for result in current_city:
        current_city_list.append(result['city'])
    current_city.close()


    current_city = current_city_list[0]

    uid = g.conn.execute("Select people.uid from people where people.name = '{}'".format(name))

    uid_list = []

    for result in uid:
        uid_list.append(result['uid'])

    uid.close()
    uid = uid_list[0]

    party_references = g.conn.execute("SELECT DISTINCT parties.name AS party_name, parties.pid FROM parties, people, attends WHERE people.current_city='{}' AND parties.pid NOT IN (SELECT parties.pid FROM parties WHERE parties.host={})".format(current_city,uid))

    party_references_list = []

    for result in party_references:
        party_references_list.append((result['party_name'],result['pid']))
    party_references.close()



    pending_approvals = g.conn.execute("select people.name,parties.name as party_name,to_char(parties.start_time, 'Day, Month DD, YYYY  HH12:MI') as time from attends,people,parties where attends.uid = people.uid and attends.pid = parties.pid and people.name = '{}' and attends.approved='P'".format(name))

    pending_approvals_list = []
    for result in pending_approvals:
        pending_approvals_list.append((result['party_name'],result['time']))  # can also be accessed using result[0]
    pending_approvals.close()

    profile_picture = g.conn.execute("select people.image_url from people where people.name='{}'".format(name))

    profile_picture_list = []
    for result in profile_picture:
        profile_picture_list.append(result['image_url'])  # can also be accessed using result[0]
    profile_picture.close()



    people_awaiting_approval = g.conn.execute("SELECT people.name AS name, parties.name AS party_name,parties.pid as party_pid,people.uid as request_uid FROM people, attends, parties WHERE attends.approved='P' and people.uid = attends.uid and attends.pid = parties.pid AND parties.host={}".format(uid))

    people_awaiting_approval_list = []
    for result in people_awaiting_approval:
        people_awaiting_approval_list.append((result['name'],result['party_name'],result['party_pid'],result['request_uid']))
    people_awaiting_approval.close()

    elements = []
    elements.append(name) #0
    elements.append(parties_list) #1
    elements.append(parties_hosted) #2
    elements.append(dish_names) #3
    elements.append(current_city) #4
    elements.append(party_references_list) #5
    elements.append(uid) #6
    elements.append(pending_approvals_list) #7
    elements.append(profile_picture_list[0]) #8
    elements.append(people_awaiting_approval_list) #9
    return render_template("user_profile.html",elements = elements)

#Log User In
@app.route('/')
def start():
    conn = g.conn.execute("SELECT name FROM people")
    global names
    for result in conn:
        names.add(result['name'])
    conn.close()
    return render_template("main_page.html")

@app.route('/create_account')
def create_account():
    return render_template("create_account.html")

@app.route('/another')
def another():
  return render_template("another.html") #WHEN another is called, you can simply return that HTML file

@app.route('/error')
def error():
  return render_template("user_doesnt_exist.html")

#FORMS
@app.route('/approve/<pid>/<uid>/<host_uid>', methods=['POST'])
def approve(pid,uid,host_uid):
  conn = g.conn.execute("SELECT name FROM people where uid={}".format(host_uid))
  names = []
  for result in conn:
      names.append(result['name'])
  conn.close()

  engine.execute("UPDATE attends SET approved='Y' WHERE attends.uid={} AND attends.pid={} AND attends.approved='P'".format(uid,pid))

  return  redirect('/user/{}'.format(names[0]))

@app.route('/deny/<pid>/<uid>/<host_uid>', methods=['POST'])
def deny(pid,uid,host_uid):
  conn = g.conn.execute("SELECT name FROM people where uid={}".format(host_uid))
  names = []
  for result in conn:
      names.append(result['name'])
  conn.close()

  engine.execute("UPDATE attends SET approved='N' WHERE attends.uid={} AND attends.pid={} AND attends.approved='P'".format(uid,pid))

  return  redirect('/user/{}'.format(names[0]))

@app.route('/user_login', methods=['POST'])
def user_login():
    global names
    login_name = request.form['user_login']

    if login_name not in names:
        return redirect('/error')
  #engine.execute("""INSERT INTO people (did) VALUES (1+(select MAX(did) from people));""")
    return redirect('/user/{}'.format(login_name))

@app.route('/add_user', methods=['POST'])
def add_user():
  user_name = request.form['user_name'] #form that is called name
  image_url = request.form['image_url']
  age = request.form['age']
  hometown = request.form['hometown']
  current_city = request.form['current_city']

  max_uid = g.conn.execute("SELECT MAX(uid) from people")
  max = []
  for result in max_uid:
    max.append(result['max'])  # can also be accessed using result[0]
  print max
  max_uid.close()
  uid = max[0] + 1

  engine.execute("INSERT INTO people VALUES ('{}', '{}' ,{} ,{} ,'{}','{}')".format(user_name, image_url, age, uid, hometown, current_city))

  return redirect('/')

# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['user_name'] #form that is called name
  g.conn.execute("INSERT INTO test(name) VALUES ('{}')".format(name))
  #USE regular python .format() for forms e.g. '{} {}'.format('one', 'two')
  return redirect('/')

@app.route('/attend/<pid>/<uid>', methods=['POST'])
def attend(pid,uid):
  engine.execute("INSERT INTO attends VALUES ({},{}, 'P')".format(uid, pid, 'approved'))

  conn = g.conn.execute("SELECT name FROM people where uid={}".format(uid))
  names = []
  for result in conn:
      names.append(result['name'])
  conn.close()

  return  redirect('/user/{}'.format(names[0]))

@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
