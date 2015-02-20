from datetime import datetime
from flask import session, g, jsonify
import flask_login
from flask_login import current_user
from flask_login import logout_user
from flask import render_template, flash, redirect, url_for, request
from app import app, db, crypto
from app.user_models import User, UserEmailAddress, EmailActivation, EmailActivationException
from app.user_forms import LoginForm, PasswordResetForm, EmailOnlyForm, RegisterForm
from . import emails
from . import auth_models


class PasswordResetException(Exception):
    pass


@app.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    """
    This is the route that a user accesses when they are resetting their password
    :return: rendered template
    """
    problem = None
    form = PasswordResetForm(activation_code=request.args['confirmation_code'])
    try:
        if form.validate_on_submit():
            activation = EmailActivation.query.filter_by(activation_code=request.args['confirmation_code']).first()
            if activation is None:
                problem = "invalid_code"
                raise PasswordResetException("Invalid activation code")
            if activation.activated is True:
                problem = "already_activated"
                raise PasswordResetException("That activation code has already been activated")
            if activation.expired() is True:
                problem = "expired"
                raise PasswordResetException("That activation code is expired")
            user = User.query.filter_by(id=activation.user_id).first()
            if user is None:
                problem = "unknown_user"
                raise PasswordResetException("Unknown account associated to that e-mail address")
            user.password_digest = crypto.get_digest(form.password.data)
            db.session.add(user)
            EmailActivation.activate(activation.activation_code)
            db.session.commit()
            flash("Your password has been reset, please remember to login with your new password", category="success")
            return redirect(url_for('login'))
    except PasswordResetException as error:
        flash(error, category="danger")
    except EmailActivationException as error:
        flash(error, category="danger")
    return render_template(
        'auth/page_password_reset.html',
        problem=problem,
        title='Request Password Reset',
        form=form)


class RequestPasswordResetException(Exception):
    pass


@app.route('/request_password_reset', methods=['GET', 'POST'])
def request_password_reset():
    """
    This is the route that a user accesses when they need to reset their password
    :return: rendered template
    """
    problem = None
    form = EmailOnlyForm()
    if form.validate_on_submit():
        try:
            email = UserEmailAddress.query.filter_by(email_address=form.email.data).first()
            if email is None:
                problem = "invalid_email"
                raise RequestPasswordResetException("Unknown e-mail address")
            user = User.query.filter_by(id=email.user_id).first()
            if user is None:
                problem = "unknown_user"
                raise RequestPasswordResetException("Unknown account associated to that e-mail address")
            new_activation = EmailActivation(user_id=user.id, email_address_id=email.id)
            db.session.add(new_activation)
            db.session.commit()
            emails.send_reset_password_activation(new_activation)
            flash("Check your e-mail, we sent the password reset request to " + email.email_address, category="info")
        except RequestPasswordResetException as error:
            flash(error, category="danger")
    return render_template(
        'auth/page_request_password_reset.html',
        problem=problem,
        title='Request Password Reset',
        form=form)

@app.route('/email_activation', methods=['GET', 'POST'])
def email_activation():
    """
    This is the route that a user accesses when activating their e-mail address
    :return:
    """
    try:
        activation = EmailActivation.activate(request.args['confirmation_code'])
        email_address = UserEmailAddress.query.filter_by(id=activation.email_address_id).first()
        email_address.confirmed = True
        db.session.add(email_address)
        db.session.commit()
        flash("E-mail address " + email_address.email_address + " activated, you may now login", category="success")
        return redirect(url_for('login'))
    except EmailActivationException as err:
        flash("Error activating that e-mail address: {0}".format(err), category="danger")
    return render_template(
        'auth/page_activate.html',
        title='Activate Your Account')


class SendActivationException(Exception):
    pass


@app.route('/send_activation', methods=['GET', 'POST'])
def send_activation():
    """
    This is the route that a user accesses when re-sending their activation e-mail
    :return: rendered template
    """
    problem = None
    form = EmailOnlyForm()
    if form.validate_on_submit():
        try:
            email = UserEmailAddress.query.filter_by(email_address=form.email.data).first()
            if email is None:
                problem = "invalid_email"
                raise SendActivationException("Unknown e-mail address")
            user = User.query.filter_by(id=email.user_id).first()
            if user is None:
                problem = "unknown_user"
                raise SendActivationException("Unknown account associated to that e-mail address")
            new_activation = EmailActivation(user_id=user.id, email_address_id=email.id)
            db.session.add(new_activation)
            emails.send_user_email_activation(new_activation)
            db.session.add(new_activation)
            db.session.commit()
            flash("Check your e-mail, we sent a new activation code to " + email.email_address, category="info")
            #TODO add a generic activation template here.
        except SendActivationException as error:
            flash(error, category="danger")
    return render_template(
        'auth/page_send_activation.html',
        problem=problem,
        title='Send New Activation',
        form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        #todo: try
        email_address = UserEmailAddress.query.filter_by(email_address=form.email.data).first()
        username = User.query.filter_by(username=form.username.data).first()
        if username is not None:
            flash("The username ({0}) is already taken".format(form.username.data), category="danger")
        elif email_address is not None:
            flash("That e-mail address has already been registered on this site", category="danger")
        else:
            new_user = User(
                username=form.username.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                password_digest=crypto.get_digest(form.password.data))
            db.session.add(new_user)
            db.session.commit()
            new_user.add_to_users_group()

            new_email_address = UserEmailAddress(
                user_id=new_user.id,
                email_address=form.email.data)
            db.session.add(new_email_address)
            db.session.commit()

            activation = EmailActivation(
                user_id=new_user.id,
                email_address_id=new_email_address.id)
            db.session.add(activation)
            db.session.commit()

            new_user.primary_email_id = new_email_address.id
            db.session.add(new_user)
            db.session.commit()

            emails.send_user_email_activation(activation)
            flash("Please check your e-mail for activation instructions", category="info")
            return redirect('login')
    return render_template(
        'auth/page_register.html',
        title='Register',
        form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


class LoginException(Exception):
    pass


@app.route('/login', methods=['GET', 'POST'])
def login():
    problem = None
    form = LoginForm()
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    try:
        if form.validate_on_submit():
            session['remember_me'] = form.remember_me.data
            email = UserEmailAddress.query.filter_by(email_address=form.email.data).first()
            if email is None:
                problem = "email"
                raise LoginException("That account does not exist")
            user = User.query.filter_by(id=email.user_id).first()
            if user is None:
                problem = "email"
                raise LoginException("Unknown account associated to that e-mail address")
            if not crypto.is_password(form.password.data, user.password_digest):
                problem = "password"
                raise LoginException("Invalid password")
            if email.confirmed is False:
                problem = "inactive"
                raise LoginException("Your account hasn't been activated yet")
            remember_me = False
            if 'remember_me' in session:
                remember_me = session['remember_me']
                session.pop('remember_me', None)
            flask_login.login_user(user, remember=remember_me)
            user.last_login = datetime.utcnow()
            db.session.add(user)
            db.session.commit()
            flash("You are now logged in, welcome back {}".format(user.username), category="success")
            return redirect(request.args.get('next') or url_for('index'))
    except LoginException as error:
        flash(error, category="danger")
    return render_template(
        'auth/page_login.html',
        problem=problem,
        title='Login',
        form=form)


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('index'))
    oauth = auth_models.OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('index'))
    oauth = auth_models.OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('login'))
    user = User.query.filter_by(social_id=social_id).first()

    if user is not None:
        user.last_login = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        flask_login.login_user(user, remember=False)
        flash("You are now logged in, welcome back {}".format(user.username), category="success")

    # We didn't find an existing user with that social ID
    # but the provider returns an email address, check that...
    elif not user and email is not None:
        user_email = UserEmailAddress.query.filter_by(email_address=email).first()
        if user_email is not None:
            user = User.query.filter_by(id=user_email.user_id).first()
            # Add the social ID so we don't have to go through an email lookup next time.
            user.social_id = social_id
            user.last_login = datetime.utcnow()
            db.session.add(user)
            db.session.commit()
            flash("You are now logged in, welcome back {}".format(user.username), category="success")
            flash("Note: the email address {} is now linked to the {} account with ID {}"
                  .format(email, provider, social_id), category="info")
            flask_login.login_user(user, remember=False)

        # There was no user with that social ID or email
        # so we need to create a new user with an email account
        else:
            new_email = UserEmailAddress(email_address=email, activated=True)
            db.session.add(user_email)
            db.session.commit()
            new_user = User(social_id=social_id, primary_email_id=new_email.id, username=username,
                            last_login=datetime.utcnow())
            db.session.add(new_user)
            db.session.commit()
            new_email.user_id = new_user.id
            db.session.add(new_email)
            db.session.commit()
            flask_login.login_user(new_user, remember=False)
            flash("You are now logged in new {} account linked to {}".format(provider, user.username), category="success")

    # We didn't find an existing user with that social ID and
    # the provider did not return an email address, so we're
    # creating a new user without an email account associated
    elif not user:
        new_user = User(social_id=social_id, username=username, last_login=datetime.utcnow())
        db.session.add(new_user)
        db.session.commit()
        flask_login.login_user(new_user, remember=False)
        flash("New account created and logged in via your {} account, welcome {}".format(provider, new_user.username),
              category="success")

    return redirect(url_for('index'))
