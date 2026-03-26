from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import Base, Ticket, Slot

engine = create_engine('sqlite:///database.db')
Session = sessionmaker(bind=engine)
db_session = Session()

# Ensure tables exist
Base.metadata.create_all(engine)

# Delete all tickets but keep slots
deleted_count = db_session.query(Ticket).delete()
db_session.commit()

print(f"Deleted {deleted_count} tickets. Slots remain intact.")
