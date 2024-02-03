from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()

class Favourites(db.Model):
    __tablename__="favourites"
    bk_id=db.Column(db.Integer(),db.ForeignKey('books.id'),primary_key=True)
    user_id=db.Column(db.Integer(),db.ForeignKey('user.id'),primary_key=True)


class Book_Author(db.Model):
    __tablename__="Book_auth"
    bk_id=db.Column(db.Integer,db.ForeignKey('books.id'),primary_key=True)
    author_id=db.Column(db.Integer(),db.ForeignKey('author.id'),primary_key=True)


class User(db.Model):
    __tablename__="user"
    id=db.Column(db.Integer(),primary_key=True)
    firstname=db.Column(db.String(),nullable=False)
    lastname=db.Column(db.String())
    email=db.Column(db.String(),nullable=False,unique=True)
    password=db.Column(db.String(),nullable=False)
    type=db.Column(db.String(),nullable=False)
    favourites=db.relationship('Book',secondary='favourites',backref='user')

class Books(db.Model):
    __tablename__="books"
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String(),nullable=False)
    content=db.Column(db.String())
    authors = db.relationship('Author',secondary = 'book_auth',backref = 'book')
    likes = db.relationship('User',secondary='favorites',backref='book')

class Author(db.Model):
    __tablename__="author"
    id = db.Column(db.Integer(),primary_key = True)
    name = db.Column(db.String(),nullable = False)
    books = db.relationship('Book',secondary = 'book_auth',backref = 'author')
