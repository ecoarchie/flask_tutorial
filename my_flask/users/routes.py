from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from my_flask import bcrypt, db
from my_flask.models import User, UserDetails
from my_flask.users.forms import (
    AccountUpdateForm,
    ChangePasswordForm,
    LoginForm,
    RegistrationForm,
    ResetPasswordForm,
)
from my_flask.users.utils import save_account_image, send_email


users = Blueprint("users", __name__)


@users.route("/register", methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("users.account"))
    form = RegistrationForm()
    if form.validate_on_submit():
        encrypted_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=encrypted_password,
        )
        db.session.add(user)
        db.session.commit()
        flash(
            f"Account created successfuly for {form.username.data}", category="success"
        )
        return redirect(url_for("users.login"))
    return render_template("register.html", title="SignUp", form=form)


@users.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("users.account"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if form.email.data == user.email and bcrypt.check_password_hash(
            user.password, form.password.data
        ):
            login_user(user)
            flash(f"Entered successfully in {form.email.data}", category="success")
            return redirect(url_for("users.account"))
        else:
            flash(
                f"Invalid account email or password for {form.email.data}",
                category="danger",
            )
    return render_template("login.html", title="Login", form=form)


@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("users.login"))


@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = AccountUpdateForm()
    if form.validate_on_submit():
        if form.account_image.data:
            new_account_imagefile_name = save_account_image(form.account_image.data)
            current_user.profile_image = new_account_imagefile_name
        current_user.username = form.username.data
        current_user.email = form.email.data
        user_details = UserDetails(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            user_id=current_user.id,
        )
        db.session.add(user_details)
        db.session.commit()
        flash(f"Account info updated successfully", category="success")
        return redirect(url_for("users.account"))

    elif request.method == "GET":
        print(current_user.username)
        try:
            form.first_name.data = current_user.details[-1].first_name
            form.last_name.data = current_user.details[-1].last_name
        except:
            pass

        form.username.data = current_user.username
        form.email.data = current_user.email
    image_url = url_for(
        "static", filename="profile_images/" + current_user.profile_image
    )

    return render_template(
        "account.html",
        title="Account",
        legend="Account details",
        form=form,
        image_url=image_url,
    )


@users.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_email(user)
            flash("Reset request is sent. Check your mail", category="success")
            return redirect(url_for("users.login"))
    return render_template(
        "reset_pass.html", title="Reset password", form=form, legend="Reset password"
    )


@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    user = User.verify_token(token)
    if user is None:
        flash("That token is invalid or expired. Please try again", "warning")
        redirect(url_for("users.reset_password"))
    form = ChangePasswordForm()
    if form.validate_on_submit():
        encrypted_password = bcrypt.generate_password_hash(
            form.new_password.data
        ).decode("utf-8")
        user.password = encrypted_password
        db.session.commit()
        flash("Password has been changed successfully. Please login", "success")
        return redirect(url_for("users.login"))
    return render_template(
        "change_password.html",
        title="Change password",
        legend="Change password",
        form=form,
    )
