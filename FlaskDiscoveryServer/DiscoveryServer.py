from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///discovery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define the Service model
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    address = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address
        }

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        service_name = data.get('name')
        service_address = data.get('address')
        
        if not service_name or not service_address:
            return jsonify({"error": "Invalid data"}), 400
        
        # Check if the service already exists
        existing_service = Service.query.filter_by(name=service_name).first()
        if existing_service:
            # Update the existing service's address
            existing_service.address = service_address
        else:
            # Create a new service entry
            new_service = Service(name=service_name, address=service_address)
            db.session.add(new_service)

        db.session.commit()
        return jsonify({"message": "Service registered successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/discover/<service_name>', methods=['GET'])
def discover(service_name):
    try:
        service = Service.query.filter_by(name=service_name).first()
        if service:
            service_dict = service.to_dict()
            return jsonify(service_dict["address"]), 200
        return jsonify({"error": "Service not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database and tables if they don't exist
    app.run(port=5000)  # Discovery server runs on port 5000
