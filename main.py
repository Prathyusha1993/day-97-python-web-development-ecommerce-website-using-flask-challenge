from flask import Flask, render_template, request, session, url_for, redirect
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
app.secret_key = os.urandom(24)  #required for sessions

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
        products = stripe.Product.list().data
        product_data = []  # create a list that will hold all of the product information
        for product in products:
            price_id = product.metadata.get('price_id')
            image_url = None  # set image url to none by default.
            if price_id:
                price = stripe.Price.retrieve(price_id)
                if hasattr(price, 'images') and price.images:  # check if the price object has images
                    image_url = price.images[0]
                else:
                    if hasattr(product, 'images') and product.images:  # check the product for images.
                        image_url = product.images[0]
            product_data.append({
                'name': product.name,
                'description': product.description,
                'price_id': price_id,
                'image_url': image_url
            })

        return render_template('index.html', products=product_data)

    except stripe.error.StripeError as e:
        print(f'Stripe api error:{e}')
        return render_template('index.html', products=[])

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    price_id = request.form.get('price_id')
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(price_id)
    session.modified = True  #required to save the session
    return redirect(url_for('cart'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    price_id = request.form.get('price_id')
    if 'cart' in session and price_id in session['cart']:
        session['cart'].remove(price_id)
        session.modified = True
    return redirect(url_for('cart'))


@app.route('/cart')
def cart():
    cart_items = []
    total = 0
    if 'cart' in session:
        for price_id in session['cart']:
            try:
                price = stripe.Price.retrieve(price_id)
                product = stripe.Product.retrieve(price.product)
                cart_items.append({
                    'name': product.name,
                    'price': price.unit_amount / 100,
                    'price_id': price_id
                })
                total += price.unit_amount / 100
            except stripe.error.StripeError as e:
                print(f'Stripe api error: {e}')
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    if 'cart' not in session or not session['cart']:
        return redirect(url_for('cart'))
    line_items = []
    for price_id in session['cart']:
        line_items.append({
            'price': price_id,
            'quantity': 1,
        })
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='subscription', #change to subscription mode.
            success_url=url_for('success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('cancelled', _external=True),
        )
        session['cart'] = []
        session.modified = True
        return redirect(checkout_session.url, code=303)
    except stripe.error.StripeError as e:
        return f"Stripe Error: {e}"

@app.route('/success')
def success():
    return 'Payment successful!'

@app.route('/cancelled')
def cancelled():
    return 'Payment cancelled!'

if __name__ == '__main__':
    app.run(debug=True)