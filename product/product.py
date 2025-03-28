from flask import Blueprint,Flask,jsonify,request
#!pipenv install flask_restful
from flask_restful import Resource,Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text,DECIMAL
import requests


app = Flask(__name__)

# config the connection string
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///product.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False

# intialize SQLAlchemy
db= SQLAlchemy(app)

api = Api(app)

DISCOVERY_SERVER_URL = 'http://localhost:5000'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = False)
    description = db.Column(db.String(200), nullable = False)
    price = db.Column(db.DECIMAL(precision=10))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price
        }


class ProductResource(Resource):

    def get(self,id=None):
        if id is None:
            try:
               products = Product.query.all()
               return jsonify([product.to_dict() for product in products]) 
            except:
                return {"status": "Failed"}
        else:
            try:
                product = Product.query.get(id)
                if product is None:
                    return  jsonify({"error":"Not found!"})
                return jsonify(product.to_dict())
            except:
                return {"status": "Failed"}

        return {"Method" : "GET"}
    
    def post(self):
        try:
            #payload = request.get_json()
            data = request.json
            name = data["name"]
            description = data["description"]
            price = data["price"]

            print(data)            
            # Create a new product
            new_product = Product(
                name=data['name'],
                description=data['description'],
                price=data['price']
            )

            # Add to the database
            db.session.add(new_product)
            db.session.commit()
            return {"status": "Success", "product" : data} 
        except Exception as e:
            return {"status": "Failed", "Error": str(e)}
        return {"Method" : "POST"}
    
    def put(self,id):
        # Extract data from the request body
        data = request.get_json()

        try:
            # Find the product by ID
            product = Product.query.get(id)
            if not product:
                return jsonify({"error": "Product not found"})

            # Update fields if they are provided in the request
            if 'name' in data:
                product.name = data['name']
            if 'description' in data:
                product.description = data['description']
            if 'price' in data:
                product.price = data['price']

            # Commit the changes to the database
            db.session.commit()
        except:
            return {"status": "Failed"}
        return {"Method" : "PUT"}

    def delete(self,id):
        try:
            # Find the product by ID
            product = Product.query.get(id)
            if not product:
                return jsonify({"error": "Product not found"})

            # Delete the product from the database
            db.session.delete(product)
            db.session.commit()
            return jsonify({"message": f"Product with ID {id} deleted successfully"})
        except:
            return {"status": "Failed"}
        
        return {"Method" : "DEL"}

api.add_resource(ProductResource,'/products','/products/<int:id>')

with app.app_context():
    db.create_all()
def register_service():
    """Register the service with the discovery server."""
    service_info = {
        "name": "product_service",
        "address": "http://localhost:8001"  # Address where this app is running
    }
    try:
        response = requests.post(f"{DISCOVERY_SERVER_URL}/register", json=service_info)
        if response.status_code == 200:
            print("Service registered successfully!")
        else:
            print("Failed to register service:", response.json())
    except Exception as e:
        print("Error registering service:", str(e))

if __name__ == "__main__":
    register_service()
    app.run(debug=True,port=8001)