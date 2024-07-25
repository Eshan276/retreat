import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Import your Retreat model and db object from your main app file
from main import Retreat, db

# Load the JSON data
with open('retreats_data.json', 'r') as file:
    retreats_data = json.load(file)

# Create a database engine and session
engine = create_engine(
    'postgresql://retreats_owner:ZO3E8CJMAxhH@ep-gentle-pond-a1frw6yn.ap-southeast-1.aws.neon.tech/retreats?sslmode=require')
Session = sessionmaker(bind=engine)
session = Session()

# Function to convert Unix timestamp to datetime


def unix_to_datetime(unix_time):
    return datetime.fromtimestamp(unix_time)


# Populate the database
for retreat_data in retreats_data:
    retreat = Retreat(
        id=retreat_data['id'],
        title=retreat_data['title'],
        description=retreat_data['description'],
        location=retreat_data['location'],
        price=float(retreat_data['price']),
        duration=retreat_data['duration'],
        date=unix_to_datetime(retreat_data['date']),
        type=retreat_data['type'],
        condition=retreat_data['condition'],
        image=retreat_data['image'],
        # Store tags as comma-separated string
        tag=retreat_data['tag']
    )
    session.add(retreat)

# Commit the changes
session.commit()

print("Database populated successfully!")

# Close the session
session.close()
