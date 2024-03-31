from flask import redirect,url_for,session,render_template,request
from sqlalchemy.orm.exc import NoResultFound
from functools import wraps
import re
from models import *
import os
import fitz


def login_required(f):
    @wraps(f)
    def wrapper(*args,**kwargs):
        if "userID" in session:
            return f(*args,**kwargs)
        else:
            return redirect(url_for('home'))
    return wrapper

def is_user(expectedType):
    def decorator(f):
        @wraps(f)
        def wrapper(*args,**kwargs):
            if "userID" in session:
                if session["user_type"] == expectedType:
                    return f(*args,**kwargs)
            return redirect(url_for('home'))
        return wrapper
    return decorator


def remove_multiple_spaces(text):
    cleaned_text = re.sub(r'\s+', ' ', text)
    return cleaned_text

def adding_books_via_form(app,fetch_title,fetch_auth,fetch_genre,fetch_description,file):
    genresQuery = Genre.query.with_entities(Genre.name).all()
    allGenres = [name for (name,) in genresQuery]
    authorsQuery = Author.query.with_entities(Author.name).all()
    allAuthors = [name for (name,) in authorsQuery]
    
    titleError=""
    authorsError=""
    fileError=""
    genreError=""
    descriptionError=""


    if(fetch_title == ""):
            titleError="Title can not be empty!"
            print(titleError)
    else:
        title =remove_multiple_spaces(fetch_title).title()
        book = Book.query.filter_by(name=title).first()
        print("Adding new book")
        if book:
            titleError="This title already exists!"
            print(titleError)
    if fetch_auth=="":
        authorsError="You need to add at least 1 Author"
    else:
        fetch_auth = [author.strip() for author in remove_multiple_spaces(fetch_auth).title().split(sep=",")]
        print(fetch_auth)
        for name in fetch_auth:
            author = Author.query.filter_by(name=name).first()
            if not author:
            # Author doesn't exist, so add it to the list to be added to the database
                new_author = Author(name=name)
                db.session.add(new_author)
                db.session.commit()
                print("authos: "+name)

    if fetch_genre=="":
        genreError="Genre field can't be empty"

    else:
        print(fetch_genre)
        print("yolo")
        fetch_genre = [genre.strip() for genre in remove_multiple_spaces(fetch_genre).title().split(sep=",")]
        for genre_name in fetch_genre:
            print(genre_name)
            
            genre =Genre.query.filter_by(name=genre_name).first()
            print(genre)
            if not genre:
                genreError="Invalid genre! "+ genre_name
                    
    if fetch_description=="":
        descriptionError="Description field can't be empty!"
        
        

    if file.filename=="":
        fileError="Please select a file."
        
    print("printing all errors :- ")
    print(fileError,descriptionError,authorsError,genreError,titleError)
    if not(fileError or descriptionError or authorsError or genreError or titleError):
    
        ext='.pdf'
        file_path=os.path.join(app.config['FILE_UPLOAD'], title)
        file.save(file_path+ext)
        print("file saved")

        open_book=fitz.open(file_path+ext)
        book_cover=fitz.Pixmap(open_book,open_book[0].get_images()[0][0])
    
        if book_cover.n - book_cover.alpha > 3:
            book_cover = fitz.Pixmap(fitz.csRGB,book_cover)
        
        coverPath = os.path.join(app.static_folder,'bookcover_imgs', os.path.basename(file_path)+'.png')
        
        book_cover._writeIMG(coverPath,format_="png",jpg_quality=None)
        
        book_cover=None
        open_book.close()
        book=Book(name=title,content=fetch_description)
        db.session.add(book)
        db.session.commit()
        bookID = Book.query.filter_by(name=title).first().id

        for author in fetch_auth:
            print("prinitng bookid: ")
            print(bookID)
            author_id = Author.query.filter_by(name=author).first().id
            print(author_id)
            db.session.add(Book_Author(bk_id=bookID,author_id=author_id))
        db.session.commit()
        print(fetch_genre)
        for genre in fetch_genre:
            
            g = Book_Genre(book_id=bookID,genre_id=Genre.query.filter_by(name=genre).first().id)
            db.session.add(g)
        db.session.commit()
        return redirect(url_for('librarianDashboard'))


    return render_template('addBooks.html',title=fetch_title,genres=allGenres,desc=fetch_description,titleError=titleError,authorsError=authorsError,fileError=fileError,genreError=genreError,descError=descriptionError)