from flask import Flask,redirect,url_for,render_template,request,session,send_from_directory
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import update,text,or_
from sqlalchemy.orm import joinedload
from models import *
from utility import *
import os




app=Flask(__name__)

file_upload = os.path.join(os.getcwd(), 'appBooks')
app.config["SECRET_KEY"]="anythingworksherefornow"
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///database.db"
app.config['FILE_UPLOAD'] = file_upload


db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signin",methods=["GET","POST"])
def signin():
    if request.method=="GET":
        return render_template("signin.html")
    
    elif request.method=="POST":
        if "userID" in session:
            session.clear()
        username=request.form.get("username")
        userpassword=request.form.get("userpassword")        
        signinerror=""
        passworderror=""
        if username=="":
            signinerror="Email Required"
        if userpassword=="":
            passworderror="Password Required"
        if signinerror or passworderror:
            return render_template("signin.html",signinerror=signinerror,passworderror=passworderror,username=username,password=userpassword)
        else:
            user= User.query.filter_by(email = username).first()
            session["userID"] = user.id
            session["user_type"] = user.type
            if session["user_type"] == "student":
                return redirect(url_for('studentDashboard'))
            else:
                return redirect(url_for('librarianDashboard'))

@app.route("/student/read")
@login_required
def student_read():
    
    books=Book.query.all()
    if "user_type" in session:
        user_type = session["user_type"]
    else:
        user_type = None
    issues=Issue_Request.query.filter(Issue_Request.user_id==session["userID"],Issue_Request.status=="Book Issued").all()
    user_issues={}
    for issue in issues:
        user_issues[issue.book_id]=issue
    print(user_issues)
    success_msg = session.get('successMsg', None)
    error_msg = session.get('errorMsg', None)
    if request.method == "GET":
        search_query = request.args.get("search_query")
        if search_query:
            # Filter books based on search query
            books = Book.query.filter(or_(Book.name.ilike(f"%{search_query}%"))).all()
    return render_template("lib_display.html", books=books, user_type=user_type, errorMsg=error_msg, successMsg=success_msg, user_issues=user_issues,session=session)



@app.route("/librarian/dashboard")
@login_required
@is_user("librarian")
def librarianDashboard():
    user_type = session.get("user_type")
    if user_type == "librarian":
        user = User.query.filter_by(id=session["userID"]).first()
        if user:
            return render_template('librarian_dashboard.html', user=user.firstname, user_type=user_type)
        else:
            return "User not found."
    else:
        return "Unauthorized access."


@app.route('/issue-book/<string:book_id>')
@login_required
def book_issue(book_id):
    book = Book.query.filter_by(id=book_id).first()
    if book:
        book_id = book.id
        user_id = session["userID"]
        user_type = session["user_type"]
        issue_duration = 7
        issue = Issue_Request.query.filter(Issue_Request.user_id == user_id, Issue_Request.book_id == book_id).order_by(desc(Issue_Request.request_date)).first()

        if user_type == "librarian":
            if not issue:
                session['successMsg'] = "Issued Book: " + book.name
                req_date = db.func.datetime(db.func.current_timestamp(), '+5 Hours', '+30 Minutes')
                issue_date = db.func.datetime(db.func.current_timestamp(), '+5 Hours', '+30 Minutes')
                return_date = db.func.datetime(db.func.current_timestamp(), '+7 Days', '+5 Hours', '+30 Minutes')
                issue = Issue_Request(book_id=book_id, user_id=user_id, request_date=req_date, issue_date=issue_date, return_date=return_date, issue_period=issue_duration, status="Book Issued")
                db.session.add(issue)
                db.session.commit()

           # elif issue.status=="Returned":
           #     session['successMsg'] = "Book returned: " + book.name
            elif issue.status=="Book Issued":
                session["errorMsg"]="Already Issued: "+ book.name
            
            return redirect(url_for('lib_display'))

        elif user_type == "student":
            if not issue:
                session['successMsg'] = "Requested: " + book.name
                req_date = db.func.datetime(db.func.current_timestamp(), '+5 Hours', '+30 Minutes')
                issue = Issue_Request(book_id=book_id, user_id=user_id, request_date=req_date, issue_period=issue_duration, status="Requested")
                db.session.add(issue)
                db.session.commit()
            elif issue.status == "Requested":
                session['successMsg'] = "Already requested: " + book.name
            elif issue.status == "Rejected":
                session['errorMsg'] = "Request has been Rejected: " + book.name
            elif issue.status == "Revoked":
                session['errorMsg'] = "Access has been Revoked: " + book.name
                
            elif issue.status=="Book Issued":
                session['errorMsg'] = "Already Issued: " + book.name
            
            return redirect(url_for('student_read'))

    else:
        session['errorMsg'] = "The book ID provided is not valid: " + book_id
        
        return redirect(url_for('lib_display' if session["user_type"]=="librarian" else "student_read"))
    
@app.route('/return-book/<string:book_id>')
@login_required
def book_return(book_id):
    book = Book.query.filter_by(id=book_id).first()
    
    if not book:
        session['errorMsg'] = "Invalid Book ID: "+ book_id
        return redirect(url_for('lib_display' if session['user_type'] == "librarian" else 'student_read'))
    bookID = book.id
    issue = Issue_Request.query.filter(Issue_Request.book_id == bookID, Issue_Request.user_id==session['userID']).first()
    if issue.status == "Book Issued":
        issue.status = "Returned"
        db.session.commit()
        session['successMsg'] = "Book returned: "+ book.name
        return redirect(url_for('lib_display' if session['user_type'] == "librarian" else 'student_read'))
    else:
        session['errorMsg'] = "Un-Issued Book: "+ book.name
        return redirect(url_for('lib_display' if session['user_type'] == "librarian" else 'student_read'))
    
@app.route("/requests")
@login_required
@is_user("librarian")
def request_config():
    user = User.query.filter_by(id=session["userID"]).first()
    
    if user:
        if request.method == "GET":
            issue_req = Issue_Request.query.all()
            all_users = User.query.all()
            all_books = Book.query.all()

            users = {user.id: user for user in all_users}
            books = {book.id: book for book in all_books}

            success_msg = session.pop('successMsg', None)
            error_msg = session.pop('errorMsg', None)

            return render_template('requests.html', user=user, issue_req=issue_req, users=users, books=books, successMsg=success_msg, errorMsg=error_msg)
    else:
        return "User not found."
    
@app.route("/read_disp/<string:book_name>")
@login_required
def read_disp(book_name):
    d={}
    book=Book.query.filter_by(name=book_name).first()
    genres=[genre.name for genre in Genre.query.join(Book_Genre).filter(Book_Genre.book_id==book.id).all()]
    authors=[author.name for author in Author.query.join(Book_Author).filter(Book_Author.bk_id==book.id).all()]
    
    success_msg = session.pop('successMsg', None)
    error_msg = session.pop('errorMsg', None)
    
    feedbacks=Feedback.query.filter_by(book_id=book.id).all()
    for fb in feedbacks:
        d[fb.user_id]=User.query.filter_by(id=fb.user_id).first().firstname
    print(genres)
    print(authors)

    return render_template('read_display.html',book_name=book_name,successMsg=success_msg,errorMsg=error_msg,feedbacks=feedbacks,d=d,genres=genres,authors=authors)

@app.route("/read_display/<string:book_name>")
@login_required
def read_pdf(book_name):
    # Assuming 'books_folder' is the directory where your books are stored
    books_folder = "appBooks"
    # Construct the path to the PDF file
    pdf_path = os.path.join(books_folder)
    # Send the PDF file as a response
    return send_from_directory(books_folder, book_name+".pdf")
    
@app.route("/feedback/<string:book_name>", methods=["POST"])
def receive_feedback(book_name):
    if request.method == 'POST':
        comments = request.form.get('comments')
        book=Book.query.filter_by(name=book_name).first()
        print(comments)
        print(book.name)

        # Validate if comments field is not empty
        if comments=="":
            session['errorMsg']="Feedback can't be empty"
            return redirect(request.referrer)
            

        # Create a new Feedback object and add it to the database
        feedback = Feedback(user_id=session["userID"],book_id=book.id,comments=comments)
        db.session.add(feedback)
        db.session.commit()
       
        session['successMsg']="Feedback submitted successfully!"
        return redirect(request.referrer)


@app.route("/request-action/<string:issue_id>/<string:action>")
@login_required
@is_user("librarian")
def request_action(issue_id, action):
    issue = Issue_Request.query.filter_by(id=issue_id).first()

    if not issue:
        session["errorMsg"] = "Issue ID doesn't exist!"
        return redirect(url_for('request_config'))

    if action == "issue" and issue.status == "Requested":
        update_stmt = update(Issue_Request).where(Issue_Request.id == issue_id).values(
            issue_date=db.func.datetime(db.func.current_timestamp(), '+5 Hours', '+30 Minutes'),
            return_date=db.func.datetime(db.func.current_timestamp(), '+7 Days', '+5 Hours', '+30 Minutes'),
            status="Book Issued"
        )
        db.session.execute(update_stmt)
        db.session.commit()
        session["successMsg"] = "Issued Successfully"
    elif action == "reject" and issue.status == "Requested":
        issue.status = "Rejected"
        db.session.commit()
        session["successMsg"] = "Request Rejected!"
    elif action == "revoke" and issue.status == "Book Issued":
        issue.status = "Revoked"
        db.session.commit()
        session["successMsg"] = "Revoked Book Access Successfully."
    elif action == "reissue" and issue.status in ["Revoked", "Returned", "Rejected"]:
        update_stmt = update(Issue_Request).where(Issue_Request.id == issue_id).values(
            issue_date=db.func.datetime(db.func.current_timestamp(), '+5 Hours', '+30 Minutes'),
            return_date=db.func.datetime(db.func.current_timestamp(), '+7 Days', '+5 Hours', '+30 Minutes'),
            status="Book Issued"
        )
        db.session.execute(update_stmt)
        db.session.commit()
        session["successMsg"] = "Book has been Re-Issued!"
    elif action == "remove" and issue.status in ["Revoked", "Returned", "Rejected"]:
        db.session.delete(issue)
        db.session.commit()
        session["successMsg"] = "Deleted!"
    else:
        session["errorMsg"] = "Invalid action for the current status!"

    return redirect(url_for('request_config'))

                

@app.route("/student/dashboard")
@login_required
@is_user("student")
def studentDashboard():
    try:
        user = User.query.filter_by(id=session["userID"]).first()
        if user:
            return render_template('student_dashboard.html', user=user.firstname)
        else:
            raise Exception("User not found.")
    except KeyError:
        return "User ID not found in session."



@app.route('/signout')
@login_required
def signout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/requests")
def requests():
    return render_template("requests.html") 


@app.route("/librarian/register",methods=["GET","POST"])   
def librarian_register():
    if request.method=="GET":
        return render_template("librarian_registration.html")
    
    elif request.method=="POST":
        firstname=request.form.get("firstname")
        lastname=request.form.get("lastname")
        email=request.form.get("email")
        password=request.form.get("password")
        confirm_password=request.form.get("confirm_password")
        passcode = request.form.get("passcode")

        firstnameerror=""
        emailerror=""
        passworderror=""
        confirmpassworderror=""
        passcodeError=""

        user=User.query.filter_by(email=email).first()
        duplicate_flag=False
        if user:
            duplicate_flag=True
        

        if firstname == "":
            firstnameerror = "Name Required"
          
        
        if email == "":
            emailerror = "Email Required"
        
        elif duplicate_flag:
            emailerror="Username already exists"
            

        if password=="":
            passworderror="Password Required!"

           

        elif confirm_password=="":
            confirmpassworderror="Confirm password required"
            
        
        elif password!=confirm_password:
            confirmpassworderror="Password doesn't match"
            
        if passcode=="":
            passcodeError="This field cannot be empty."
        elif passcode!="mangoman":
            passcodeError="Invalid passcode"

        if firstnameerror or passworderror or emailerror or confirmpassworderror or passcodeError:
             return render_template("librarian_registration.html",
                                firstname=firstname,
                                lastname=lastname,
                                email=email,
                                password=password,
                                confirm_password=confirm_password,
                                confirmpassworderror=confirmpassworderror, 
                                firstnameerror=firstnameerror,
                                emailerror=emailerror,
                                passworderror=passworderror,
                                passcodeError=passcodeError)
        else:
            if lastname=="":
                lastname=None
            user=User(firstname=firstname,
                      lastname=lastname,
                      email=email,
                      password=generate_password_hash(password),
                      type="librarian")
            db.session.add(user)
            db.session.commit()

            return redirect("/signin")

@app.route("/books")
@login_required
def lib_display():
    books=Book.query.all()
    if "user_type" in session:
        user_type = session["user_type"]
    else:
        user_type = None
    
    issues=Issue_Request.query.filter(Issue_Request.user_id==session["userID"],Issue_Request.status=="Book Issued").all()
    user_issues=[issue.book_id for issue in issues]
    #user_issues={}
    #for issue in issues:
    #    user_issues[issue.book_id]=issue
    #print(user_issues)
    success_msg = session.get('successMsg', None)
    error_msg = session.get('errorMsg', None)
    return render_template("lib_display.html", books=books, user_type=user_type, errorMsg=error_msg, successMsg=success_msg, user_issues=user_issues,session=session)




@app.route('/search_genre/<string:genre>')
def search_books_by_genre(genre):
    user_type = session["user_type"]
    genre_id_query = text("SELECT id FROM genre WHERE name = :genre_name")
    issues=Issue_Request.query.filter_by(user_id=session["userID"]).all()
    user_issues={}
    for issue in issues:
        user_issues[issue.book_id]=issue
    with db.engine.connect() as connection:
        genre_id = connection.execute(genre_id_query, {"genre_name": genre}).fetchone()[0]
    books_query = text("""
        SELECT book.*
        FROM book
        JOIN book_genre ON book.id = book_genre.book_id
        WHERE book_genre.genre_id = :genre_id
    """)
    with db.engine.connect() as connection:
        books = connection.execute(books_query, {"genre_id": genre_id}).fetchall()
    return render_template("lib_display.html", books=books, user_type=user_type,user_issues=user_issues)


@app.route('/search_author/<string:author>')
def search_books_by_author(author):
    user_type = session["user_type"]
    author_id_query = text("SELECT id FROM author WHERE name = :author_name")
    issues=Issue_Request.query.filter_by(user_id=session["userID"]).all()
    user_issues={}
    for issue in issues:
        user_issues[issue.book_id]=issue
    author_id = db.session.execute(author_id_query, {"author_name": author}).fetchone()[0]
    books_query = text("""
        SELECT book.*
        FROM book
        JOIN book_auth ON book.id = book_auth.bk_id
        WHERE book_auth.author_id = :author_id
    """)
    books = db.session.execute(books_query, {"author_id": author_id}).fetchall()
    return render_template("lib_display.html", books=books, user_type=user_type,user_issues=user_issues)


@app.route('/delete/<string:book_id>')
def delete_book(book_id):
    delete_book_query = text("DELETE FROM book WHERE id = :book_id")
    delete_genre_query = text("DELETE FROM book_genre WHERE book_id = :book_id")
    delete_author_query = text("DELETE FROM book_auth WHERE bk_id = :book_id")
    db.session.execute(delete_genre_query, {"book_id": book_id})
    db.session.execute(delete_author_query, {"book_id": book_id})
    db.session.execute(delete_book_query, {"book_id": book_id})
    db.session.commit()
    return redirect(url_for('lib_display'))

@app.route('/addBooks', methods=['GET', 'POST'])
@login_required
@is_user("librarian")
def addBooks():
    if request.method == "GET":
        genres = [genre.name for genre in Genre.query.with_entities(Genre.name).all()]
        return render_template("addBooks.html", genres=genres)
    elif request.method == "POST":
        fetch_title = request.form.get("bookName")
        fetch_auth = request.form.get("authorName")
        fetch_genre = request.form.get('selectedGenres')
        fetch_description = request.form.get("description")
        file = request.files.get('file')

        if 'file' in request.files:
            file = request.files['file']
            print("filename: "+file.filename)
        else:
            file = None

        return adding_books_via_form(app=app, fetch_title=fetch_title, fetch_auth=fetch_auth, fetch_genre=fetch_genre, fetch_description=fetch_description, file=file)





@app.route("/genres", methods=["GET", "POST"])
@login_required
def genres():
    user_type=session["user_type"]

    if request.method == "GET":
        search_query = request.args.get("search_query")
        
        if search_query:
            # Filter genres based on search query
            genres = Genre.query.filter(or_(Genre.name.ilike(f"%{search_query}%"))).all()
            genreList=[g.name for g in genres]
            return render_template("genres.html", listGen=genreList, search_query=search_query, user_type=user_type ,url=url_for('genres'))
        else:
            # Fetch all genres if no search query is provided
            genres = Genre.query.all()
            genreList=[g.name for g in genres]
            return render_template("genres.html", listGen=genreList, user_type=user_type,url=url_for('genres'))
        #listGenre= Genre.query.with_entities(Genre.name).all()
        #genreList=[name for (name,) in listGenre]
        #return render_template("genres.html",listGen=genreList,user_type=user_type)
    
    elif request.method == "POST":
        button = request.form.get("action")
        text=remove_multiple_spaces(request.form.get("textfield")).title()
        genError=""
        verMsg=""
        if button == "add":
            if text=="":
                genError="Field Required,can't be empty."
            else:
                g=Genre.query.filter_by(name=text).first()
                if g:
                    genError="Genre already exists."
                else:
                    g=Genre(name=text)
                    db.session.add(g)
                    db.session.commit()
                    verMsg=text+" added."

        elif(button=="remove"):
            if(text==""):
                genError="Field Required."
            else:
                g=Genre.query.filter_by(name=text).first()
                if (not g):
                    genError="Genre doesn't exist!"
                else:
                    verMsg=text+" delete"
                    db.session.delete(g)
                    db.session.commit()

        listGenre= Genre.query.with_entities(Genre.name).all()
        genreList=[name for (name,) in listGenre] 
        print(genreList)
        return render_template('genres.html',genError=genError,verMsg=verMsg,listGen=genreList,user_type=user_type)   

@app.route("/authors", methods=["GET", "POST"])
@login_required
def authors():
    user_type=session["user_type"]
    if request.method == "GET":
        search_query = request.args.get("search_query")
        
        if search_query:
            # Filter genres based on search query
            authors = Author.query.filter(or_(Author.name.ilike(f"%{search_query}%"))).all()
            authorList=[a.name for a in authors]
            return render_template("authors.html", listAuthor=authorList, search_query=search_query, user_type=user_type ,url=url_for('authors'))
        else:
            # Fetch all genres if no search query is provided
            authors = Author.query.all()
            authorList=[a.name for a in authors]
            return render_template("authors.html", listAuthor=authorList, user_type=user_type,url=url_for('authors'))
        #listGenre= Genre.query.with_entities(Genre.name).all()
        #genreList=[name for (name,) in listGenre]
        #return render_template("genres.html",listGen=genreList,user_type=user_type)
    elif request.method == "POST":
        button = request.form.get("action")
        text=remove_multiple_spaces(request.form.get("textfield")).title()
        authError=""
        verMsg=""
        if button == "add":
            if text=="":
                authError="Field Required,can't be empty."
            else:
                g=Author.query.filter_by(name=text).first()
                if g:
                    authError="Author already exists."
                else:
                    g=Author(name=text)
                    db.session.add(g)
                    db.session.commit()
                    verMsg=text+" added."

        elif(button=="remove"):
            if(text==""):
                authError="Field Required."
            else:
                g=Author.query.filter_by(name=text).first()
                if (not g):
                    authError="Author doesn't exist!"
                else:
                    verMsg=text+" delete"
                    db.session.delete(text)
                    db.session.commit()
        listAuthor= Author.query.with_entities(Author.name).all()
        genreList=[name for (name,) in listAuthor] 
        
        return render_template('authors.html',authError=authError,verMsg=verMsg,listAuthor=genreList,user_type=user_type)   


@app.route("/genre-delete/<string:genre>")
@login_required
@is_user("librarian")
def delGenre(genre):
    delete_query = text("DELETE FROM genre WHERE name = :genre_name")
    db.session.execute(delete_query, {"genre_name": genre})
    db.session.commit()
    return redirect(url_for('genres'))


@app.route("/author-delete/<string:author>")
@login_required
@is_user("librarian")
def delAuthor(author):
    delete_query = text("DELETE FROM author WHERE name = :author_name")
    db.session.execute(delete_query, {"author_name": author})
    db.session.commit()
    return redirect(url_for('authors'))

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html") 

@app.route("/register",methods=["GET","POST"])    
def register():
    if request.method=="GET":
        return render_template("register.html")
    
    elif request.method=="POST":
        firstname=request.form.get("firstname")
        lastname=request.form.get("lastname")
        email=request.form.get("email")
        password=request.form.get("password")
        confirm_password=request.form.get("confirm_password")

        firstnameerror=""
        emailerror=""
        passworderror=""
        confirmpassworderror=""

        user=User.query.filter_by(email=email).first()
        duplicate_flag=False
        if user:
            duplicate_flag=True
        

        if firstname == "":
            firstnameerror = "Name Required"
          
        
        if email == "":
            emailerror = "Email Required"
        
        elif duplicate_flag:
            emailerror="Username already exists"
            

        if password=="":
            passworderror="Password Required!"
            

        elif confirm_password=="":
            confirmpassworderror="Confirm password required"
            
        
        elif password!=confirm_password:
            confirmpassworderror="Password doesn't match"
            


        if firstnameerror or passworderror or emailerror or confirmpassworderror:
             return render_template("register.html",
                                firstname=firstname,
                                lastname=lastname,
                                email=email,
                                password=password,
                                confirm_password=confirm_password,
                                confirmpassworderror=confirmpassworderror, 
                                firstnameerror=firstnameerror,
                                emailerror=emailerror,
                                passworderror=passworderror)
        else:
            if lastname=="":
                lastname=None
            user=User(firstname=firstname,
                      lastname=lastname,
                      email=email,
                      password=generate_password_hash(password),
                      type="student")
            db.session.add(user)
            db.session.commit()

            return redirect("/signin")


if __name__ == "__main__":
    app.run(debug = True) 

