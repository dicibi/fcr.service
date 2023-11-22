from sqlalchemy import create_engine

def getEngine():
    return create_engine("sqlite:///db/fcr.sqlite", echo=True)
