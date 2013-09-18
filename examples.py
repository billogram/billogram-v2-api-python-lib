#encoding=utf-8
# Copyright (c) 2013 Billogram AB
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# This example code is written to work on Python 2.7 and 3.3.
# Some things are a little uglier for this reason, please bear with us.
from __future__ import unicode_literals, print_function, division

# By default the billogram_api module exports just two symbols, the BillogramAPI
# class and the BillogramExceptions namespace-class.
# Effectively, importing * should be fine in all cases, although your coding
# standards may prescribe otherwise.
from billogram_api import *
#from billogram_api import BillogramAPI, BillogramExceptions  # same effect

# Some of these examples need to work with dates
from datetime import date, timedelta


def create_connection():
    """Create an API pseudo-connection object for the examples

    Either read configuration from a local configuration module, or from
    standard input if the module does not exist.
    """
    try:
        from _testing_defaults import API_USER, API_KEY, API_URLBASE
        print("Using credentials from _testing_defaults")
        username = API_USER
        authkey = API_KEY
        api_urlbase = API_URLBASE or None

    except:
        # Python 2/3 compatibility
        try: input = raw_input
        except: pass

        # Get the credentials from standard input
        username = input("Enter API username: ").strip()
        authkey = input("Enter API authentication key: ").strip()
        api_urlbase = input("API URL base (or blank for default): ").strip() or None

    # The BillogramAPI constructor can optionally take api_base and user_agent if you
    # want or need to override those, but for regular production operation the defaults
    # should be correct.
    # For testing you may have been given an api_base URL for a testing environment.
    return BillogramAPI(username, authkey, api_base=api_urlbase)


def example1(api):
    """Basic example, create, send and credit an invoice

    The invoice will be sent to customer number 1, and be for 1 unit of item 1.

    Will obviously fail if there are no customers or items with numbers 1 on the
    business account connected to.
    """
    # Make a dictionary with the data for the billogram object we want to create
    # Skip non-mandatory fields in this example
    data = {
        # Specifying the recipient, must always be one from the database.
        'customer': {
            # On creation, only the customer_no can be specified.
            'customer_no': 1
        },
        # Specifying the items being invoiced for, can either be from the database or single-use ones
        'items': [
            {
                # This item specifies just an item_no, so it always uses one from the database.
                # If there is no item by this number, the call will fail since other mandatory
                # fields are then missing.
                # Note that item numbers are strings, they can contain non-numeric characters.
                'item_no': '1',
                # You must always specify how many of each item is being invoiced for.
                'count': 1
            }
        ],
        # The inovoicing currency must always be given, although currently only SEK is supported.
        'currency': 'SEK',
        # Have the due date be 35 days (5 weeks) in the future
        'due_date': (date.today() + timedelta(days=35)).isoformat()
    }

    print("Creating and sending billogram with data:\n{}".format(prettyfy(data)))

    try:
        # Attempt to create and then send the billogram using the data. If this succeeds,
        # the result will be a billogram object, wrapping a dictionary with the state of
        # the billogram after the two operations.
        bg = api.billogram.create_and_send(data, 'Email')
        print("The result of creating the billogram object:\n{}".format(prettyfy(bg.data)))

        print("Now crediting the entire billogram (id {})".format(bg['id']))
        # Credit the billogram, creates a new state in the billogram object and sends a
        # credit invoice to the recipient. The object is updated with the new state
        # after the operation.
        bg.credit_full()
        print("State of billogram after crediting:\n{}".format(prettyfy(bg.data)))

    except BillogramExceptions.BillogramAPIError as e:
        print("An API error occurred: {!r}".format(e))



def example2(api):
    """Find all "gadget" items and increase their price by 10%
    """
    # First create a query object for the items class
    qry = api.items.query()
    # Set up some query parameters
    qry.filter_search('title', 'gadget')  # items with "gadget" in somewhere their title

    # print some status
    print("Matched {} gadget items to change".format(qry.count))

    # Loop over every page of results, processing all items
    for item in qry.iter_all():
        print("Current price for item {} is {}".format(item['item_no'], item['price']))
        # modify the item
        item.update({
            'price': item['price']*1.1
        })
        print("    New price is {}".format(item['price']))



def example3(api):
    """Create or find a customer and invoice them
    """
    customer_no = 12345
    try:
        print("Trying to fetch customer {}".format(customer_no))
        customer = api.customers.get(customer_no)
        print("Found the customer")

    except BillogramExceptions.ObjectNotFoundError:
        print("Customer not found, creating instead")
        customer_data = {
            "customer_no": customer_no,
            "name": "Terkel Testsson",
            "contact": {
                "name": "Terkel Testsson",
                "email": "terkel@example.com",
            },
            "address": {
                "street_address": "Exempelgatan 123",
                "city": "Stockholm",
                "zipcode": "123 45",
                "country": "SE",
            },
            "company_type": "individual",
        }
        customer = api.customers.create(customer_data)
        print("Customer was created")

    print("Trying to create billogram object")
    billogram_data = {
        "customer": {
            "customer_no": customer_no,
        },
        "items": [
            {
                "title": "Customer assistance",
                "description": "Phone conversation and physical warehouse search",
                "price": 300,
                "unit": "hour",
                "vat": 25,
                "count": 0.5,
            },
            {
                "item_no": "20",
                "description": "Adding 0.14 extra for your convenience",
                "count": 3.14,
            },
        ],
        "currency": "SEK",
        "invoice_fee": 50,
        "due_date": (date.today() + timedelta(days=30)).isoformat(),
        "automatic_reminders": False,
    }
    billogram = api.billogram.create(billogram_data)
    print("Billogram object created, id is {}".format(billogram['id']))

    customer.update({"notes": "Last conversation was on invoice id {}".format(billogram['id']) })
    print("Customer object updated before sending invoice")

    billogram.send('Email+Letter')
    print("Invoice has now been sent")



def example4(api):
    """Find a fully paid or credited invoice and download all its PDF documents
    """
    print("Querying for paid or credited billogram objects")
    query = api.billogram.query()
    query.filter_state_any('Paid', 'Credited')
    query.page_size = 1
    bgs = query.get_page(1)
    if not bgs:
        print("No billogram found")
        return
    bg = bgs[0]
    print("Found billogram with id {0[id]}, state is {0[state]}".format(bg))
    print("Getting full information for billogram object")
    bg.refresh()  # the object is initially a compact one, refreshing it will get the full data
    print("Now processing events")
    for ev in bg['events']:
        print("{0[type]} event at {0[created_at]}".format(ev))
        if ev['data'] and 'letter_id' in ev['data']:
            print("  - has letter_id {0[data][letter_id]}, getting it".format(ev))
            try:
                pdf = bg.get_invoice_pdf(letter_id=ev['data']['letter_id'])
                print("  - pdf is {} bytes long".format(len(pdf)))
            except BillogramExceptions.ObjectNotAvailableYetError:
                print("  - pdf not created yet")
            except BillogramExceptions.ObjectNotFoundError:
                print("  - pdf was not found")


def example5(api):
    """This example shows some error handling
    """
    # A billogram dataset containing invalid items
    billogram_data = {
        "customer": {
            "customer_no": 12345
        },
        "items": [
            # This item (0) is fine
            {'title': 'Test 1', 'price': 1, 'unit': 'unit', 'vat': 25, 'count': 1},
            # This one (1) is fine too
            {'title': 'Test 2', 'price': -2, 'unit': 'kg', 'vat': 0, 'count': 1},
            # Error here (2), title is empty
            {'title': '', 'price': 3, 'unit': 'kg', 'vat': 0, 'count': 1},
            # Error here too (3), missing count
            {'title': 'Test 4', 'price': -10, 'vat': 0},
        ],
        "currency": "SEK",
        "due_date": (date.today() + timedelta(days=30)).isoformat(),
    }
    # Attempt creating it
    try:
        print("Trying to create invalid billogram")
        bg = api.billogram.create(billogram_data)
        print("Billogram created?! This should not happen.")
    except BillogramExceptions.RequestDataError as e:
        print("Creating the billogram failed! Exception is {}".format(e.__name__))
        if e.message:
            print("The error message returned is: {}".format(e.message))
        if e.field:
            print("The context of the error is {} and the field name is '{}'".format(e.error_source, e.field))
        if e.field_path:
            print("Additionally, the error is located in this sub-object: {}".format(e.field_path))
        print("The expected error is 'Title not set', in the 'title' field of ['items', 2]")




######### From here on it's just housekeeping, no more examples #########


# Helper function to pretty-print the structures
def prettyfy(o, level=''):
    nextlevel = level + '  '
    if isinstance(o, dict):
        return '{\n' + ',\n'.join(['{}{!s}: {}'.format(nextlevel, k, prettyfy(v, nextlevel)) for k, v in o.items()]) + '\n' + level + '}'
    elif isinstance(o, list):
        return '[\n' + ',\n'.join(['{}{}'.format(nextlevel, prettyfy(v, nextlevel)) for v in iter(o)]) + '\n' + level + ']'
    elif isinstance(o, set):
        return '{\n' + ',\n'.join(['{}{}'.format(nextlevel, prettyfy(v, nextlevel)) for v in iter(o)]) + '\n' + level + '}'
    elif isinstance(o, tuple):
        return '(\n' + ',\n'.join(['{}{}'.format(nextlevel, prettyfy(v, nextlevel)) for v in iter(o)]) + '\n' + level + ')'
    else:
        return repr(o)

# For running the examples from a terminal
if __name__ == '__main__':
    print("Billogram v2 API examples")
    api = create_connection()
    print()

    print("Running example 1")
    example1(api)
    print()

    print("Running example 2")
    example2(api)
    print()

    print("Running example 3")
    example3(api)
    print()

    print("Running example 4")
    example4(api)
    print()

    print("Running example 5")
    example5(api)
    print()

    print("Finished running all examples")

