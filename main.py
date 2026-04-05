from flask import Flask, abort, render_template, request
from math import ceil
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text

app = Flask(__name__)
conn_str = "mysql://root:cset155@localhost/boatdb"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()


# render a file
@app.route('/')
def index():
    return render_template('index.html')


# remember how to take user inputs?
@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


# methods=['GET'] - is usually for retrieving or showing information. (Give me this page/data)
# methods=['POST'] - is usually for sending data to the server to create, update, or delete something. (the function occurs after the submit form button is clicked)(Here is some data, do something with it.)


# get all boats
# this is done to handle requests for two routes -
@app.route('/boats/')
@app.route('/boats/<page>')
def get_boats(page=1):
    page = int(page)  # request params always come as strings. So type conversion is necessary. IMPORTANT
    if page < 1:
        page = 1
    
    per_page = 30  # records to show per page
    total_boats = conn.execute(text("SELECT count(*) FROM boats")).scalar()
    total_pages = max(1, ceil(total_boats / per_page))
    if page > total_pages:
        page = total_pages
        
    # if page < 1 or page > total_pages:
    #     abort(404)

    boats = conn.execute(text(f"SELECT * FROM boats LIMIT {per_page} OFFSET {(page - 1) * per_page}")).all() # the -1 is due to indexing of data so page 1 will have 1-10 ...
    print(boats)
    return render_template('boats.html', boats=boats, page=page, per_page=per_page, count=total_boats, total_pages=total_pages) # you have to do variable=variable


# methods=['GET'] means this route responds to normal page visits and URL query strings.
# GET is commonly used to retrieve/show information, and form data is sent in the URL after '?'.
# Example: /boats/filter?name=Malcolm&type=sail
@app.route('/boats/filter', methods=['GET'])
def boat_filter():
    form_data = { # the get(input "name", default) will deal with the defaults
        'boatID': request.args.get('boatID', None), # the key for each will be the column name. The arguemnt entered is the name from the input in the boats.html file
        'name': request.args.get('name', None),
        'type': request.args.get('type', None),
        'owner_id': request.args.get('owner_id', None),
        'rental_price': request.args.get('rental_price', None)
    }
    whereStatement = f""
    for key, value in form_data.items():
        if value:
            whereStatement += f"{key} = '{value}' and "
    whereStatementList = whereStatement.rsplit(" and ", 1)
    whereStatement = "".join(whereStatementList)
    
    boats = conn.execute(text(f"SELECT * FROM boats where {whereStatement}")).all()
    print("boats", boats)
    
    return render_template('boat_filtered.html', form_data=form_data, boats=boats)


@app.route('/boats/id/<id>') # declaring the variable here changes the datatype 
def get_request(id):
    boat = conn.execute(text(f'SELECT * from boats where boatID = "{id}"'))
    print(type(boat))
    return  render_template('boat_request.html', boats=boat)
# Flask checks both the URL and the HTTP method.
# GET /create runs when the user visits the page in the browser.
# This is usually used to SHOW a page or form, not to save changes.
@app.route('/create', methods=['GET'])
def create_get_request():
    return render_template('boats_create.html')


# POST /create runs when the form is submitted with method="post".
# POST is usually used to SEND data to the server so something can be created, updated, or deleted.
# Unlike GET, POST form data is sent in the request body instead of being placed in the URL.
# After a POST finishes, the browser stays on the POST response unless you explicitly redirect.
# If you want the user to end up back on a GET page, return redirect(url_for(...)) after processing.
@app.route('/create', methods=['POST'])
def create_boat():
    # you can access the values with request.from.name
    # this name is the value of the name attribute in HTML form's input element
    # ex: print(request.form['id'])
    # request.form is the submitted HTML form data.
    # Each form input's name becomes a key, and what the user typed becomes the value.
    try:
        
        conn.execute(
            text("INSERT INTO boats values (:id, :name, :type, :owner_id, :rental_price)"), #these are variables with the name coming after the ':' # these come from the form element in the html file
            request.form
        )
        # conn.commit() saves the database change permanently.
        # This is a database commit, not a Git or GitHub commit.
        # Without conn.commit(), the new row may not actually be saved in the database.
        conn.commit()
        return render_template('boats_create.html', error=None, success="Data inserted successfully!")
    except Exception as e: # an error can occur if there is a duplicate primary key and in that scenario this section runs
        error = e.orig.args[1]
        print(error)
        return render_template('boats_create.html', error=error, success=None)

# Same URL idea here:
# GET /delete shows the page and the form.
# POST /delete receives the submitted form data and processes the deletion.
# The browser does not automatically switch back to GET after POST unless the code returns a redirect.
@app.route('/delete', methods=['GET'])  # Runs when the user visits /delete and shows the delete form.
def delete_get_request():
    return render_template('boats_delete.html')


@app.route('/delete', methods=['POST'])  # Runs when the user submits the delete form and processes the deletion.
def delete_boat():
    
    try:
        boat = conn.execute(
            text("select * FROM boats WHERE BoatID = :id"), # changed from id to BoatID becuase that is how it is in my database but :id is the same becuase it comes from the request.form
            request.form # this is the form element in the html file
        ).first()
        # .first() returns the first matching row, or None if no row exists.
        if boat is None:
            # Raising ValueError stops the try block immediately and jumps to except below.
            raise ValueError("Record not found")
        # request.form here contains the values submitted from the delete form.
        conn.execute(
            text("DELETE FROM boats WHERE BoatID = :id"), # changed from id to BoatID(inside of where clause) becuase that is how it is in my database but :id is the same becuase it comes from the request.form
            request.form # this is the form element in the html file
        )
        conn.commit()
        return render_template('boats_delete.html', error=None, success="Data deleted successfully!")
    except Exception as e:
        # This catches both database errors and the ValueError raised above.
        error = e.orig.args[1] if hasattr(e, "orig") else str(e)
        print(error)
        
        return render_template('boats_delete.html', error=error, success=None)
# make a route method for 'boats/id/<int: id>

# this will run when the user first goes to the update page and handles the request to take the form request
@app.route('/update', methods=['GET'])
def update_boat_request():
    return render_template('boats_update.html')

@app.route('/update', methods=['POST'])
def update_boat():
    try:        
        conn.execute(
            text("INSERT INTO boats values (:id, :name, :type, :owner_id, :rental_price)"), #these are variables with the name coming after the ':' # these come from the form element in the html file
            request.form
        )
        
    except Exception as e:
        # This catches both database errors and the ValueError raised above.
        error = e.orig.args[1] if hasattr(e, "orig") else str(e)
        print(error)
        
        return render_template('boats_update.html', error=error, success=None)
    return render_template('boats_update.html')
if __name__ == '__main__':
    app.run(debug=True)
