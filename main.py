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

# Flask checks both the URL and the HTTP method.
# GET /create happens when a user visits the page, so this route shows the form.
@app.route('/create', methods=['GET'])
def create_get_request():
    return render_template('boats_create.html')


# POST /create happens when that form is submitted with method="post",
# so this route receives the form data and saves it.
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
    except Exception as e:
        error = e.orig.args[1]
        print(error)
        return render_template('boats_create.html', error=error, success=None)

# Same URL idea here:
# GET /delete shows the delete form, while POST /delete processes the submitted data.
@app.route('/delete', methods=['GET'])  # Runs when the user visits /delete and shows the delete form.
def delete_get_request():
    return render_template('boats_delete.html')


@app.route('/delete', methods=['POST'])  # Runs when the user submits the delete form and processes the deletion.
def delete_boat():
    try:
        # request.form here contains the values submitted from the delete form.
        conn.execute(
            text("DELETE FROM boats WHERE BoatID = :id"), # changed from id to BoatID becuase that is how it is in my database but :id is the same becuase it comes from the request.form
            request.form # this is the form element in the html file
        )
        return render_template('boats_delete.html', error=None, success="Data deleted successfully!")
    except Exception as e:
        error = e.orig.args[1]
        print(error)
        conn.commit()
        return render_template('boats_delete.html', error=error, success=None)
# make a route method for 'boats/id/<int: id>

if __name__ == '__main__':
    app.run(debug=True)
