from flask import Flask, render_template, jsonify
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import os
from dotenv import load_dotenv
import stripe

app = Flask(__name__)
bootstrap = Bootstrap5(app)

load_dotenv()
# Load environment variables
stripe.api_key = os.getenv('SECRET_KEY')

# create db
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class Product(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)

with app.app_context():
    # db.session.add(Product(name='Laptop', price=50000, description='A High-end laptop', image_url='https://via.placeholder.com/150'))
    # db.session.add(Product(name='Phone', price=10000, description='Smart phone with great features',
    #                        image_url='https://via.placeholder.com/150'))
    # db.session.add(Product(name='Tablet', price=20000, description='Portable tablet with large screen',
    #                        image_url='https://via.placeholder.com/150'))
    # db.session.commit()
    db.create_all()


@app.route('/', methods=['GET'])
def home():
    try:
        products = stripe.Product.list()
        return render_template('index.html', products=products.data)
    except stripe.error.StripeError as e:
        print(f'Error fetching products: {e}')
        return render_template('index.html', products=[])





if __name__ == '__main__':
    app.run(debug=True)