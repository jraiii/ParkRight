from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import Base, Slot

engine = create_engine('sqlite:///database.db')
Session = sessionmaker(bind=engine)
db_session = Session()

# Ensure tables exist
Base.metadata.create_all(engine)

# Add sample slots
slots = ["A1", "A2", "B1", "B2", "C1"]
for name in slots:
    if not db_session.query(Slot).filter_by(name=name).first():
        db_session.add(Slot(name=name))

db_session.commit()
print("Seeded slots:", slots)
