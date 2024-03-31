from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc,func
from datetime import datetime,timedelta
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


db=SQLAlchemy()

class Book_Author(db.Model):
    __tablename__="book_auth"
    bk_id=db.Column(db.Integer(),db.ForeignKey('book.id'),primary_key=True)
    author_id=db.Column(db.Integer(),db.ForeignKey('author.id'),primary_key=True)


class User(db.Model):
    __tablename__="user"
    id=db.Column(db.Integer(),primary_key=True)
    firstname=db.Column(db.String(),nullable=False)
    lastname=db.Column(db.String())
    email=db.Column(db.String(),nullable=False,unique=True)
    password=db.Column(db.String(),nullable=False)
    type=db.Column(db.String(),nullable=False)
    

class Book(db.Model):
    __tablename__="book"
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String(),nullable=False)
    content=db.Column(db.String())
    authors = db.relationship('Author',secondary = 'book_auth',backref = 'book')
    #likes = db.relationship('User',secondary='favourites',backref='book')
    genres = db.relationship('Genre',secondary = 'book_genre',backref = 'book')
    

class Author(db.Model):
    __tablename__="author"
    id = db.Column(db.Integer(),primary_key = True)
    name = db.Column(db.String(),nullable = False)
    books = db.relationship('Book',secondary = 'book_auth',backref = 'author')

class Genre(db.Model):
    __tablename__="genre"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

class Book_Genre(db.Model):
    __tablename__ = "book_genre"
    book_id = db.Column(db.Integer(),db.ForeignKey('book.id'),primary_key = True)
    genre_id = db.Column(db.Integer(),db.ForeignKey('genre.id'),primary_key = True)

class Issue_Request(db.Model):
    __tablname__="issue"
    id = db.Column(db.Integer(),primary_key = True)
    book_id = db.Column(db.Integer(),db.ForeignKey('book.id'),nullable=False)
    user_id = db.Column(db.Integer(),db.ForeignKey('user.id'),nullable=False)
    request_date = db.Column(db.DateTime(),nullable = False, default = db.func.current_timestamp())
    issue_date = db.Column(db.DateTime(),nullable = True)
    return_date = db.Column(db.DateTime(),nullable = True)
    issue_period = db.Column(db.Integer(),nullable = True)
    status = db.Column(db.String(),nullable = False,default = 'requested')

class Feedback(db.Model):
    __tablname__="feedback"
    id = db.Column(db.Integer(), primary_key=True)
    book_id = db.Column(db.Integer(), db.ForeignKey("book.id"), nullable=False)
    user_id = db.Column(db.Integer(),db.ForeignKey('user.id'),nullable=False)
    comments = db.Column(db.String(),nullable=False)