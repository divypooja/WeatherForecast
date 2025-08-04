from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from forms import LoginForm
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    # Handle both form validation and direct POST data for compatibility
    if request.method == 'POST':
        username = form.username.data if form.username.data else request.form.get('username')
        password = form.password.data if form.password.data else request.form.get('password')
        
        if username and password:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password) and user.is_active:
                login_user(user, remember=True)
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
            else:
                flash('Invalid username or password', 'danger')
        elif form.validate_on_submit():
            # Fallback to form validation if direct access failed
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data) and user.is_active:
                login_user(user, remember=True)
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
            else:
                flash('Invalid username or password', 'danger')
        else:
            flash('Please check your form entries', 'warning')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth.login'))
