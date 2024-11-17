from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import datetime
import matplotlib.pyplot as plt
import io
import base64
import random
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Database models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

class Simulation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    years = db.Column(db.Integer, nullable=False)
    result_data = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/simulate', methods=['POST'])
@login_required
def simulate():
    ticker = request.form['ticker']
    years = int(request.form['years'])

    # Dummy simulation data
    data = np.random.normal(10, 2, 100)

    # Generate plots
    plt.figure()
    plt.plot(data)
    line_chart = save_plot_to_base64()

    plt.figure()
    plt.hist(data, bins=10)
    histogram = save_plot_to_base64()

    plt.figure()
    plt.pie([random.random() for _ in range(5)], labels=["A", "B", "C", "D", "E"], autopct='%1.1f%%')
    pie_chart = save_plot_to_base64()

    # Save to database
    simulation = Simulation(
        user_id=current_user.id,
        ticker=ticker,
        years=years,
        result_data="Example Data"
    )
    db.session.add(simulation)
    db.session.commit()

    return jsonify({'status': 'success', 'line_chart': line_chart, 'histogram': histogram, 'pie_chart': pie_chart})

def save_plot_to_base64():
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    return image_base64

@app.route('/history')
@login_required
def history():
    simulations = Simulation.query.filter_by(user_id=current_user.id).all()
    return render_template('history.html', simulations=simulations)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
