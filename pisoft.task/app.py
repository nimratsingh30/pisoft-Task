from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'advanced_ecommerce_secret_key'

# Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///advanced_store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------------------------------------------------
# DATABASE MODELS & RELATIONSHIPS
# -------------------------------------------------------------

# Many-to-Many Link Table (Association Table between Order and Product)
order_products = db.Table('order_products',
    db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

# 1. Category Model (One-to-Many Relationship with Product)
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    # Relationship: Ek category ke paas multiple products ho sakte hain
    products = db.relationship('Product', backref='category', lazy=True)

# 2. Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    # Relationship 1-to-1: Product ka extra technical description
    # uselist=False isko One-to-One banata hai
    technical_detail = db.relationship('ProductDetail', backref='product', uselist=False, cascade="all, delete-orphan")

# 3. ProductDetail Model (One-to-One Partner with Product)
class ProductDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, unique=True)
    warranty = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)

# 4. Order Model (Many-to-Many Relationship with Product)
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    # Relationship: Ek order me kai products, ek product kai orders me
    products = db.relationship('Product', secondary=order_products, backref=db.backref('orders', lazy='dynamic'))

# -------------------------------------------------------------
# ROUTES & CONTROLLERS
# -------------------------------------------------------------

# 1. Dashboard / Main View (Data Fetching and Displaying)
@app.route('/')
def index():
    categories = Category.query.all()
    products = Product.query.all()
    orders = Order.query.all()
    return render_template('dashboard.html', categories=categories, products=products, orders=orders)

# 2. Form Action: Add Category (Simple Record)
@app.route('/add_category', methods=['POST'])
def add_category():
    name = request.form.get('category_name')
    if name:
        new_category = Category(name=name)
        db.session.add(new_category)
        db.session.commit()
    return redirect(url_for('index'))

# 3. Form Action: Add Product (Demonstrating One-to-Many & One-to-One via Form)
@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    price = float(request.form.get('price'))
    category_id = int(request.form.get('category_id'))
    
    # Technical Details fields (For One-to-One relationship)
    warranty = request.form.get('warranty')
    manufacturer = request.form.get('manufacturer')

    # Creating Product (One-to-Many link established via category_id)
    new_product = Product(name=name, price=price, category_id=category_id)
    db.session.add(new_product)
    db.session.flush() # Temp ID generate karne ke liye takki 1-to-1 me use ho sake

    # Creating Product Details (One-to-One link)
    new_detail = ProductDetail(product_id=new_product.id, warranty=warranty, manufacturer=manufacturer)
    db.session.add(new_detail)
    
    db.session.commit()
    return redirect(url_for('index'))

# 4. Form Action: Create Order (Demonstrating Many-to-Many Form)
@app.route('/create_order', methods=['POST'])
def create_order():
    customer_name = request.form.get('customer_name')
    selected_product_ids = request.form.getlist('product_ids') # Form se array milega check-boxes ka

    if customer_name and selected_product_ids:
        new_order = Order(customer_name=customer_name)
        
        # Selected IDs se products database se nikal kar list me append karna
        for p_id in selected_product_ids:
            product = Product.query.get(int(p_id))
            if product:
                new_order.products.append(product) # Appending to Many-to-Many Relationship
        
        db.session.add(new_order)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)