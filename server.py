#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""


import os
import random
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response,session
import datetime
from datetime import timedelta

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)


# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "rz2570"
DB_PASSWORD = "1361"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"
global CART
CART=[]
#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
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
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
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
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route('/')
def index():
    context = dict(data = [''])

    return render_template("index.html",**context)

#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
# @app.route('/')
def templete_index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
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


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/check',methods=['POST'])
def check():
  # session['cart'].append({'id':productId,'name':name,'price':price,'merchant':session['merchant']})
  global CART
  mers=[]
  for i in CART:
    mers.append(i['merchant'])
  mers=list(set(mers))
  for m in mers:
    temp=[]
    for i in CART:
      if i['merchant']==m:
        temp.append(i)
    price=0
    content=''
    for t in temp:
      price+=t['price']
      content+=t['name']
      content+=','

    try:
      cmd='INSERT INTO Orders_make_send VALUES ((:v1),(:v2),(:v3),to_date ( (:v4) , \'YYYY-MM-DD\' ) ,(:v5),(:v6))'
      g.conn.execute(text(cmd),v1=random.randint(0,99999999),v2=session['account'],v3=m,v4=datetime.datetime.now().strftime('%Y-%m-%d'),v5=price,v6=content)
  
  
      CART=[]
    except Exception as e:
      print(e)
      return redirect('/cartpage')

 

  return redirect('/cartpage')

@app.route('/delete',methods=['POST'])
def delete():
  # session['cart'].append({'id':productId,'name':name,'price':price})
  global CART
  productId = int(request.form.get('id'))
  ori=CART
  new=[]
  for i in ori:
    if i['id']!=productId:
      new.append(i)
  CART=new
  
 

  return redirect('/cartpage')

@app.route('/cartpage')
def cartpage():
  # session['cart'].append({'id':productId,'name':name,'price':price})
  
  context = {}
  # context['items']=session['cart']
  # print(session['cart'])
  context['items']=CART
  print(CART)

  total=0
  for i in CART:
    total+=i['price']
  context['total']=total

  
 

  return render_template("cartPage.html",**context)

@app.route('/add',methods=['POST'])
def add():
  
  productId = int(request.form.get('id'))
  name=request.form.get('name')
  price=int(request.form.get('price'))

  
  # session['cart'].append({'id':productId,'name':name,'price':price,'merchant':session['merchant']})
  # print(session['cart'])
  CART.append({'id':productId,'name':name,'price':price,'merchant':session['merchant']})
  print(CART)
  merchant_id=session['merchant']

  context = {}
  context['id']=merchant_id
  cmd='SELECT merchant_id, category, address, star, is_vip FROM Merchants WHERE merchant_id=(:v1)'
  cursor =g.conn.execute(text(cmd),v1=merchant_id)
  results=[]
  for result in cursor:
    results.append(result)
  merchant_inf=results[0]
  context['merchant_inf']=merchant_inf


  cmd='SELECT user_id, rating, content FROM Comments_edit_write WHERE merchant_id=(:v1)'
  cursor =g.conn.execute(text(cmd),v1=merchant_id)
  results=[]
  for result in cursor:
    results.append(result)
  context['comments']=results


  cmd='SELECT product_id, product_name, price FROM Products WHERE merchant_id=(:v1)'
  cursor =g.conn.execute(text(cmd),v1=merchant_id)
  results=[]
  for result in cursor:
    results.append(result)
  context['menu']=results

  return render_template("merchantPage.html",**context)




 
@app.route('/post',methods=['POST'])
def post():
  
  content = request.form.get('post')
  try:
    cmd='INSERT INTO Posts_edit VALUES ((:v1),(:v2),(:v3),(:v4))'
    g.conn.execute(text(cmd),v1=random.randint(0,99999999),v2=session['account'],v3=content,v4=0)
  except Exception as e:
    print(e)
    return redirect('/postpage')


  return redirect('/postpage')

@app.route('/like',methods=['POST'])
def like():
  try:
    postId=int(request.form.get('id'))
  

    cmd='''UPDATE Posts_edit
    SET likes=likes+1 
    WHERE post_id=(:v1)'''
    g.conn.execute(text(cmd),v1=postId)
  except Exception as e:
    print(e)
    

  return redirect('/postpage')

@app.route('/postpage')
def postpage():
  

  cmd='''
  SELECT user_id,post_id, content, likes 
  FROM Posts_edit
  WHERE user_id IN(
    SELECT user_id_2
    FROM Follow
    WHERE user_id_1=(:v1)
  )
  
  '''
  cursor =g.conn.execute(text(cmd),v1=session['account'])
  results=[]
  for result in cursor:
    results.append(result)



  context = {}
  context['posts']=results

  cmd='''
  SELECT post_id, content, likes 
  FROM Posts_edit
  WHERE user_id =(:v1)
  '''
  cursor =g.conn.execute(text(cmd),v1=session['account'])
  results=[]
  for result in cursor:
    results.append(result)



 
  context['yourposts']=results



  return render_template("postcenter.html",**context)
  


@app.route('/follow',methods=['POST'])
def follow():
  try:
    userId=int(request.form.get('account'))
  except ValueError:
    return redirect('/mainpage')

  cmd='INSERT INTO Follow VALUES ((:v1),(:v2))'
  g.conn.execute(text(cmd),v1=session['account'],v2=userId)
  return redirect('/mainpage')



@app.route('/searchuser',methods=['POST'])
def searchuser():
  try:
    userId=int(request.form.get('id'))
  except ValueError:
    context = {}
    context['users']=results
    if len(results)>0:
      note='User found'
    else:
      note='don\'t find this user'
    context['note']=note
    return render_template("peoplesearch.html",**context)
  cmd='SELECT * FROM Users WHERE user_id=(:v1)'
  cursor =g.conn.execute(text(cmd),v1=userId)

  results=[]
  #id gender age
  for result in cursor:
    r={}
    r['user_id']=result['user_id']
    if result['gender']==1:
      r['gender']='Female'
    else:
      r['gender']='male'
    r['age']=result['age']
    results.append(r)



  context = {}
  context['users']=results
  if len(results)>0:
    note='User found'
  else:
    note='don\'t find this user'
  context['note']=note
  return render_template("peoplesearch.html",**context)
 




@app.route('/comment',methods=['POST'])
def comment():
  merchant_id=session['merchant']
  try:
    rating = int(request.form.get('rating'))
  except ValueError:  
      return redirect('/mainpage')

  content = request.form.get('comment')
  cmd='INSERT INTO Comments_edit_write VALUES ((:v1),(:v2),(:v3),(:v4),(:v5))'
  g.conn.execute(text(cmd),v1=random.randint(0,99999999),v2=session['account'],v3=merchant_id,v4=rating,v5=content)
 



  
  return redirect('/mainpage')

@app.route('/mainpage')
def mainpage():
  # session['cart']=[]
  session['merchant']=None
  cmd='SELECT merchant_id, merchant_name,category, address, star, is_vip FROM Merchants '
  cursor =g.conn.execute(text(cmd))
  results=[]
  for result in cursor:
    results.append(result)



  context = {}
  context['data']=results

  




  return render_template("mainPage.html",**context)

@app.route('/visit',methods=['POST'])
def visit():
  merchant_id = request.form.get('id')
  session['merchant']=merchant_id
  print(merchant_id)
  context = {}
  context['id']=merchant_id
  cmd='SELECT merchant_id, category, address, star, is_vip FROM Merchants WHERE merchant_id=(:v1)'
  cursor =g.conn.execute(text(cmd),v1=merchant_id)
  results=[]
  for result in cursor:
    results.append(result)
  merchant_inf=results[0]
  context['merchant_inf']=merchant_inf


  cmd='SELECT user_id, rating, content FROM Comments_edit_write WHERE merchant_id=(:v1)'
  cursor =g.conn.execute(text(cmd),v1=merchant_id)
  results=[]
  for result in cursor:
    results.append(result)
  context['comments']=results


  cmd='SELECT product_id, product_name, price FROM Products WHERE merchant_id=(:v1)'
  cursor =g.conn.execute(text(cmd),v1=merchant_id)
  results=[]
  for result in cursor:
    results.append(result)
  context['menu']=results

  return render_template("merchantPage.html",**context)


@app.route('/signuppage')
def signuppage():
    context = dict(data = [''])
    return render_template("signUp.html",**context)

@app.route('/signUp',methods=['POST'])
def signUp():
    account = request.form.get('account')
    password=request.form.get('password')
    rePassword = request.form.get('rePassword')
    gender=int(request.form.get('gender'))
    age=int(request.form.get('age'))
    if password!=rePassword:
        context = dict(data = ['passwords doesn\'t match'])
        return render_template("signUp.html",**context)
    try:  
        account=int(account)
    except ValueError:  
        context = dict(data = ['account must be nunber'])
        return render_template("signUp.html",**context)
    
    cmd = 'INSERT INTO Users VALUES ((:v1),(:v2),(:v3),(:v4));'
    g.conn.execute(text(cmd), v1=account,v2=password,v3=gender,v4=age)





    context = dict(data = ['success'])
    return render_template("index.html",**context)




@app.route('/login',methods=['POST'])
def login():
    session['account']=None
    username = request.form.get('username')
    password=request.form.get('password')
    print(username)
    
    
    cmd='SELECT password FROM Users WHERE user_id = (:name1)'
    cursor =g.conn.execute(text(cmd), name1 = username)
    results=[]
    for result in cursor:
        results.append(result[0])
    
    
    if password==result[0]:
        print('login success')
        cursor.close()
        session['account']=username
        # session['cart']=[]
        CART=[]
        return redirect('/mainpage')
    else:
        print('fail')
        context = dict(data = ['Wrong password'])
        cursor.close()
        return render_template("index.html", **context)



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
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """
    
    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()