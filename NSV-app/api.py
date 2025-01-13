from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from sqlalchemy.exc import SQLAlchemyError
from models.admin import Admin
from models.user import User

app = Flask(__name__)

# Database configuration
# Note: Using 'postgresql://' instead of 'postgres://'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://avnadmin:AVNS_dWN9U8tAIxdxc5b-ByF@nsv-aset-2024-nsv-aset.h.aivencloud.com:16519/defaultdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with error handling
try:
    db = SQLAlchemy(app)
except SQLAlchemyError as e:
    print(f"Database connection error: {e}")
    raise

# Sample model
class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.user_id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

# Routes with error handling
@app.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users])
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/<username>', methods=['GET'])
def get_user(username):
    try:
        user = User.query.filter_by(username=username).first()
        if user is None:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict())
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create tables with error handling
    with app.app_context():
        try:
            db.create_all()
        except SQLAlchemyError as e:
            print(f"Error creating tables: {e}")
            raise
    
    app.run(debug=True)