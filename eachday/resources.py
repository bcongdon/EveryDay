import flask
from flask import request
from flask_restful import Resource, wraps
from .models import User, Entry, BlacklistToken, UserSchema, EntrySchema
from .utils import send_error, send_success, send_data, InvalidJSONException

from eachday import db, bcrypt


def validate_auth(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header.split(' ')[1]
        else:
            return send_error('Please provide an auth token', 401)

        resp = User.decode_auth_token(auth_token)
        if not isinstance(resp, str):
            user_id = resp
            flask.g.auth_token = auth_token
            return func(user_id=user_id, *args, **kwargs)
        else:
            return send_error(resp, 401)
    return wrapped


def json_load_failed(self):
    raise InvalidJSONException


def get_json():
    request.on_json_loading_failed = json_load_failed
    return request.get_json(force=True)


class UserResource(Resource):
    method_decorators = [validate_auth]

    def get(self, user_id=None):
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return send_error('Invalid user id', 404)

        return send_data(UserSchema().dump(user).data)

    def put(self, user_id=None):
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return send_error('Invalid user id', 404)

        data = get_json()
        if 'password' not in data:
            return send_error('Must provide password', 401)
        if not bcrypt.check_password_hash(user.password, data.get('password')):
            return send_error('Invalid password.', 401)

        if data.get('new_password'):
            user.set_password(data['new_password'])

        if data.get('email'):
            user.email = data['email']

        if data.get('name'):
            user.name = data['name']

        return send_data(UserSchema().dump(user).data)


class RegisterResource(Resource):
    def post(self):
        args, errors = UserSchema().load(get_json())
        if errors:
            return send_error(errors)

        user = db.session.query(User).filter_by(email=args['email']).first()
        if user:
            return send_error('User already exists.')

        try:
            user = User(**args)
            db.session.add(user)
            db.session.commit()
            auth_token = user.encode_auth_token(user.id)
            return send_success('Successfully registered.', 201,
                                auth_token=auth_token.decode())
        except Exception as e:
            return send_error(str(e))


class LoginResource(Resource):
    def post(self):
        data = get_json()
        email, password = data['email'], data['password']

        user = db.session.query(User).filter_by(email=email).first()
        if not user:
            return send_error('User does not exist.', 404)

        if bcrypt.check_password_hash(user.password, password):
            auth_token = user.encode_auth_token(user.id)
            return send_success('Successfully logged in.', 200,
                                auth_token=auth_token.decode())
        else:
            return send_error('Invalid login.', 401)


class LogoutResource(Resource):
    method_decorators = [validate_auth]

    def post(self, user_id=None):
        auth_token = flask.g.auth_token
        blacklist_token = BlacklistToken(token=auth_token)
        try:
            db.session.add(blacklist_token)
            db.session.commit()
            return send_success('Successfully logged out')
        except Exception as e:
            return send_error(str(e))


class EntryResource(Resource):
    method_decorators = [validate_auth]

    def get(self, user_id=None, entry_id=None):
        entries = db.session.query(Entry).filter_by(user_id=user_id)

        if not entry_id:
            return send_data(EntrySchema(many=True).dump(
                entries.order_by(Entry.date.desc()).all()).data)

        entry = entries.filter_by(id=entry_id).first()
        if not entry:
            return send_error('Invalid entry id', 404)

        return send_data(EntrySchema().dump(entry).data)

    def post(self, user_id=None, entry_id=None):
        args, errors = EntrySchema().load(get_json())
        if errors:
            return send_error(errors)

        entry = Entry(user_id=user_id, **args)
        try:
            db.session.add(entry)
            db.session.commit()
            return send_data(EntrySchema().dump(entry).data, 201)
        except Exception as e:
            return send_error(str(e))

    def put(self, entry_id, user_id=None):
        entry = db.session.query(Entry).filter_by(
            user_id=user_id, id=entry_id).first()

        if not entry:
            return send_error('Invalid entry id', 404)

        entry_dict = EntrySchema().dump(entry).data
        entry_dict.update(get_json())

        if entry_dict['rating'] == 0:
            entry_dict['rating'] = None

        args, errors = EntrySchema().load(entry_dict)
        if errors:
            return send_error(errors)

        for k, v in args.items():
            setattr(entry, k, v)

        try:
            db.session.add(entry)
            db.session.commit()
            return send_data(EntrySchema().dump(entry).data, 200)
        except Exception as e:
            return send_error(str(e))

    def delete(self, entry_id, user_id=None):
        entry = db.session.query(Entry).filter_by(
            user_id=user_id, id=entry_id).first()

        if not entry:
            return send_error('Invalid entry id', 404)

        try:
            db.session.delete(entry)
            db.session.commit()
            return send_success('Successfully deleted entry.', 200)
        except Exception as e:
            return send_error(str(e))


def create_apis(api):
    api.add_resource(UserResource, '/user')
    api.add_resource(EntryResource, '/entry/<int:entry_id>', '/entry')
    api.add_resource(LoginResource, '/login')
    api.add_resource(LogoutResource, '/logout')
    api.add_resource(RegisterResource, '/register')


def register_error_handlers(app):
    @app.errorhandler(InvalidJSONException)
    def invalid_json(error):
        return send_error('Invalid JSON body')
