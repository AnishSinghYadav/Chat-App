from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import random
from twilio.rest import Client
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Twilio configuration
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
client = Client(twilio_account_sid, twilio_auth_token)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    otp = db.Column(db.String(6), nullable=False)

# Routes
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    phone_number = request.form['phone']
    otp = str(random.randint(100000, 999999))
    
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        user = User(phone_number=phone_number, otp=otp)
        db.session.add(user)
    else:
        user.otp = otp
    db.session.commit()

    # Send OTP via Twilio
    client.messages.create(
        to=phone_number,
        from_=twilio_phone_number,
        body=f"Your OTP is {otp}"
    )

    flash('OTP sent! Check your phone.')
    return redirect(url_for('verify', phone=phone_number))

@app.route('/verify')
def verify():
    phone_number = request.args.get('phone')
    return render_template('verify.html', phone=phone_number)

@app.route('/verify', methods=['POST'])
def verify_otp():
    phone_number = request.form['phone']
    otp = request.form['otp']

    user = User.query.filter_by(phone_number=phone_number, otp=otp).first()
    if user:
        session['user'] = phone_number
        flash('Login successful!')
        return redirect(url_for('chat'))
    else:
        flash('Invalid OTP. Try again.')
        return redirect(url_for('verify', phone=phone_number))

@app.route('/chat')
def chat():
    if 'user' not in session:
        flash('Please login first.')
        return redirect(url_for('index'))
    return render_template('chat.html', user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
