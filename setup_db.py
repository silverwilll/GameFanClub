import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine  
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=True)
    email = Column(String(250), nullable=True)
    picture = Column(String(250))
    level = Column(Integer, default=3)

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=True)
    description = Column(String(250), nullable=True)
    img_url = Column(String(250))
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    user = relationship(User)

class Game(Base):
    __tablename__ = 'game'


    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=True)
    year = Column(String(50))
    image_url = Column(String(250))
    description = Column(String(500))
    trailer_url = Column(String(250))
    genre = Column(String(250), nullable=True)
    developer = Column(String(250))
    rate = Column(String(50))
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    user = relationship(User)

    @property
    def serialize(self):
        #Return object data in serializable format
        return {
            'name' : self.name,
            'id' : self.id,
            'description' : self.description,
            'year' : self.year,
            'genre' : self.genre,
            'developer' : self.developer,
            'rate' : self.rate,
            'creator_id' : self.creator_id,
            'image_url' : self.image_url,
            'trailer_url' : self.trailer_url,
        }

engine = create_engine('sqlite:///GameFan.db')
Base.metadata.create_all(engine)
