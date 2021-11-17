"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python3 server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
import psycopg2
import random
import string
import re
import pytz
import hashlib
import time
from collections import defaultdict
from typing import DefaultDict
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, flash, session, url_for, request, render_template, g, redirect, Response
from flask_socketio import SocketIO, join_room
from datetime import datetime
from functools import wraps
from datetime import date


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key='secret'
socketio = SocketIO(app)

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.74.246.148/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@34.74.246.148/proj1part2"
#
DATABASEURI = "postgresql://mc5090:0249@34.74.246.148/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
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
    print("uh oh, problem connecting to database")
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
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/2.0.x/quickstart/?highlight=routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: https://flask.palletsprojects.com/en/2.0.x/api/?highlight=incoming%20request%20data

  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)



  #
  # example of a database query
  #
  #cursor = g.conn.execute("SELECT username FROM users")
  #names = []
  #for result in cursor:
  #  names.append(result['username'])  # can also be accessed using result[0]
  #cursor.close()

  #
  # Flask uses Jinja templathttps://github.com/Bamimore-Tomi/fauna-chat.gites, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/primer-on-jinja-templating/
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
  #context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html")

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#

#@app.route('/another')
#def another():
#  print(request.args)
#  cursor = g.conn.execute("SELECT username FROM users")
#  names = []
# for result in cursor:
#    names.append(result['username'])  # can also be accessed using result[0]
#  cursor.close()
#  context = dict(data = names)
#  return render_template("another.html",**context)


# Login functionality
@app.route('/login', methods=['GET','POST'])
def login():
  msg = ''
  if request.method == 'POST' and 'username' in request.form:
        # Create variables for easy access
        username = request.form['username']
        cursor = g.conn.execute("SELECT * FROM users WHERE username = (%s)", username)
        account = cursor.fetchone()

        if account:
          session['loggedin'] = True
          session['user_id'] = account['user_id']
          session['username'] = account['username']
          return redirect(url_for('home'))
        else:
          msg = 'Incorrect username'
  return render_template('index.html', msg=msg)

@app.route('/logout')
def logout():
  session.pop('loggedin', None)
  session.pop('user_id', None)
  session.pop('username', None)
  return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
  # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'name' in request.form and 'username' in request.form and 'email' in request.form:
      # Create variables for easy access
      name = request.form['name']
      username = request.form['username']
      email = request.form['email']
      print("test")
        # Check if account exists using MySQL
      cursor = g.conn.execute("SELECT * FROM users WHERE username = (%s)", username)
      account = cursor.fetchone()
      # If account exists show error and validation checks
      if account:
          msg = 'Account already exists!'
      elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
          msg = 'Invalid email address!'
      elif not re.match(r'[A-Za-z0-9]+', username):
          msg = 'Username must contain only characters and numbers!'
      elif not username or not email or not name:
          msg = 'Please fill out the form!'
      else:
          # Account doesnt exists and the form data is valid, now insert new account into accounts table
          id = ''
          while True:
            id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 7))
            temp = g.conn.execute("SELECT user_id FROM users where user_id = (%s)", id)
            exists = temp.fetchone()
            if not exists:
              break
      
          cursor = g.conn.execute("INSERT INTO users VALUES (%s, %s, %s, %s)", (id, username, email, name))
          cursor1 = g.conn.execute("INSERT INTO consumers(user_id) VALUES (%s)", id)
          msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

# Home page
@app.route('/home')
def home():
  # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        username=session['username']
        user_id=session['user_id']
        ids = []
        posts = []
        data = []
        # Get friends list
        cursor = g.conn.execute("SELECT connection FROM connected_to WHERE user_id = (%s)", user_id)
        friends = cursor.fetchall()
        cursor.close()

        # Collect user ids
        if friends:
          ids.append(user_id)
          for i in friends:
            ids.append(i['connection'])

          # Get posts
          for i in ids:
            cursor = g.conn.execute("SELECT * FROM posts WHERE user_id = (%s)", i)
            temp = cursor.fetchall()
            cursor.close()
            for j in temp:
              cursor = g.conn.execute("SELECT username, name FROM users WHERE user_id = (%s)", j['user_id'])
              names = cursor.fetchone()
              cursor.close()

              data.append(
              {
                "username":names['username'],
                "post_type":j['post_type'],
                "post_content":j['post_content'],
                "user_id":j['user_id'],
                "name":names['name'],
                "privacy_type":j['privacy_type'],
                "date_time":j['date_time'],
                "post_id":j['post_id']
              }
              )
          if data:
            return render_template('home.html', username=username, data=data, hasFriends=True, existsPosts=True)
          else:
            return render_template('home.html', username=username, data=data, hasFriends=True, existsPosts=False)
        else:
          return render_template('home.html', username=username, data=data, hasFriends=False, existsPosts=False)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/posts', methods=['GET','POST'])
def posts():
  if (request.method == 'POST'):
    post_id = ''
    while True:
      post_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))
      temp = g.conn.execute("SELECT post_id FROM posts WHERE post_id = (%s)", post_id)
      exists = temp.fetchone()
      if not exists:
        break
    
    content = request.form['content']
    privacy = request.form['privacy']
    user_id = session['user_id']
    dateTimeObj = datetime.now()
    date = dateTimeObj.strftime('%Y-%m-%d %H:%M:%S')

    cursor = g.conn.execute("INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s)", post_id, 'status', content, user_id, privacy, date)
    cursor.close()
  return redirect(url_for('home'))

# Delete posts
@app.route('/delpost', methods=['POST', 'GET'])
def delpost():
  if (request.method == "POST"):
    post_id = request.form['post_id']
    cursor = g.conn.execute("DELETE FROM posts WHERE post_id = (%s)", post_id)
  return redirect(url_for('home'))


# Profile page
@app.route('/profile')
def profile():
  id = session['user_id']
# Check if user is loggedin
  if 'loggedin' in session:
      # We need all the account info for the user so we can display it on the profile page
      cursor = g.conn.execute("SELECT * FROM users WHERE user_id = (%s)", id)
      account = cursor.fetchone()
      cursor.close()
      cursor1 = g.conn.execute("SELECT * FROM lives_at WHERE user_id = (%s)", id)
      livesAt = cursor1.fetchone()
      cursor1.close()
      cursor2 = g.conn.execute("SELECT connection FROM connected_to WHERE user_id = (%s)", id)
      friends = cursor2.fetchall()

      usernames = []
      for i in friends:
        cursor = g.conn.execute("SELECT username FROM users WHERE user_id = (%s)", i['connection'])
        temp = cursor.fetchone()
        cursor.close
        usernames.append(temp['username'])
      if (livesAt):
        cursor3 = g.conn.execute("SELECT * FROM addresses WHERE street_1 = (%s)", livesAt['street_1'])
        address = cursor3.fetchone()
        cursor3.close()
      else:
        address = 0
      # Show the profile page with account info
      return render_template('profile.html', account=account, address=address, friends=friends, usernames=usernames)
  # User is not loggedin redirect to login page
  return redirect(url_for('login'))

# Add friends
@app.route('/requestadd', methods=['GET', 'POST'])
def requestadd():
  id = session['user_id']
  username = request.form['user']

  if username == id:
    return redirect(url_for('profile'))
  
  try:
    cursor = g.conn.execute("SELECT user_id FROM users WHERE username = (%s)", username)
    user_id = cursor.fetchone()
    cursor.close()
  except:
    return redirect(url_for('profile'))
  
  try:
    cursor = g.conn.execute("INSERT INTO connected_to VALUES (%s, %s)", id, user_id['user_id'])
    cursor.close()
  except:
    return redirect(url_for('profile'))
  return redirect(url_for('profile'))


# Unfollow users
@app.route('/unfollow', methods=['GET','POST'])
def unfollow():
  print("test")
  if (request.method == 'POST'):
    id = session['user_id']
    username = request.form['user']

    cursor = g.conn.execute("SELECT user_id FROM users WHERE username = (%s)", username)
    friend = cursor.fetchone()
    cursor.close()

    cursor = g.conn.execute("DELETE FROM connected_to WHERE user_id = (%s) AND connection = (%s)", id, friend['user_id'])
  return redirect(url_for('profile'))

# Settings page
@app.route('/settings', methods=['GET','POST'])
def settings():
  msg=''
  if request.method == 'POST' and 'address1' in request.form and 'city' in request.form and 'state' in request.form and 'zip' in request.form and 'dob' in request.form and 'size' in request.form and session['user_id']:
    id = session['user_id']
    address1 = request.form['address1']
    address2 = request.form['address2']
    city = request.form['city']
    state = request.form['state']
    zip = request.form['zip']
    dob = request.form['dob']
    size = request.form['size']
    
    cursor1 = g.conn.execute("INSERT INTO addresses VALUES (%s, %s, %s, %s, %s)", address1, address2, city, state, zip)
    cursor2 = g.conn.execute("INSERT INTO lives_at VALUES (%s, %s, %s, %s)", id, address1, address2, zip)
  return render_template('settings.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
  room_id = request.args.get("rid", None)
  id = session['user_id']
  data = []
  chat_list = []
  username = ''
  try:
    chat_list = g.conn.execute("SELECT a.* FROM chat a LEFT OUTER JOIN chat b ON (a.session_id = b.session_id AND a.message_id > b.message_id) WHERE b.session_id IS NULL")
  except:
    chat_list = []
  
  for i in chat_list:
    username = id
    print("sender: " + i['sender'])
    if i['sender'] == id:
      username = i['recipient']
    elif i['recipient'] == id:
      username = i['sender']
  

    cursor = g.conn.execute("SELECT username FROM users WHERE user_id = (%s)", username)
    username = cursor.fetchone()
    cursor.close()
    active = False
    print("username: ")
    print(username)

    if room_id == i['session_id']:
      active = True
    
    try:
      # Last message
      cursor = g.conn.execute("SELECT content FROM chat WHERE session_id =  (%s)", i['session_id'])
      last_message = ''
      for n in cursor:
        last_message = n['content']
      cursor.close()
    except:
      last_message = "No messages..."

    if i['sender'] == id or i['recipient'] == id:
      data.append(
        {
          "username":username['username'],
          "room_id":i['session_id'],
          "active":active,
          "last_message":last_message,
        }
      )
  chat_list.close()
  message = []
  dates = []
  senders = []
  if room_id != None:
    cursor = g.conn.execute("SELECT date_time, content, sender FROM chat WHERE session_id = (%s)", room_id)
    message = cursor.fetchall()
  
  print("test")
  for n in message:
    print(n['sender'])
  return render_template(
    "chat.html",
    user_data=id,
    room_id=room_id,
    data=data,
    message=message,
  )

# New chat
@app.route('/newchat', methods=['POST'])
def newchat():
  print("test1")
  user_id = session['user_id']
  new_chat = request.form['user']
  print(new_chat)

  if new_chat == session['username']:
    return redirect(url_for("chat"))

  try:
    cursor = g.conn.execute("SELECT user_id FROM users WHERE username = (%s)", new_chat)
    new_chat_id = cursor.fetchone()
    cursor.close()
  except:
    return redirect(url_for("chat"))
  
  cursor = g.conn.execute("SELECT * from chat WHERE sender = (%s) OR recipient = (%s)", user_id, user_id)
  senders = cursor.fetchall()
  cursor.close()

  cursor = g.conn.execute("SELECT * from chat WHERE sender = (%s) OR recipient = (%s)", new_chat_id['user_id'], new_chat_id['user_id'])
  recipient = cursor.fetchall()
  cursor.close()

  try:
    chat_list1 = [list(i['recipient'] for i in senders)]
    chat_list2 = [list(i['senders'] for i in senders)]
  except:
    chat_list1 = []
    chat_list2 = []

  if new_chat_id['user_id'] not in chat_list1 or new_chat_id['user_id'] not in chat_list2:
    room_id = ''
    while True:
      room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))
      temp = g.conn.execute("SELECT session_id FROM chat WHERE session_id = (%s)", user_id)
      exists = temp.fetchone()
      if not exists:
        break
    
    dateTimeObj = datetime.now()
    date = dateTimeObj.strftime('%Y-%m-%d %H:%M:%S')
    cursor = g.conn.execute("INSERT INTO chat VALUES (%s, %s, %s, %s, %s, %s)", room_id, '1', date, 'New Chat Request', user_id, new_chat_id['user_id'])
  return redirect(url_for("chat"))

# Join room
@socketio.on("join-chat")
def join_private_chat(data):
    room = data["rid"]
    join_room(room=room)
    socketio.emit(
        "joined-chat",
        {"msg": f"{room} is now online."},
        room=room,
        # include_self=False,
    )

@socketio.on("outgoing")
def chatting_event(json, methods=["GET", "POST"]):
    room_id = json["rid"]
    timestamp = json["timestamp"]
    message = json["message"]
    sender_id = json["sender_id"]
    sender_username = json["sender_username"]

    cursor = g.conn.execute("SELECT a.* FROM chat a LEFT OUTER JOIN chat b ON (a.session_id = b.session_id AND a.message_id > b.message_id) WHERE b.session_id IS NULL")
    message = cursor.fetchall()
    cursor.close()

    for i in message:
      if i['session_id'] == room_id:
        message_id = int(i['message_id']) + 1
    
    cursor = g.conn.execute("INSERT INTO chat VALUES (%s, %s, %s, %s, %s, %s)", room_id, message_id, timestamp, message, sender_id, '')

    socketio.emit(
        "message",
        json,
        room=room_id,
        include_self=False,
    )

# user's cart
@app.route('/cart')
def cart():
  id = session['user_id']
  cursor = g.conn.execute("SELECT * FROM has_in_cart C, products P WHERE C.user_id = (%s) AND P.product_number = C.product_number", id)
  names = []
  quantities = []
  productnumbers = []
  for result in cursor:
    names.append(result['name'])
    quantities.append(result['quantity'])
    productnumbers.append(result['product_number'])
  cursor.close()

  my_dict = defaultdict(dict)
  for i, j, k in zip(names, quantities, productnumbers):
    my_dict[i] = j, k

  order_numbers =[]
  order_dates = []
  statuses = []
  street_1 = []
  street_2 = []
  zips = []
  cursor2 = g.conn.execute("SELECT * FROM orders O WHERE O.user_id = (%s)", id)
  for r in cursor2:
    order_numbers.append(r['order_number'])
    order_dates.append(r['order_date'])
    statuses.append(r['status'])
    street_1.append(r['street_1'])
    street_2.append(r['street_2'])
    zips.append(r['zip'])
  cursor2.close()
    
  my_dict2 = defaultdict(dict) 
  for l, m, n, o, p, q in zip(order_numbers, order_dates, statuses, street_1, street_2, zips):
    my_dict2[l] = m,n,o,p,q
  
  my_dict3 = defaultdict(dict)
  for order in order_numbers:
    cursor3 = g.conn.execute("SELECT * FROM contains_item C, products P WHERE C.product_number = P.product_number AND C.order_number = (%s)",order)
    for item in cursor3:
      my_dict3[order][item['name']] = item['quantity']
    cursor3.close()

  context = {'my_dict':my_dict, 'my_dict2':my_dict2, 'my_dict3':my_dict3}

  return render_template('cart.html', **context)

# remove an item from the cart (cart page)
@app.route('/removefromcart', methods=['POST'])
def removefromcart():
  id = session['user_id']
  product = request.form['removefromcart'] 
  g.conn.execute("DELETE FROM has_in_cart C WHERE C.user_id = (%s) and C.product_number = (%s)", id, product)
  return redirect('/cart')

# checkout page
@app.route('/checkout', methods=['POST','GET'])
def orderpage():
  id = session['user_id']
  cursor = g.conn.execute("SELECT * FROM has_in_cart C, products P WHERE C.user_id = (%s) AND P.product_number = C.product_number", id)
  names = []
  quantities = []
  productnumbers = []
  for result in cursor:
    names.append(result['name'])
    quantities.append(result['quantity'])
    productnumbers.append(result['product_number'])
  cursor.close()

  my_dict = defaultdict(dict)
  for i, j, k in zip(names, quantities, productnumbers):
    my_dict[i] = j, k

  cursor2 = g.conn.execute("SELECT * FROM users U, lives_at L WHERE U.user_id = L.user_id AND U.user_id = (%s)", id)
  street_1 = []
  street_2 = []
  zips = []
  for r in cursor2:
    street_1.append(r['street_1'])
    street_2.append(r['street_2'])
    zips.append(r['zip'])
  cursor2.close()

  my_dict2 = defaultdict(dict)
  count = 0
  for l, m, n in zip(street_1, street_2, zips):
    my_dict2[count] = l,m,n
    count = count + 1

  context = {'my_dict':my_dict,'my_dict2':my_dict2}

  return render_template("order.html", **context)

# set if you want send your order to your address or a new one on checkout page
@app.route('/setaddress',methods=['POST'])
def setaddress():
  whichaddress=request.form['selectaddress']
  print(whichaddress)
  id = session['user_id']
  cursor = g.conn.execute("SELECT * FROM has_in_cart C, products P WHERE C.user_id = (%s) AND P.product_number = C.product_number", id)
  names = []
  quantities = []
  productnumbers = []
  for result in cursor:
    names.append(result['name'])
    quantities.append(result['quantity'])
    productnumbers.append(result['product_number'])
  cursor.close()

  my_dict = defaultdict(dict)
  for i, j, k in zip(names, quantities, productnumbers):
    my_dict[i] = j, k

  cursor2 = g.conn.execute("SELECT * FROM users U, lives_at L WHERE U.user_id = L.user_id AND U.user_id = (%s)", id)
  street_1 = []
  street_2 = []
  zips = []
  for r in cursor2:
    street_1.append(r['street_1'])
    street_2.append(r['street_2'])
    zips.append(r['zip'])
  cursor2.close()

  my_dict2 = defaultdict(dict)
  for l, m, n in zip(street_1, street_2, zips):
    my_dict2[l] = m,n

  context = {'my_dict':my_dict,'my_dict2':my_dict2}

  return render_template("order.html", **context, whichaddress=whichaddress)

# submit order from checkout page
@app.route('/order', methods=['POST'])
def order():
  id = session['user_id']
  order_id = ''
  while True:
    order_id = ''.join(random.choices(string.digits, k = 10))
    temp = g.conn.execute("SELECT * FROM orders O WHERE O.order_number= (%s)", order_id)
    exists = temp.fetchone()
    if not exists:
      break
  today = datetime.now()
  date = today.strftime("%Y-%m-%d")

  
  if 'address1' in request.form and 'city' in request.form and 'state' in request.form and 'zip' in request.form:
    address1 = request.form['address1']
    address2 = request.form['address2']
    city = request.form['city']
    state = request.form['state']
    zip = request.form['zip']
    
    g.conn.execute("INSERT INTO addresses VALUES (%s, %s, %s, %s, %s)", address1, address2, city, state, zip)
    g.conn.execute("INSERT INTO lives_at VALUES (%s, %s, %s, %s)", id, address1, address2, zip)

  cursor = g.conn.execute("SELECT * FROM users U, lives_at L WHERE U.user_id = L.user_id AND U.user_id = (%s)", id)
  street_1 = []
  street_2 = []
  zips = []

  for r in cursor:
    street_1.append(r['street_1'])
    street_2.append(r['street_2'])
    zips.append(r['zip'])
  cursor.close()
  address1 = street_1[0]
  address2 = street_2[0]
  zip=zips[0]
  
  itemsincart = defaultdict(dict)
  cursor1 = g.conn.execute("SELECT * FROM has_in_cart C WHERE C.user_id = (%s)", id)
  for n in cursor1:
    itemsincart[n['product_number']] = n['quantity']
  cursor1.close()

  g.conn.execute("INSERT INTO orders VALUES (%s, %s, %s, %s, %s, %s, %s)",order_id, date, "Processing", id, address1, address2, zip)
  for item in itemsincart:
    g.conn.execute("INSERT INTO contains_item VALUES (%s,%s,%s)", order_id, item, itemsincart[item])
  g.conn.execute("DELETE FROM has_in_cart C WHERE C.user_id = (%s)", id)
  return redirect(url_for('cart'))

# add an item to the cart (item page)
@app.route('/addtocart',methods=['POST'])
def addtocart():
  id = session['user_id']
  product = request.form['add-to-cart'] 
  print(product)
  quantity = request.form['cart-quantity']
  incartalready = g.conn.execute("SELECT * FROM has_in_cart C WHERE C.user_id = (%s) AND C.product_number=(%s)",id, product)
  exists = incartalready.fetchone()
  if not exists:
    g.conn.execute("INSERT INTO has_in_cart VALUES (%s, %s, %s)", id, product, quantity) 
  else:
    g.conn.execute("UPDATE has_in_cart SET quantity = quantity + (%s) WHERE user_id=(%s) AND product_number = (%s)",quantity,id,product)
  return redirect('/cart')

# add review to an item
@app.route('/addreview', methods=['POST'])
def addreview():
    print(request.args)
    id = session['user_id']
    review_type = request.form['add-review']
    next = request.referrer

    selected_color = next.split("&color=",1)
    
    if not not selected_color and selected_color[0] != next:
      selected_item = re.search("type=(.*?)&color=",next).group(1)
      print(selected_item)
      selected_item = selected_item.replace("+", " ")
      selected_color = next.split("&color=",1)[1]
      selected_color = selected_color.replace("+"," ")
      cursor = g.conn.execute("SELECT product_number FROM Products P WHERE P.name = (%s) AND P.color = (%s)", selected_item, selected_color)
    else:
      selected_item = next.split("type=",1)[1]
      selected_item = selected_item.replace("+", " ")
      print(selected_item)
      cursor = g.conn.execute("SELECT product_number FROM Products P WHERE P.name = (%s)", selected_item)
    
    name = []
    for result in cursor:
      name.append(result['product_number'])
    cursor.close()
    product_id = name[0]
    review_id = ''
    while True:
      review_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 7))
      temp = g.conn.execute("SELECT review_id FROM review_posts WHERE review_id = (%s)", review_id)
      exists = temp.fetchone()
      if not exists:
        break
    g.conn.execute("INSERT INTO review_posts VALUES (%s,%s,%s,%s)",review_id,review_type,id,product_id)
    return redirect(next)

# remove one of your reviews for an item
@app.route('/removereview', methods=['POST'])
def removereview():
  next = request.referrer
  review_id = request.form['removereview']
  print(review_id)
  g.conn.execute("DELETE FROM review_posts R WHERE R.review_id = (%s)", review_id)
  return redirect(next)

# populate products page based on category
@app.route('/category', methods=['POST'])
def category():
  print(request.args)
  category = request.form['category']
  print(category)
  categories = []
  product_numbers = []
  descriptions = []
  colors = []
  cursor = g.conn.execute("SELECT product_number, name, description,color FROM Products WHERE products.item_type = (%s)", category)
  
  for result in cursor:
    categories.append(result['name'])
    product_numbers.append(result['product_number'])
    descriptions.append(result['description'])
    colors.append(result['color'])
  cursor.close()

  my_dict2=defaultdict(dict)
  for i,j,k,l in zip(product_numbers, categories, descriptions,colors):
    my_dict2[i][j] = k,l

  context = {'my_dict2':my_dict2, 'category':category}
  return render_template("products.html", **context)

# populate products page based on brand
@app.route('/brand', methods=['POST'])
def brand():
  print(request.args)
  brand = request.form['brand']
  brands = []
  product_numbers = []
  descriptions = []
  colors=[]
  cursor = g.conn.execute("SELECT product_number, name, description,color FROM Products WHERE products.sold_by = (%s) GROUP BY product_number, name, description", brand)
  
  for result in cursor:
    brands.append(result['name'])
    product_numbers.append(result['product_number'])
    descriptions.append(result['description'])
    colors.append(result['color'])
  cursor.close()

  cursor1 = g.conn.execute("SELECT name FROM users WHERE user_id = (%s)", brand)
  names = []
  for n in cursor1:
    names.append(n)
  cursor1.close()
  print(cursor1)

  my_dict2=defaultdict(dict)
  for i,j,k,l in zip(product_numbers,brands, descriptions,colors):
    my_dict2[i][j] = k,l

  my_dict = dict(zip(product_numbers, brands))
  context = {'my_dict':my_dict, 'brand':names, 'my_dict2':my_dict2}

  return render_template("products.html", **context)

# individual item page
@app.route('/item')
def item():
  print(request.args)
  selected_item=request.args.get('type')
  selected_color = request.args.get('color')
  names = []
  if selected_color:
    cursor = g.conn.execute("SELECT * FROM Products, Retailers, Users WHERE products.sold_by = retailers.user_id AND retailers.user_id = users.user_id AND products.name = (%s) AND products.color = (%s)", selected_item, selected_color)
  else:
    cursor = g.conn.execute("SELECT * FROM Products, Retailers, Users WHERE products.sold_by = retailers.user_id AND retailers.user_id = users.user_id AND products.name = (%s)", selected_item)
  for result in cursor:
    names.append(result[0]) #product number
    #names.append(result[1]) #seller id
    names.append(result[2]) #product name
    names.append(result[3]) #color
    names.append(result[4]) #price
    names.append(result[5]) #description
    names.append(result[6]) #bool
    names.append(result[7]) #bool
    #names.append(result[8]) #item type
    #names.append(result[9]) #stock
    names.append(result[10]) #size
    names.append(result[11]) #discount price
    #names.append(result[12]) #seller id
    #names.append(result[13]) #store type
    #names.append(result[14]) #seller id
    names.append(result[15]) #username
    #names.append(result[16]) #email
    names.append(result[17]) #seller name
  cursor.close()

  cursor1 = g.conn.execute("SELECT * FROM review_posts R, users U WHERE R.reviewer = U.user_id AND R.reviewed_product = (%s)", names[0])
  reviews = [] # all reviews for the product (includes all attributes)
  for n in cursor1:
    reviews.append(n)
  cursor1.close()

  photos = []
  for review in reviews:
    cursor4 = g.conn.execute("SELECT * FROM include_photo P WHERE P.review_id = (%s)",review['review_id'])
    for photo in cursor4:
      photos.append(photo)
      #reviews[review].append(photo)
      #print(reviews[review])
      #print(photo)
    cursor4.close()

  cursor2 = g.conn.execute("SELECT COUNT(*)::FLOAT FROM review_posts R WHERE R.review_type = 'thumbs up' AND R.reviewed_product = (%s)", names[0])
  cursor3 = g.conn.execute("SELECT COUNT(*)::FLOAT FROM review_posts R WHERE R.reviewed_product = (%s)", names[0])
  
  average = []
  for i in cursor2:
    for j in cursor3:
      if (j[0] != 0):
        average.append(i[0]/j[0] *100)
    cursor3.close()
  cursor2.close()

  context = dict(data=names)

  return render_template("item.html", **context, reviews=reviews, photos=photos, average=average)


# POST ITEM
# @app.route('/posts', methods=['POST'])
# def posts():


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

        python3 server.py

    Show the help text using:

        python3 server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
