import os
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Connection string from user
DATABASE_URL = "postgresql://neondb_owner:npg_aqznhH0k4BJp@ep-lively-heart-add7hxf1-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

Base = declarative_base()

class PostedEvent(Base):
    __tablename__ = 'posted_events'
    event_id = Column(String, primary_key=True) # e.g., "match123_goal_23"
    event_type = Column(String)
    caption = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialize the Neon database tables."""
    Base.metadata.create_all(engine)

def is_event_posted(event_id):
    """Check if a specific event has already been posted to FB."""
    session = SessionLocal()
    exists = session.query(PostedEvent).filter(PostedEvent.event_id == event_id).first() is not None
    session.close()
    return exists

def mark_event_posted(event_id, event_type, caption):
    """Mark an event as posted in the database."""
    session = SessionLocal()
    new_event = PostedEvent(event_id=event_id, event_type=event_type, caption=caption)
    session.add(new_event)
    session.commit()
    session.close()
