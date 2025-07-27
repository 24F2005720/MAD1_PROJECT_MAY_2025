# Vehicle Parking Management System

This is a comprehensive, multi-user Vehicle Parking Application built with Flask. It provides a complete solution for managing parking lots, spots, and vehicle bookings, featuring separate interfaces for an administrator and regular users.

## Demo Video

https://drive.google.com/file/d/1jwGw3WLaSAI6feNy2FGGUuICBOt6g0Ow/view?usp=sharing

-----

## Features

### Admin Functionality

  * *Secure Login*: Admins have a dedicated login portal.
  * *Lot Management*: Full CRUD (Create, Read, Update, Delete) functionality for parking lots.
  * *Dynamic Spot Creation*: Parking spots are automatically generated based on the lot's specified capacity.
  * *User Management*: View a list of all registered users, their contact details, and their complete booking history.
  * *Detailed History*: Drill down to view the complete booking history for any individual parking spot.
  * *Data Visualization*:
      * A dashboard with key statistics like Total Revenue and Total Bookings.
      * An interactive bar chart showing Monthly Revenue.
      * A live occupancy pie chart for each individual parking lot.

### User Functionality

  * *Secure Registration & Login*: Users can create an account with their username, email, and phone number.
  * *Multi-Booking Capability*: Users can book multiple parking spots in different lots simultaneously.
  * *Automated Spot Allocation*: The system automatically assigns the first available spot in a chosen lot.
  * *Booking Lifecycle*: Users can easily "Release" a spot. The system then calculates the total duration and cost.
  * *Personalized Dashboard*: View a list of all active parking sessions.
  * *Booking History & Analytics*: Users can view their complete booking history and a monthly spending chart.
  * *Input Validation*: The vehicle number input field includes front-end validation to guide users toward the standard Indian format.

-----

## Technologies Used

  * *Backend*: Flask, Flask-SQLAlchemy
  * *Database*: SQLite
  * *Frontend*: HTML, CSS, Bootstrap 5, Jinja2
  * *Charting*: Chart.js

-----

## Database Schema

erdiagram
    USER {
        int id PK
        string username
        string email
        string phone_number
        string password_hash
        string role
    }

    PARKING_LOT {
        int id PK
        string name
        string address
        string pin_code
        float price_per_hour_4_wheeler
        int capacity_4_wheeler
    }

    PARKING_SPOT {
        int id PK
        int lot_id FK
        int spot_number
        string vehicle_type
        boolean status
    }

    BOOKING {
        int id PK
        int user_id FK
        int spot_id FK
        string vehicle_number
        datetime entry_time
        datetime exit_time
        float cost
    }

    USER ||--o{ BOOKING : "places"
    PARKING_LOT ||--|{ PARKING_SPOT : "contains"
    PARKING_SPOT ||--o{ BOOKING : "has"


-----

## Setup and Installation

To run this project on your local machine, please follow these steps:

*1. Clone the Repository*

sh
git clone <your-repository-url>
cd <repository-folder>


*2. Create and Activate a Virtual Environment*

It's highly recommended to use a virtual environment to manage project dependencies.

For Linux/macOS:

sh
python3 -m venv venv
source venv/bin/activate


For Windows:

sh
python -m venv venv
.\venv\Scripts\activate


*3. Install Dependencies*

Install all the required packages from the requirements.txt file.

sh
pip install -r requirements.txt


*4. Run the Application*

Execute the app.py file. The application will automatically create the parking.db database file and the default admin user on the first run.

sh
python app.py


The application will be running at http://127.0.0.1:5000.

-----

## Admin Credentials

A default administrator account is created automatically. Use the following credentials to log in as an admin:

  * *Username*: admin
  * *Password*: admin
