from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, CheckConstraint
from sqlalchemy.orm import validates, relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin

metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)

db = SQLAlchemy(metadata=metadata)


class Restaurant(db.Model, SerializerMixin):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    address = db.Column(db.String)

    restaurant_pizzas = relationship("RestaurantPizza", backref="restaurant", cascade="all, delete-orphan")
    pizzas = association_proxy("restaurant_pizzas", "pizza")

    serialize_rules = ("-restaurant_pizzas.restaurant", "-pizzas.restaurant_pizzas")

    def to_dict(self, exclude=None):
        if exclude is None:
            exclude = []
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name not in exclude}
        if 'restaurant_pizzas' not in exclude:
            data['restaurant_pizzas'] = [rp.to_dict() for rp in self.restaurant_pizzas]
        return data

    def __repr__(self):
        return f"<Restaurant {self.name}>"


class Pizza(db.Model, SerializerMixin):
    __tablename__ = "pizzas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    ingredients = db.Column(db.String)

    restaurant_pizzas = relationship("RestaurantPizza", backref="pizza", cascade="all, delete-orphan")
    restaurants = association_proxy("restaurant_pizzas", "restaurant")

    serialize_rules = ("-restaurant_pizzas.pizza", "-restaurants.restaurant_pizzas")

    def to_dict(self, exclude=None):
        if exclude is None:
            exclude = []
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name not in exclude}
        if 'restaurant_pizzas' not in exclude:
            data['restaurant_pizzas'] = [rp.to_dict() for rp in self.restaurant_pizzas]
        return data

    def __repr__(self):
        return f"<Pizza {self.name}, {self.ingredients}>"


class RestaurantPizza(db.Model, SerializerMixin):
    __tablename__ = "restaurant_pizzas"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False)
    pizza_id = db.Column(db.Integer, db.ForeignKey("pizzas.id"), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)

    serialize_rules = ("-restaurant.restaurant_pizzas", "-pizza.restaurant_pizzas")

    __table_args__ = (
        CheckConstraint('price >= 1 AND price <= 30', name='check_price_between_1_and_30'),
    )

    @validates("price")
    def validate_price(self, key, value):
        if not (1 <= value <= 30):
            raise ValueError("validation errors")
        return value

    def __repr__(self):
        return f"<RestaurantPizza ${self.price}>"
