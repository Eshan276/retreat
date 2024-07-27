from sqlalchemy.sql import select
from sqlalchemy import and_, or_, func
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_cors import CORS
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import uuid
from sqlalchemy import case, select
from sqlalchemy import and_, or_, func
from sqlalchemy.sql import select
import sqlalchemy

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 'postgresql://retreats_owner:ZO3E8CJMAxhH@ep-gentle-pond-a1frw6yn.ap-southeast-1.aws.neon.tech/retreats')
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
    user_id = db.Column(db.String(255), nullable=False)
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

    booking_date = datetime.strptime(data['booking_date'], '%Y-%m-%d').date()

    retreat = Retreat.query.get(data['retreat_id'])
    if not retreat:
        return jsonify({'error': 'Retreat not found'}), 404
    retreat_duration_days = retreat.duration - 1
    print('retreat_duration_days', retreat_duration_days)
    end_date = booking_date + timedelta(days=retreat_duration_days)
    booking_dates = Booking.query.filter_by(
        retreat_id=data['retreat_id']).all()

    booking_dates_array = [int(booking.booking_date.strftime(
        '%Y%m%d')) for booking in booking_dates]
    print(booking_dates_array)
    fbooking_date = int(booking_date.strftime('%Y%m%d'))
    nearest_previous_booking = None
    nearest_next_booking = None

    for date in booking_dates_array:
        if date < fbooking_date:
            if nearest_previous_booking is None or date > nearest_previous_booking:
                nearest_previous_booking = date
        elif date > fbooking_date:
            if nearest_next_booking is None or date < nearest_next_booking:
                nearest_next_booking = date
        else:
            return jsonify({'error': 'This retreat is already booked during the requested period'}), 400

    # print('nearest_previous_booking', nearest_previous_booking,
    #       'nearest_next_booking', nearest_next_booking)
    if nearest_previous_booking:
        nearest_previous_booking_date = datetime.strptime(
            str(nearest_previous_booking), '%Y%m%d').date()
    else:
        nearest_previous_booking_date = None

    if nearest_next_booking:
        nearest_next_booking_date = datetime.strptime(
            str(nearest_next_booking), '%Y%m%d').date()
    else:
        nearest_next_booking_date = None
    print('nearest_previous_booking_date', nearest_previous_booking_date,
          'nearest_next_booking_date', nearest_next_booking_date)

    # if (nearest_previous_booking_date is not None and nearest_previous_booking_date is not None):
    #     print('Overlap with nearest previous booking: ',
    #           nearest_previous_booking_date + timedelta(days=retreat.duration))
    #     return jsonify({'error': 'This retreat is already booked during the requested period'}), 400

    if nearest_previous_booking_date:
        if (nearest_previous_booking_date + timedelta(days=retreat_duration_days) >= booking_date):
            print('Overlap with nearest previous booking:',
                  nearest_previous_booking_date + timedelta(days=retreat_duration_days))
            return jsonify({'error': 'This retreat is already booked during the requested period,prev'}), 400
    # print(nearest_previous_booking_date + timedelta(days=retreat_duration_days),
    #       nearest_next_booking_date+timedelta(days=retreat_duration_days))

    if nearest_next_booking_date:
        if (nearest_next_booking_date <= end_date):
            print('Overlap with nearest next booking:',
                  nearest_next_booking_date)
            return jsonify({'error': 'This retreat is already booked during the requested period,next'}), 400
    # print(nearest_previous_booking_date +
    #       timedelta(days=retreat_duration_days), nearest_next_booking_date+timedelta(days=retreat_duration_days))

    # if overlapping_booking:
    #     return jsonify({'error': 'This retreat is already booked during the requested period,basic'}), 400

    # Generate a unique UUID
    unique_uuid = str(uuid.uuid4())

    # If the date is available, create the new booking
    new_booking = Booking(
        user_id=unique_uuid,  # Use the generated unique UUID
        user_name=data['user_name'],
        user_email=data['user_email'],
        user_phone=data['user_phone'],
        retreat_id=retreat.id,
        retreat_title=retreat.title,
        retreat_location=retreat.location,
        retreat_price=retreat.price,
        retreat_duration=retreat.duration,
        payment_details=data['payment_details'],
        booking_date=booking_date
    )

    db.session.add(new_booking)
    db.session.commit()

    return jsonify({'message': 'Booking successful', 'booking_id': new_booking.user_id})


# @app.route('/book', methods=['POST'])
# def book_retreat():
#     data = request.json

#     existing_booking = Booking.query.filter_by(
#         user_email=data['user_email'],
#         retreat_id=data['retreat_id']
#     ).first()

#     if existing_booking:
#         return jsonify({'error': 'You have already booked this retreat'}), 400
#     unique_uuid = str(uuid.uuid4())
#     new_booking = Booking(
#         user_id=unique_uuid,
#         user_name=data['user_name'],
#         user_email=data['user_email'],
#         user_phone=data['user_phone'],
#         retreat_id=data['retreat_id'],
#         retreat_title=data['retreat_title'],
#         retreat_location=data['retreat_location'],
#         retreat_price=data['retreat_price'],
#         retreat_duration=data['retreat_duration'],
#         payment_details=data['payment_details'],
#         booking_date=data['booking_date']
#     )

#     db.session.add(new_booking)
#     db.session.commit()

#     return jsonify({'message': 'Booking successful', 'booking_id': new_booking.id}), 201
@app.route('/create_retreat', methods=['POST'])
def create_retreat():
    data = request.json

    required_fields = ['title', 'date', 'location', 'price', 'duration']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD HH:MM:SS'}), 400

    retreat_id = str(uuid.uuid4())[:8]

    new_retreat = Retreat(
        id=retreat_id,
        title=data['title'],
        description=data.get('description', ''),
        date=date,
        location=data['location'],
        price=data['price'],
        type=data.get('type', ''),
        condition=data.get('condition', ''),
        image=data.get('image', ''),
        tag=data.get('tag', []),
        duration=data['duration']
    )

    db.session.add(new_retreat)
    db.session.commit()

    return jsonify({'message': 'Retreat created successfully', 'retreat_id': new_retreat.id}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
