# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://storage.sqlite')    
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db = db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db)
crud, service, plugins = Crud(db), Service(), PluginManager()

# Extra fields for user
#auth.settings.extra_fields['auth_user']= [
#  Field('is_admin', 'boolean', default=False, label='I will be the one paying the bills and collecting')]

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail=auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth,filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)

# A table to store home names
db.define_table('home',
    Field('home_name', 'string', requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'home.home_name')]))

# A table to store bills
db.define_table('bill',
    Field('company_name', 'string', requires=IS_NOT_EMPTY()),
    Field('amount', 'decimal(5, 2)', requires=IS_NOT_EMPTY()),
    Field('bill', 'upload'),
    Field('home', 'reference home', writable=False),
    Field('created_on', 'date', 'default=request.now'))

# A table to store user-home pairs. i.e. the homes where the user is a roommate and whether they are admin
db.define_table('user_home',
    Field('user', 'reference auth_user'),
    Field('home', 'reference home', requires=[IS_NOT_EMPTY(), IS_IN_DB(db, 'home.id')], label='Home ID'), 
    Field('is_admin', 'boolean', writable=False),
    Field('status', 'string', writable=False),
    Field('amount_paid', 'decimal(10,2)'))

# A table to store the total of a user's payments for a particular home
db.define_table('payments',
    Field('user', 'reference auth_user'),
    Field('home', 'reference home'),
    Field('total_payments', 'decimal(10,2)'))

# global variables
def name_of_home(home_id): return db(db.home.id==home_id).select(db.home.home_name)[0]['home_name']
def name_of_user(user_id): return db(db.auth_user.id==user_id).select(db.auth_user.ALL)[0]['first_name'] + ' ' + db(db.auth_user.id==user_id).select(db.auth_user.ALL)[0]['last_name']
def name_of_month(month):
    month_name = ''
    if month == 1:
        month_name = 'January'
    elif month == 2:
        month_name = 'February'
    elif month == 3:
        month_name = 'March'
    elif month == 4:
        month_name = 'April'
    elif month == 5:
        month_name = 'May'
    elif month == 6:
        month_name = 'June'
    elif month == 7:
        month_name = 'July'
    elif month == 8:
        month_name = 'August'
    elif month == 9:
        month_name = 'September'
    elif month == 10:
        month_name = 'October'
    elif month == 11:
        month_name = 'November'
    elif month == 12:
        month_name = 'December'
    return month_name