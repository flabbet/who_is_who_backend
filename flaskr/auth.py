from flask import (
    Blueprint, request
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.code_generator import generate_code
from flaskr.db import get_db

name_required = "Organization Name is required."

bp = Blueprint('auth', __name__, url_prefix='/org')


@bp.route('/register', methods=('POST', 'GET'))
def register_organization():
    if request.method == 'POST':
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
        elif db.execute('SELECT id FROM organization WHERE name = ?', (organization_name,)).fetchone() is not None:
            error = 'Organization "{}" is already registered.'.format(organization_name)

        if error is None:
            access_code = generate_unique_code(db)

            last_org_id = db.execute('SELECT id FROM user ORDER BY id DESC LIMIT 1').fetchone()
            if last_org_id is None:
                last_org_id = 0
            else:
                last_org_id = last_org_id[0]
            db.execute('INSERT INTO user (access_code, organization_id, is_admin) VALUES (?, ?, ?)',
                       (generate_password_hash(access_code), last_org_id + 1, True))
            author_id = db.execute('SELECT id FROM organization ORDER BY id DESC LIMIT 1').fetchone()
            if author_id is None:
                author_id = 1
            else:
                author_id = author_id[0]
            db.execute('INSERT INTO organization (name, organization_deck, author_id, organization_logo_url) VALUES (?, ?, ?, ?)',
                       (organization_name, organization_deck, author_id, organization_logo_url))
            db.commit()
            return access_code
        return error


@bp.route('/addUser', methods=('POST', 'GET'))
def add_user():
    if request.method == 'POST':
        db = get_db()
        org_name = request.form['organization_name']
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
            access_code = generate_unique_code(db)
            db.execute('INSERT INTO user (access_code, organization_id, is_admin) VALUES (?, ?, ?)',
                       (generate_password_hash(access_code), org_id, is_admin))
            db.commit()
            return access_code
        return error


@bp.route('/getDeck', methods=('POST', 'GET'))
def get_deck():
    if request.method == 'POST':
        error = None
        db = get_db()
        access_code = request.form['access_code']
        for user in db.execute('SELECT * FROM user').fetchall():
            if check_password_hash(user['access_code'], access_code):
                org_id = db.execute('SELECT organization_id FROM user WHERE id = ?', (user['id'],)).fetchone()
                if org_id is None:
                    org_id = 1
                else:
                    org_id = org_id[0]
                return db.execute("SELECT organization_deck FROM organization WHERE id = ?", (org_id,)).fetchone()[0]
        error = "Entered access code is not valid."
        return error


def access_code_exists(access_code, entries):
    for user in entries:
        if check_password_hash(user['access_code'], access_code):
            return True
    return False


def generate_unique_code(db):
    access_code = generate_code()
    users = db.execute('SELECT * FROM user').fetchall()
    while access_code_exists(access_code, users):
        access_code = generate_code()
    return access_code
