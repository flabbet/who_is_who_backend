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
        elif db.execute('SELECT id FROM organization WHERE name = ?', (organization_name,)).fetchone() is not None:
            error = 'Organization "{}" is already registered.'.format(organization_name)

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
                'INSERT INTO organization (name, organization_deck, author_id, organization_logo_url) VALUES (?, ?, ?, ?)',
                (organization_name, organization_deck, author_id, organization_logo_url))
            db.commit()
            return "Success"
        return error


@bp.route('/addUser', methods=('POST', 'GET'))
def add_user():
    if request.method == 'POST':
        db = get_db()
        org_name = request.form['organization_name']
        user_email = request.form['email']
        is_admin = request.form['is_admin']

        error = None
        if not org_name:
            error = name_required
        elif not is_admin:
            is_admin = 0
        elif db.execute('SELECT * FROM organization WHERE name = ?', (org_name,)).fetchone() is None:
            error = "Entered organization doesn't exist."

        if error is None:
            org_id = db.execute('SELECT id FROM organization WHERE name = ?', (org_name,)).fetchone()[0]
            db.execute('INSERT INTO user (email, organization_id, is_admin) VALUES (?, ?, ?)',
                       (user_email, org_id, is_admin))
            db.commit()
            return "Success!"
        return error


@bp.route('/getDeck', methods=('POST', 'GET'))
def get_deck():
    if request.method == 'POST':
        db = get_db()
        access_token = request.form['access_token']
        validation_request = requests.get(
            "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}".format(access_token))
        try:
            oauth_email = validation_request.json()['email']
        except KeyError:
            return "Invalid access token"
        org_id = db.execute("SELECT organization_id FROM user WHERE email = ?", (oauth_email,)).fetchone()
        if org_id is None:
            return "Logged user is not connected to any organization."
        else:
            data = db.execute("SELECT organization_deck, organization_logo_url FROM organization WHERE id = ?", (org_id[0],)).fetchall()[0]
            return jsonify({"deck_url": data[0],
                            "logo_url": data[1]})
