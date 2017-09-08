from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from setup_db import Base, Category, Game, User

engine = create_engine('sqlite:///GameFan.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a 'staging zone' for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

category1 = Category(name='rpg', description='Classic Role Play Game', img_url='https://i.pinimg.com/564x/47/6f/d2/476fd20e9aa6ef387d7fd4f5daf579d5.jpg')
category2 = Category(name='strategy', description='Needs Thinking', img_url='http://en.wikipedia.org/wiki/Civilization_V')

session.add(category1)
session.commit()
session.add(category2)
session.commit()

game1 = Game(name='AAA', year='1999', description='AFFJDKDFFF', trailer_url='http://google.com', genre='rpg')
game2 = Game(name='BBB', year='1999', description='AFFJDKDFFF', trailer_url='http://google.com', genre='strategy')

session.add(game1)
session.commit()
session.add(game2)
session.commit()