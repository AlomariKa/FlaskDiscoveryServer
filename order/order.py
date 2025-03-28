from flask import Blueprint,Flask,jsonify,request
#!pipenv install flask_restful
from flask_restful import Resource,Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text,DECIMAL
import requests
from py_eureka_client import eureka_client
# provides functionality for registering services with a Eureka Server and discovering other services
app = Flask(__name__)

# eureka_client.init(eureka_server="http://localhost:8761/eureka", # Specifies the URL of the Eureka Server where the service will register itself.
#                     app_name="order-service", # Sets the name of the application or service being registered. Other services will use this name to discover it.
#                     instance_ip ="127.0.0.1", # Specifies the IP address of the instance being registered (here, it's localhost)
#                     instance_port = 8002) # Specifies the port number on which this service is running.
# # The init method is used to configure the service and register it with the Eureka Server


# Discovery server URL
DISCOVERY_SERVER_URL = 'http://localhost:5000'
# config the connection string
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///order.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False

# intialize SQLAlchemy
db= SQLAlchemy(app)

api = Api(app)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    skuCode = db.Column(db.String(100), nullable = False)
    price = db.Column(db.DECIMAL(precision=10))
    quantity = db.Column(db.Integer, nullable = True)


    def to_dict(self):
        return {
            "id": self.id,
            "skuCode": self.skuCode,
            "price": self.price,
            "quantity": self.quantity
        }


class OrderResource(Resource):

    def get(self,id=None):
        if id is None:
            try:
               order = Order.query.all()
               return jsonify([order_line.to_dict() for order_line in order]) 
            except:
                return {"status": "Failed"}
        else:
            try:
                order_line = Order.query.get(id)
                if order_line is None:
                    return  jsonify({"error":"Not found!"})
                return jsonify(order_line.to_dict())
            except:
                return {"status": "Failed"}

    
    def post(self):
        try:
            #payload = request.get_json()
            data = request.json
            skuCode = data["skuCode"]
            quantity = data["quantity"]
            price = data["price"]
          
            if checkInventory(skuCode,quantity):
                # Create a new product
                new_order_line = Order(
                    skuCode=data['skuCode'],
                    quantity=data['quantity'],
                    price=data['price']
                )

                # Add to the database
                db.session.add(new_order_line)
                db.session.commit()
                return {"status": "Success", "orderLine" : data}
            else:
                return {"Statue" : "Out of Stock"}
             
        except Exception as e:
            return {"status": "Failed", "Error": str(e)}
    
    def put(self,id):
        # Extract data from the request body
        data = request.get_json()

        try:
            # Find the product by ID
            order_line = Order.query.get(id)
            if not order_line:
                return jsonify({"error": "Product not found"})

            # Update fields if they are provided in the request
            if 'skuCode' in data:
                order_line.skuCode = data['skuCode']
            if 'quantity' in data:
                order_line.quantity = data['quantity']
            if 'price' in data:
                order_line.price = data['price']

            # Commit the changes to the database
            db.session.commit()
        except:
            return {"status": "Failed"}
        return {"Method" : "PUT"}

    def delete(self,id):
        try:
            # Find the order by ID
            order_line = Order.query.get(id)
            if not order_line:
                return jsonify({"error": "Product not found"})

            # Delete the product from the database
            db.session.delete(order_line)
            db.session.commit()
            return jsonify({"message": f"Product with ID {id} deleted successfully"})
        except:
            return {"status": "Failed"}
        

api.add_resource(OrderResource,'/orders','/orders/<int:id>')


def checkInventory(skuCode,quantity):
    try:
        service_invetory_url = "http://localhost:8003/inventory"
        response = requests.get(service_invetory_url) # GET method .get
        response.raise_for_status()  # Raises an exception if the HTTP request returned an error (4xx/5xx).
        inventory = response.json()  # Parses the JSON and converts it into a Python dictionary or list response and stores it in the `inventory` variable.
        found = False
        for item in inventory:
            if skuCode == item["skuCode"] and item["quantity"]- quantity >=0:
                found = True
        return found
    except:
        return False


with app.app_context():
    db.create_all()

def register_service():
    """Register the service with the discovery server."""
    service_info = {
        "name": "order_service",
        "address": "http://localhost:8002"  # Address where this app is running
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
    app.run(debug=True,port=8002)