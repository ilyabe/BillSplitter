# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simple replace the two lines below with:
    return auth.wiki()
    """
    response.flash = T("Welcome to web2py!")
    return dict(message=T('Welcome to Bill Splitter'))

# Users can create homes
@auth.requires_login()
def create_home():
    # User creates the home
    form = SQLFORM(db.home).process()

    # Add record in user_home for creating user
    # Creating user automatically becomes the admin
    if form.accepted:
        db.user_home.insert(user=auth.user_id, home=form.vars.id, is_admin=True, status='active')
        redirect(URL('my_homes'))

    return locals()

# Users can view a list of their homes
@auth.requires_login()
def my_homes():
    homes = db(db.user_home.user==auth.user_id).select(db.user_home.ALL)
    
    my_homes = []
    for home in homes:
        my_home = {'id': home.home, 'name': db(db.home.id==home.home).select(db.home.home_name).first().home_name, 'status': home.status, 'is_admin':home.is_admin}
        my_homes.append(my_home)

    return locals()

# Users can add bills
@auth.requires_login()
def add_bill():
    # If the user is not the admin of this home, redirect to my_homes
    # Get this home's admin
    admin_id = db((db.user_home.home==request.args(0)) & (db.user_home.is_admin==True)).select(db.user_home.user).first()['user']

    # If auth.user ID doesn't match, redirect
    if auth.user_id != admin_id:
        redirect(URL('my_homes'))

    # Else allow adding the bill for this home
    db.bill.home.default = request.args(0)
    db.bill.created_on.default = request.now
    form = SQLFORM(db.bill, fields=['company_name', 'amount', 'bill', 'created_on']).process()

    return locals()

# Users can view bills for a specific home
@auth.requires_login()
def view_bills():
    # User's status must be active, else redirect
    user_status = db((db.user_home.home==request.args(0)) & (db.user_home.user==auth.user_id)).select(db.user_home.status).first()['status']
    if user_status != 'active':
        redirect(URL('my_homes'))

    # All bills for this home
    home_bills = db(db.bill.home==request.args(0)).select(db.bill.ALL)

    # Total all time bill
    total_bill = 0
    for bill in home_bills:
        #if (bill.created_on.year == request.now.year) & (bill.created_on.month == request.now.month):
        total_bill += bill.amount

    # Each roommate's portion is calculated as the total all time bill divided by total roommates minus the sum of this roommate's payments
    roommate_bill = 0
    roommate_count = db((db.user_home.home==request.args(0))).count() # Number of roommates in this home

    # Check if this user has made any payments
    this_roommate_payments = 0 # total of this roommate's payments, if any
    user_count = 0
    user_count = db((db.payments.user==auth.user_id)&(db.payments.home==request.args(0))).count()

    this_roommates_payments = 0
    if user_count != 0: # If the user has made payments, get the current sum
        this_roommates_payments = db((db.payments.user==auth.user_id)&(db.payments.home==request.args(0))).select(db.payments.total_payments).first()['total_payments']

    if roommate_count > 0:
        roommate_bill = round((total_bill / roommate_count) - this_roommates_payments, 2)

    # If the user viewing the page is the home's admin, is_admin_user = True
    admin_id = db((db.user_home.home==request.args(0)) & (db.user_home.is_admin==True)).select(db.user_home.user).first()['user']

    is_admin_user = False
    if auth.user_id == admin_id:
        is_admin_user = True

    return locals()

# Users can make a request to join a home and view its bills by providing the home's ID
@auth.requires_login()
def join_home():
    db.user_home.user.default = auth.user_id
    db.user_home.is_admin.default = False
    db.user_home.status.default = 'pending'
    form = SQLFORM(db.user_home, fields=['home']).process()
    return locals()

# Called when user submits home_id on join_home, should validate user is not a roommate at that home already
@request.restful()
def confirm_join():
    print str(request.now)
    print str(request.args(0))

    def GET(name):
        print 'called GET'
        return str(name)

    def PUT(name):
        print 'called PUT'
        return str(name)
    return locals()

# A home's admin can approve/deny requests to join
@auth.requires_login()
def review():
    # Get a list of IDs of all homes where I am the admin
    admin_homes = db((db.user_home.user==auth.user_id) & (db.user_home.is_admin==True)).select(db.user_home.ALL).as_list()

    # For each of the homes where I am the admin, get a list of pending requests
    my_requests = []
    for home in admin_homes:
        pending = db((db.user_home.home==home['home']) & (db.user_home.status=='pending')).select(db.user_home.ALL).as_list()
        my_requests.append(pending)

    return locals()

# Called when the user clicks the Approve button on the review page
@auth.requires_login()
def approve():
    db(db.user_home.id==request.args(0)).update(status='active')

# Called when the user clicks the Deny button on the review page
@auth.requires_login()
def deny():
    db(db.user_home.id==request.args(0)).delete()

# Users can enter their credit card information to pay a particular month's bill
@auth.requires_login()
def pay_bill():
    return locals()

# Called when the submits their credit card information
def charge():
    print 'called charged2'

    roommate_bill_in_cents = 0
    roommate_bill_in_cents = str(request.args(0)).replace('.', '')

    from gluon.contrib.stripe import Stripe
    stripe = Stripe('sk_test_AOSmakDZoUJJ2UZD9keIrlLS')
    d = stripe.charge(amount=roommate_bill_in_cents,
            currency='usd',
                  card_number=request.vars['card-number'],
                  card_exp_month=request.vars['card-expiry-month'],
                  card_exp_year=request.vars['card-expiry-year'],
                  card_cvc_check=request.vars['card-cvc'],
                  description='Bill Splitter')
    paid = False
    if d.get('paid',False):
        # payment accepted
        paid = True
    else:
        # error is in d.get('error','unknown')
        error = d.get('error','unknown')
        paid = False

    # Update or insert the user into the payments table
    if paid:    # If payment successful
        user_count = 0
        user_count = db((db.payments.user==auth.user_id)&(db.payments.home==request.args(1))).count()
        if user_count == 0: # If the user is not in the payments table, insert them
            db.payments.insert(user=auth.user_id, home=request.args(1), total_payments=request.args(0))
        else: # The user is in the payments table, update the total amount they have paid
            # Get the current total
            current_total = 0
            current_total = db((db.payments.user==auth.user_id)&(db.payments.home==request.args(1))).select(db.payments.total_payments).first()['total_payments']

            # Sum the current total with the payment
            from decimal import Decimal
            new_total = 0
            new_total = current_total + Decimal(request.args(0))

            # Update payments record
            db((db.payments.user==auth.user_id)&(db.payments.home==request.args(1))).update(total_payments=new_total)

    return locals()

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
