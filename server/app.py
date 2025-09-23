#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            if not data.get('username'):
                raise ValueError('Username must be present')
            if not data.get('password'):
                raise ValueError('Password must be present')
            
            user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            user.password_hash = data.get('password')
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return user.to_dict(), 201
        except (ValueError, IntegrityError) as e:
            return {'errors': [str(e)]}, 422

class CheckSession(Resource):
    def get(self):
        if 'user_id' in session:
            user = User.query.filter(User.id == session['user_id']).first()
            if user:
                return user.to_dict(), 200
        return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return {'error': 'Invalid username or password'}, 401
            
        user = User.query.filter(User.username == username).first()
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return user.to_dict(), 200
        return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        if 'user_id' in session and session['user_id']:
            session.pop('user_id')
            return '', 204
        return {'error': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        if 'user_id' not in session or not session['user_id']:
            return {'error': 'Unauthorized'}, 401
        recipes = Recipe.query.all()
        return [recipe.to_dict() for recipe in recipes], 200
    
    def post(self):
        if 'user_id' not in session or not session['user_id']:
            return {'error': 'Unauthorized'}, 401
        data = request.get_json()
        try:
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=session['user_id']
            )
            db.session.add(recipe)
            db.session.commit()
            return recipe.to_dict(), 201
        except (ValueError, KeyError) as e:
            return {'errors': [str(e)]}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Seed database if empty
        if User.query.count() == 0:
            from random import randint, choice as rc
            from faker import Faker
            
            fake = Faker()
            
            # Create users
            users = []
            usernames = []
            
            for i in range(20):
                username = fake.first_name()
                while username in usernames:
                    username = fake.first_name()
                usernames.append(username)
                
                user = User(
                    username=username,
                    bio=fake.paragraph(nb_sentences=3),
                    image_url=fake.url(),
                )
                user.password_hash = username + 'password'
                users.append(user)
            
            db.session.add_all(users)
            
            # Create recipes
            recipes = []
            for i in range(100):
                instructions = fake.paragraph(nb_sentences=8)
                
                recipe = Recipe(
                    title=fake.sentence(),
                    instructions=instructions,
                    minutes_to_complete=randint(15,90),
                )
                recipe.user = rc(users)
                recipes.append(recipe)
            
            db.session.add_all(recipes)
            db.session.commit()
    
    app.run(port=5555, debug=True)