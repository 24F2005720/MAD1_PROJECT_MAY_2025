from flask import Flask,  render_template, request, redirect, url_for, flash, session
from models import db, User, ParkingLot, ParkingSpot, Booking
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from sqlalchemy import func, extract
from sqlalchemy.orm import joinedload
import math
from collections import defaultdict

app = Flask("Quick Park")
app.config['SECRET_KEY'] = "ADI"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///parking.db"
db.init_app(app)

@app.before_request
def create_admin_and_db():
    if not hasattr(app, 'db_initialized'):
        with app.app_context():
            if not os.path.exists('instance/parking.db'):
                db.create_all()
                print("Database created successfully!")
                
                admin_user = User.query.filter_by(role='admin').first()
                if not admin_user:
                    admin_password = 'admin'
                    hashed_password = generate_password_hash(admin_password)
                    new_admin = User(
                        username='admin',
                        email='admin@quickpark.com',
                        phone_number='0000000000',
                        password_hash=hashed_password,
                        role='admin'
                    )
                    db.session.add(new_admin)
                    db.session.commit()
                    print("Admin user created successfully!")
        app.db_initialized = True

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            flash('Logged in successfully!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email address is already registered.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(phone_number=phone_number).first():
            flash('Phone number is already registered.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            phone_number=phone_number,
            password_hash=hashed_password,
            role='user'
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('login'))
    
    all_lots = ParkingLot.query.order_by(ParkingLot.name).all()
    total_bookings = Booking.query.count()
    total_revenue = db.session.query(func.sum(Booking.cost)).scalar() or 0.0

    monthly_revenue = db.session.query(
        extract('year', Booking.entry_time).label('year'),
        extract('month', Booking.entry_time).label('month'),
        func.sum(Booking.cost)
    ).filter(Booking.cost.isnot(None)).group_by('year', 'month').order_by('year', 'month').all()

    chart_labels = [f"{datetime(int(y), int(m), 1).strftime('%b %Y')}" for y, m, r in monthly_revenue]
    chart_values = [float(r) for y, m, r in monthly_revenue]

    return render_template(
        'admin/dashboard.html', 
        lots=all_lots, 
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        chart_labels=chart_labels,
        chart_values=chart_values
    )

@app.route('/admin/users')
def view_users():
    if session.get('role') != 'admin':
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('login'))
    
    users = User.query.filter_by(role='user').order_by(User.username).all()
    return render_template('admin/view_users.html', users=users)

@app.route('/admin/user/<int:user_id>')
def user_details(user_id):
    if session.get('role') != 'admin':
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.entry_time.desc()).all()
    return render_template('admin/user_details.html', user=user, bookings=bookings)

@app.route('/admin/spot/<int:spot_id>')
def spot_history(spot_id):
    if session.get('role') != 'admin':
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('login'))
    
    spot = ParkingSpot.query.get_or_404(spot_id)
    bookings = Booking.query.filter_by(spot_id=spot.id).order_by(Booking.entry_time.desc()).all()
    return render_template('admin/spot_history.html', spot=spot, bookings=bookings)

@app.route('/admin/lot/<int:lot_id>')
def view_lot(lot_id):
    if session.get('role') != 'admin':
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('login'))

    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.spot_number).all()

    occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status=False).count()
    available_count = lot.capacity_4_wheeler - occupied_count
    chart_data = {'occupied': occupied_count, 'available': available_count}

    return render_template('admin/view_lot.html', lot=lot, spots=spots, chart_data=chart_data)

@app.route('/admin/add_lot', methods=['POST'])
def add_lot():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    name = request.form['name']
    address = request.form['address']
    pin_code = request.form['pin_code']
    capacity_4_wheeler = int(request.form['capacity_4_wheeler'])
    price_per_hour_4_wheeler = float(request.form['price_per_hour_4_wheeler'])
    
    new_lot = ParkingLot(
        name=name,
        address=address,
        pin_code=pin_code,
        capacity_4_wheeler=capacity_4_wheeler,
        price_per_hour_4_wheeler=price_per_hour_4_wheeler
    )
    db.session.add(new_lot)
    db.session.commit()

    for i in range(1, capacity_4_wheeler + 1):
        spot = ParkingSpot(
            lot_id=new_lot.id,
            spot_number=i,
            vehicle_type='4w',
            status=True
        )
        db.session.add(spot)
    db.session.commit()

    flash(f'Parking lot "{name}" and its {capacity_4_wheeler} spots have been added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_lot/<int:lot_id>', methods=['GET'])
def edit_lot(lot_id):
    if session.get('role') != 'admin':
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('login'))
        
    lot = ParkingLot.query.get_or_404(lot_id)
    return render_template('admin/edit_lot.html', lot=lot)

@app.route('/admin/update_lot/<int:lot_id>', methods=['POST'])
def update_lot(lot_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    lot = ParkingLot.query.get_or_404(lot_id)

    lot.name = request.form['name']
    lot.address = request.form['address']
    lot.pin_code = request.form['pin_code']
    lot.price_per_hour_4_wheeler = float(request.form['price_per_hour_4_wheeler'])
    new_capacity = int(request.form['capacity_4_wheeler'])
    old_capacity = lot.capacity_4_wheeler

    if new_capacity < old_capacity:
        spots_to_delete = ParkingSpot.query.filter(
            ParkingSpot.lot_id == lot_id,
            ParkingSpot.spot_number > new_capacity,
            ParkingSpot.status == False
        ).count()

        if spots_to_delete > 0:
            flash('Cannot decrease capacity, one or more spots to be removed are occupied.', 'danger')
            return redirect(url_for('edit_lot', lot_id=lot_id))
        
        ParkingSpot.query.filter(ParkingSpot.lot_id == lot_id, ParkingSpot.spot_number > new_capacity).delete()

    elif new_capacity > old_capacity:
        for i in range(old_capacity + 1, new_capacity + 1):
            spot = ParkingSpot(lot_id=lot.id, spot_number=i, vehicle_type='4w', status=True)
            db.session.add(spot)

    lot.capacity_4_wheeler = new_capacity
    db.session.commit()
    flash(f'Parking lot "{lot.name}" has been updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_lot/<int:lot_id>', methods=['POST'])
def delete_lot(lot_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
        
    lot = ParkingLot.query.get_or_404(lot_id)

    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status=False).count()
    if occupied_spots > 0:
        flash(f'Cannot delete "{lot.name}" because it has occupied spots.', 'danger')
        return redirect(url_for('admin_dashboard'))

    db.session.delete(lot)
    db.session.commit()
    flash(f'Parking lot "{lot.name}" has been deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/user/dashboard')
def user_dashboard():
    if session.get('role') != 'user':
        flash('You must be logged in as a user to access this page.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']

    active_bookings = Booking.query.filter_by(user_id=user_id, exit_time=None).all()
    
    subquery = db.session.query(ParkingSpot.lot_id).filter_by(status=True).distinct()
    available_lots = ParkingLot.query.filter(ParkingLot.id.in_(subquery)).all()

    return render_template('user/dashboard.html', active_bookings=active_bookings, lots=available_lots)

@app.route('/user/book/<int:lot_id>', methods=['POST'])
def book_spot(lot_id):
    if session.get('role') != 'user':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    vehicle_number = request.form.get('vehicle_number').upper() 

    if not vehicle_number:
        flash('Vehicle number is required.', 'danger')
        return redirect(url_for('user_dashboard'))

    available_spot = ParkingSpot.query.filter_by(lot_id=lot_id, status=True).order_by(ParkingSpot.spot_number).first()
    
    if available_spot:
        available_spot.status = False
      
        new_booking = Booking(
            user_id=user_id,
            spot_id=available_spot.id,
            vehicle_number=vehicle_number,
            entry_time=datetime.utcnow()
        )
        db.session.add(new_booking)
        db.session.commit()
        
        flash(f'Successfully booked Spot {available_spot.spot_number} at {available_spot.lot.name}!', 'success')
    else:
        flash('Sorry, no spots are available in this lot at the moment.', 'danger')
        
    return redirect(url_for('user_dashboard'))

@app.route('/user/release/<int:booking_id>', methods=['POST'])
def release_spot(booking_id):
    if 'user_id' not in session:
        flash('Please log in to continue.', 'danger')
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)
    
    if booking.user_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('user_dashboard'))

    if booking.exit_time is not None:
        flash('This parking session has already ended.', 'warning')
        return redirect(url_for('user_dashboard'))

    spot = booking.spot
    spot.status = True

    booking.exit_time = datetime.utcnow()
    duration_seconds = (booking.exit_time - booking.entry_time).total_seconds()
    duration_hours = math.ceil(duration_seconds / 3600)
    if duration_hours < 1:
        duration_hours = 1
    
    price_per_hour = spot.lot.price_per_hour_4_wheeler
    booking.cost = duration_hours * price_per_hour

    db.session.commit()
    
    flash_message = (f'Thank you! You have released Spot {spot.spot_number}. '
                     f'Total time: {duration_hours} hour(s). Total cost: ₹{booking.cost:.2f}.')
    flash(flash_message, 'success')
    
    return redirect(url_for('user_dashboard'))

@app.route('/user/history')
def user_history():
    if session.get('role') != 'user':
        flash('You must be logged in as a user to access this page.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    past_bookings = Booking.query.filter(
        Booking.user_id == user_id,
        Booking.exit_time.isnot(None)
    ).order_by(Booking.entry_time.desc()).all()

    monthly_costs = defaultdict(float)
    for booking in past_bookings:
        month_key = booking.entry_time.strftime('%Y-%m')
        monthly_costs[month_key] += booking.cost

    sorted_months = sorted(monthly_costs.keys())
    chart_labels = [datetime.strptime(m, '%Y-%m').strftime('%b %Y') for m in sorted_months]
    chart_values = [monthly_costs[m] for m in sorted_months]

    return render_template('user/history.html',
                           bookings=past_bookings,
                           chart_labels=chart_labels,
                           chart_values=chart_values)

if __name__ == "__main__":
    app.run(debug=True)
