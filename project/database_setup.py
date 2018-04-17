from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)
    email = Column(String(250), nullable = False)
    picture = Column(String(250))


class RecentSearch(Base):
    __tablename__ = 'recentsearch'

    id = Column(Integer, primary_key=True)
    search = Column(String(100), nullable=False)
    location = Column(String(300), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


engine = create_engine('sqlite:///restaurant_data.db')


Base.metadata.create_all(engine)
