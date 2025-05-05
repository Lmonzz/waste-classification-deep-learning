from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os
from forms import registerForm, loginForm, updateForm, profileForm
from predict import continous_prediction
from datetime import datetime
from helper import get_category
import requests

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = 'D:\\Python\\deep_learning\\FINAL_TF2_FILES\\TF_2_Notebooks_and_Data\\04-CNNs\\ESP32CAM\\captured_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'flaskApp.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_PERMANENT"] = False


db = SQLAlchemy(app)
migrate = Migrate(app, db)

#MODEL 
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')
    password = db.Column(db.String(200), nullable=False)


    def __init__(self, username, phone, email, password):
        self.username = username
        self.phone = phone
        self.email = email
        self.role = 'user'
        self.password = password

class Trash(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    numbers = db.Column(db.Integer, default = 0)

    def __init__(self, name, category):
        self.name = name
        self.category = category
        self.numbers = 0    


@app.route('/')
def index():
    stats = db.session.query(Trash.category, db.func.sum(Trash.numbers).label('total')).group_by(Trash.category).all()
    print(f'Here is what stats look like: {stats}\n')
    stat_dict = {cat: total for cat, total in stats}
    print(f'Here is what stat dict look like: {stat_dict}\n')
    return render_template('index.html', stats = stat_dict)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = registerForm()
    if form.validate_on_submit():
        session['username'] = form.username.data
        session['phone'] = form.phone.data
        session['email'] = form.email.data
        session['password'] = generate_password_hash(form.password.data)

        user = User.query.filter_by(email=session['email']).first()
        if user:
            flash("Email already registered", "danger")
            return redirect(url_for('register'))

        new_user = User(username=session['username'], phone=session['phone'], email=session['email'], password=session['password'])
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful, please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = loginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html', form=form)

@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/upload')
def upload():
    if not session.get("username"):
        flash("You need to login first", "danger")
        return redirect(url_for('login'))
    return render_template('upload.html', username=session['username'])


@app.route('/upload_img', methods=['POST'])
def upload_img():
    if not session.get("username"):
        flash("You need to login first", "danger")
        return redirect(url_for('upload'))
    
    if 'imageFile' not in request.files:
        flash("No image file provided", "danger")
        return redirect(url_for('upload'))
        
    file = request.files['imageFile']

    if file.filename == '':
        flash("No image selected", "danger")
        return redirect(url_for('upload'))

    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"{timestamp}_{file.filename}"
    file.filename = new_filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    print(f"File saved to: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")
    result, confidence = continous_prediction(file_path) 
    trash_record = Trash.query.filter_by(name=result).first()
    if trash_record:
        trash_record.numbers += 1
    else:
        category = get_category(result)
        trash_record = Trash(name=result, category=category)
        trash_record.numbers = 1
        db.session.add(trash_record)

    db.session.commit()
    print(f"Prediction result: {result}")
    return render_template(
        'upload.html',
        username=session['username'],
        result=result,
        confidence=confidence
    )

@app.route('/upload_img_esp', methods=['POST', 'GET'])
def upload_img_esp():
    if 'imageFile' not in request.files:
        return "No image file provided", 400

    file = request.files['imageFile']
    if file.filename == '':
        return "No image selected", 400

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        file.save(file_path)
        print(f"File saved to: {file_path}")
        print(f"Exists? {os.path.exists(file_path)}")

        # Run prediction
        result, confidence = continous_prediction(file_path)
        print(f"Prediction result: {result}")

        # Update DB
        trash_record = Trash.query.filter_by(name=result).first()
        if trash_record:
            trash_record.numbers += 1
        else:
            category = get_category(result)
            trash_record = Trash(name=result, category=category)
            trash_record.numbers = 1
            db.session.add(trash_record)

        db.session.commit()
        try:
            json_data = {"result": result, "confidence": round(confidence, 2)}
            esp_response = requests.post(f"http://192.168.154.78/prediction", json=json_data)
            print(f"ESP8266 responded: {esp_response.text}")
        except Exception as e:
            print(f"Error sending data to ESP8266: {e}")

        return {
            "result": result
        }, 200
    
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}, 500


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get("username"):
        flash("You need to login first", "danger")
        return redirect(url_for('upload'))
    
    user = User.query.filter_by(username=session["username"]).first()
    if not user:
        flash("User not found", "danger")
        return redirect(url_for('login'))
    
    form = profileForm(obj=user)
    if form.validate_on_submit():
        if form.email.data != user.email:
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email:
                flash("Email already in use", "danger")
                return redirect(url_for('update_profile'))
        
        if form.phone.data != user.phone:
            existing_phone = User.query.filter_by(phone=form.phone.data).first()
            if existing_phone:
                flash("Phone already in use", "danger")
                return redirect(url_for('update_profile'))
            
        user.email = form.email.data
        user.phone = form.phone.data
        db.session.commit()
        flash("Profile updated successfully", "success")
        return redirect(url_for('profile'))
    return render_template('profile.html', form=form, user=user)

@app.route('/admin')
def admin_dashboard():
    if not session.get("username") or session['role'] != 'admin':
        flash("You need to login as admin first", "danger")
        return redirect(url_for('login'))
    users = User.query.all()
    trash = Trash.query.all()
    return render_template('admin_dashboard.html', users=users, trash=trash)

@app.route('/admin/user/update/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    if not session.get("username") or session['role'] != 'admin':
        flash("You need to login as admin first", "danger")
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    form = updateForm(obj=user)
    if form.validate_on_submit():
        if user:
            user.username = form.username.data
            user.phone = form.phone.data
            user.email = form.email.data
            user.role = form.role.data
            db.session.commit()
            flash('User updated successfully')
        else:
            flash('User not found', 'danger')
        return redirect(url_for('admin_dashboard'))
    return render_template('update_user.html', form=form, user=user)

@app.route('/admin/user/delete/<int:user_id>')
def delete_user(user_id):
    if not session.get("username") or session['role'] != 'admin':
        flash("You need to login as admin first", "danger")
        return redirect(url_for('login'))
    user = User.query.get_or_404(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully')
    else:
        flash('User not found', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reset_trash/<int:trash_id>', methods=['POST'])
def reset_trash(trash_id):
    if not session.get("username") or session['role'] != 'admin':
        flash("You need to login as admin first", "danger")
        return redirect(url_for('login'))
    trash = Trash.query.filter_by(id=trash_id).first()
    if trash:
        trash.numbers = 0
        db.session.commit()
        flash('Trash count reset successfully')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists('flaskApp.sqlite'):
            db.create_all()
            db.session.commit()

    app.run(host='0.0.0.0', port=5000, debug=True)