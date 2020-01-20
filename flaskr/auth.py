import requests
from flask import (
    Blueprint, request,
    jsonify)

from flaskr.db import get_db

name_required = "Organization Name is required."

bp = Blueprint('auth', __name__, url_prefix='/org')


@bp.route('/register', methods=('POST', 'GET'))
def register_organization():
    if request.method == 'POST':
        author_email = request.form['author_email']
        organization_name = request.form['organization_name']
        organization_deck = request.form['organization_deck']
        organization_logo_url = request.form['organization_logo']
        organization_domain = request.form['domain']
        db = get_db()
        error = None

        if not organization_name:
            error = name_required
        elif not organization_deck:
            error = "Organization deck URL is required."
        elif not organization_logo_url:
            error = "Organization logo url is required."
        elif not author_email:
            error = "Creator email is required."
        elif not organization_domain:
            error = "Organization domain is required."
        elif db.execute('SELECT id FROM organization WHERE name = ?', (organization_name,)).fetchone() is not None:
            error = 'Organization "{}" is already registered.'.format(organization_name)
        elif db.execute('SELECT id FROM organization WHERE domain = ?', (organization_domain,)).fetchone() is not None:
            error = "Domain {} is already registered.".format(organization_domain)
        elif db.execute('SELECT * FROM user WHERE email = ?', (author_email,)).fetchone() is not None:
            error = "This email is already registered to another organization"

        if error is None:

            last_org_id = db.execute('SELECT id FROM user ORDER BY id DESC LIMIT 1').fetchone()
            if last_org_id is None:
                last_org_id = 0
            else:
                last_org_id = last_org_id[0]
            db.execute('INSERT INTO user (email, organization_id, is_admin) VALUES (?, ?, ?)',
                       (author_email, last_org_id + 1, True))
            author_id = db.execute('SELECT id FROM organization ORDER BY id DESC LIMIT 1').fetchone()
            if author_id is None:
                author_id = 1
            else:
                author_id = author_id[0]
            db.execute(
                'INSERT INTO organization (name, organization_deck, author_id, organization_logo_url, domain) VALUES (?, ?, ?, ?, ?)',
                (organization_name, organization_deck, author_id, organization_logo_url, organization_domain))
            db.commit()
            return "Success"
        return error


@bp.route('/removeUser', methods=('POST', 'GET'))
def remove_user():
    if request.method == 'POST':
        db = get_db()
        access_token = request.form['access_token']
        target_user_email = request.form['target_email']
        error = None
        request_email = get_token_email(access_token)

        if not access_token:
            error = "Access token is required."
        elif request_email is None:
            error = "Access token is invalid."
        elif db.execute('SELECT * FROM user WHERE email = ?', (request_email,)).fetchone() is None:
            error = "Email registered to this token doesn't exist"
        elif db.execute('SELECT is_admin FROM user WHERE email = ?', (request_email,)).fetchone()[0] == 0:
            error = "Insufficient permissions."

        org_id = db.execute('SELECT organization_id FROM user WHERE email = ?', (request_email,)).fetchone()[0]
        if db.execute('SELECT * FROM user WHERE (email, organization_id) = (?, ?)', (target_user_email, org_id)).fetchone() is None:
            error = "User doesn't exist in requested organization"

        if error is None:
            db.execute('DELETE FROM user WHERE email = ?',
                       (target_user_email,))
            db.commit()
            return "Success"
        return error


@bp.route('/addUser', methods=('POST', 'GET'))
def add_user():
    if request.method == 'POST':
        db = get_db()
        access_token = request.form['access_token']
        user_email = request.form['email']
        is_admin = request.form['is_admin']
        request_email = get_token_email(access_token)

        error = None
        if not access_token:
            error = "Access token is required."
        elif request_email is None:
            error = "Access token is invalid."
        elif not is_admin:
            is_admin = 0
        elif db.execute('SELECT * FROM user WHERE email = ?', (user_email,)).fetchone() is not None:
            error = "This user is already registered"
        elif db.execute('SELECT * FROM user WHERE email = ?', (request_email,)).fetchone() is None:
            error = "Email registered to this token doesn't exist"
        elif db.execute('SELECT is_admin FROM user WHERE email = ?', (request_email,)).fetchone()[0] == 0:
            error = "Insufficient permissions."

        if error is None:
            org_id = db.execute('SELECT id FROM user WHERE email = ?', (request_email,)).fetchone()[0]
            db.execute('INSERT INTO user (email, organization_id, is_admin) VALUES (?, ?, ?)',
                       (user_email, org_id, is_admin))
            db.commit()
            return "Success"
        return error


@bp.route('/getDeck', methods=('POST', 'GET'))
def get_deck():
    if request.method == 'POST':
        db = get_db()
        access_token = request.form['access_token']
        oauth_email = get_token_email(access_token)
        error = None
        if oauth_email is None:
            error = "Invalid access token"

        org_id = db.execute("SELECT organization_id FROM user WHERE email = ?", (oauth_email,)).fetchone()
        user_domain = oauth_email.split('@')[1]
        if org_id is None:
            org_id = db.execute('SELECT id FROM organization WHERE domain = ?', (user_domain,)).fetchone()
            if org_id is None:
                error = "Logged user is not connected to any organization."
        if error is None:
            data = db.execute("SELECT organization_deck, organization_logo_url FROM organization WHERE id = ?",
                                 (org_id[0],)).fetchall()[0]
            logged_user_is_admin = db.execute('SELECT is_admin FROM user WHERE email = ?', (oauth_email,)).fetchone()
            if logged_user_is_admin is None:
                logged_user_is_admin = 0
            else:
                logged_user_is_admin = logged_user_is_admin[0]
            return jsonify({"deck_url": data[0],
                            "logo_url": data[1],
                            "is_admin": logged_user_is_admin
                             })
        return error


def get_token_email(token):
    validation_request = requests.get(
        "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}".format(token))
    try:
        return validation_request.json()['email']
    except KeyError:
        return None
