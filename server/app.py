#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    restaurants = Restaurant.query.all()
    result = []
    for restaurant in restaurants:
        result.append({
            'id': restaurant.id,
            'name': restaurant.name,
            'address': restaurant.address
        })
    return jsonify(result)

class RestaurantResource(Resource):
    def get(self, id):
        with db.session() as session:
            restaurant = session.get(Restaurant, id)

            if restaurant:
                return make_response(jsonify(restaurant.to_dict()), 200)
            return make_response(jsonify({"error": "Restaurant not found"}), 404)

    def delete(self, id):
        with db.session() as session:
            restaurant = session.get(Restaurant, id)

            if restaurant:
                session.query(RestaurantPizza).filter_by(restaurant_id=id).delete()
                session.delete(restaurant)
                session.commit()
                return make_response('', 204)
            return make_response(jsonify({"error": "Restaurant not found"}), 404)

class PizzasResource(Resource):
    def get(self):
        with db.session() as session:
            pizzas = session.query(Pizza).all()
            return make_response(jsonify([pizza.to_dict(exclude=['restaurant_pizzas']) for pizza in pizzas]), 200)

class RestaurantPizzasResource(Resource):
    def post(self):
        data = request.get_json()
        price = data.get("price")
        pizza_id = data.get("pizza_id")
        restaurant_id = data.get("restaurant_id")

        if not (1 <= price <= 30):
            return make_response(jsonify({"errors": ["validation errors"]}), 400)

        with db.session() as session:
            pizza = session.get(Pizza, pizza_id)
            restaurant = session.get(Restaurant, restaurant_id)

            if not pizza or not restaurant:
                return make_response(jsonify({"errors": ["Pizza or Restaurant not found"]}), 404)

            restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
            session.add(restaurant_pizza)
            session.commit()

            restaurant_pizza_data = restaurant_pizza.to_dict()
            restaurant_pizza_data["pizza"] = pizza.to_dict(exclude=["restaurant_pizzas"])
            restaurant_pizza_data["restaurant"] = restaurant.to_dict(exclude=["restaurant_pizzas"])

        return make_response(jsonify(restaurant_pizza_data), 201)
    
api.add_resource(RestaurantResource, '/restaurants/<int:id>')
api.add_resource(PizzasResource, '/pizzas')
api.add_resource(RestaurantPizzasResource, '/restaurant_pizzas')

if __name__ == "__main__":
    app.run(port=5555, debug=True)
