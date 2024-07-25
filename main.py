import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_cors import CORS
from sqlalchemy.dialects.postgresql import ARRAY
# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
# Use the environment variable for the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 'postgresql://retreats_owner:ZO3E8CJMAxhH@ep-gentle-pond-a1frw6yn.ap-southeast-1.aws.neon.tech/retreats?sslmode=require')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
# Define models


class Retreat(db.Model):
    __tablename__ = 'retreats'

    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime)
    location = db.Column(db.String(100))
    price = db.Column(db.Numeric(10, 2))
    type = db.Column(db.String(50))
    condition = db.Column(db.String(100))
    image = db.Column(db.String(255))
    tag = db.Column(ARRAY(db.String))
    duration = db.Column(db.Integer)


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    user_name = db.Column(db.String(255), nullable=False)
    user_email = db.Column(db.String(255), nullable=False)
    user_phone = db.Column(db.String(20))
    retreat_id = db.Column(db.String(50), db.ForeignKey('retreats.id'))
    retreat_title = db.Column(db.String(255))
    retreat_location = db.Column(db.String(255))
    retreat_price = db.Column(db.Numeric(10, 2))
    retreat_duration = db.Column(db.Integer)
    payment_details = db.Column(db.Text)
    booking_date = db.Column(db.Date, nullable=False)

    retreat = db.relationship(
        'Retreat', backref=db.backref('bookings', lazy=True))


# # Create tables
# db.create_all()


@app.route('/retreats', methods=['GET'])
def get_retreats():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    filter_param = request.args.get('filter', '')

    query = Retreat.query

    if search:
        query = query.filter(Retreat.title.ilike(
            f'%{search}%') | Retreat.description.ilike(f'%{search}%'))

    if location:
        query = query.filter(Retreat.location == location)

    if filter_param:
        query = query.filter(Retreat.condition.ilike(f'%{filter_param}%') |
                             Retreat.title.ilike(f'%{filter_param}%') |
                             Retreat.description.ilike(f'%{filter_param}%') |
                             Retreat.location.ilike(f'%{filter_param}%') |
                             Retreat.condition.ilike(f'%{filter_param}%'))

    retreats = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'retreats': [{'id': r.id, 'title': r.title, 'description': r.description, 'location': r.location, 'price': str(r.price), 'duration': r.duration, 'type': r.type, 'condition': r.condition, 'tags': r.tag, 'image': r.image} for r in retreats.items],
        'total': retreats.total,
        'pages': retreats.pages,
        'current_page': page
    })


@app.route('/book', methods=['POST'])
def book_retreat():
    data = request.json

    existing_booking = Booking.query.filter_by(
        user_id=data['user_id'],
        retreat_id=data['retreat_id']
    ).first()

    if existing_booking:
        return jsonify({'error': 'You have already booked this retreat'}), 400

    new_booking = Booking(
        user_id=data['user_id'],
        user_name=data['user_name'],
        user_email=data['user_email'],
        user_phone=data['user_phone'],
        retreat_id=data['retreat_id'],
        retreat_title=data['retreat_title'],
        retreat_location=data['retreat_location'],
        retreat_price=data['retreat_price'],
        retreat_duration=data['retreat_duration'],
        payment_details=data['payment_details'],
        booking_date=data['booking_date']
    )

    db.session.add(new_booking)
    db.session.commit()

    return jsonify({'message': 'Booking successful', 'booking_id': new_booking.id}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
