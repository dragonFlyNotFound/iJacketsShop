from flask import Flask, render_template, redirect, url_for, session, request, flash, Response
from forms import AddProduct, AddToCart, Checkout, Registration, Login, EditProduct, LoginAdmin, SearchProduct
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin
from db import db, db_init
from models import Product, Order, Order_Item, User

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flsite.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'my3rtmnlhg4g63jg7345ftyjt'

db_init(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к cайту"
login_manager.login_message_category = "success"


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(User.query.filter_by(id=user_id).first())


def handle_cart():
    products = []
    grand_total = 0
    index = 0
    quantity_total = 0

    for item in session['cart']:
        product = Product.query.filter_by(id=item['id']).first()

        quantity = int(item['quantity'])
        total = quantity * product.price
        grand_total += total

        quantity_total += quantity

        products.append({'id': product.id, 'name': product.name, 'price': product.price, 'image': product.image,
                         'quantity': quantity, 'total': total, 'index': index})
        index += 1

    grand_total_plus_shipping = grand_total + 1000

    return products, grand_total, grand_total_plus_shipping, quantity_total


@app.route('/')
@login_required
def index():
    if 'cart' not in session:
        session['cart'] = []
    products = Product.query.all()
    user = None
    if current_user.get_id():
        user = current_user.get_login()
    form = SearchProduct()
    form.search.data = request.args.get('search', '')
    search = request.args.get('search')
    if request.method == 'GET':
        if search:
            products = Product.query.filter(Product.name.contains(search)).all()
            if not products:
                flash("Товаров c данным названием не найдено", "error")
    return render_template('index.html', title="Главная страница", products=products, user=user, form=form)


@app.route('/product/<id>')
@login_required
def product(id):
    product = Product.query.filter_by(id=id).first()

    form = AddToCart()

    return render_template('view-product.html', title="Показать товар", product=product, form=form)


@app.route('/quick-add/<id>')
@login_required
def quick_add(id):
    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append({'id': id, 'quantity': 1})
    session.modified = True
    flash("Товар успешно добавлен в корзину", "success")

    return redirect(url_for('index'))


@app.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    if 'cart' not in session:
        session['cart'] = []

    form = AddToCart()

    if form.validate_on_submit():
        session['cart'].append({'id': form.id.data, 'quantity': form.quantity.data})
        session.modified = True
        flash("Товар успешно добавлен в корзину", "success")

    return redirect(url_for('index'))


@app.route('/cart')
@login_required
def cart():
    products, grand_total, grand_total_plus_shipping, quantity_total = handle_cart()

    return render_template('cart.html', title="Корзина", products=products, grand_total=grand_total,
                           grand_total_plus_shipping=grand_total_plus_shipping, quantity_total=quantity_total)


@app.route('/remove-from-cart/<index>')
@login_required
def remove_from_cart(index):
    del session['cart'][int(index)]
    session.modified = True
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    form = Checkout()

    products, grand_total, grand_total_plus_shipping, quantity_total = handle_cart()
    if not products:
        flash("Добавьте в корзину хотя бы 1 товар для оформления заказа", "error")
        return redirect(url_for('index'))
    if form.validate_on_submit():

        order = Order()
        form.populate_obj(order)
        order.status = 'Ожидается'
        order.userId = current_user.get_id()

        for product in products:
            order_item = Order_Item(quantity=product['quantity'], product_id=product['id'])
            order.items.append(order_item)

            product = Product.query.filter_by(id=product['id']).update({'stock': Product.stock - product['quantity']})

        db.session.add(order)
        db.session.commit()

        session['cart'] = []
        session.modified = True
        flash("Заказ успешно оформлен", "success")

        return redirect(url_for('index'))

    return render_template('checkout.html', title="Проверка", form=form, grand_total=grand_total,
                           grand_total_plus_shipping=grand_total_plus_shipping, quantity_total=quantity_total)


@app.route('/admin')
def admin():
    if isLoggedAdmin():
        products = Product.query.all()
        products_in_stock = Product.query.filter(Product.stock > 0).count()

        orders = Order.query.all()

        form = SearchProduct()
        form.search.data = request.args.get('search', '')
        search = request.args.get('search')
        if request.method == 'GET':
            if search:
                products = Product.query.filter(Product.name.contains(search)).all()
                if not products:
                    flash("Товаров c данным названием не найдено", "error")
        return render_template('admin/index.html', title="Админ панель", admin=True,
                               products=products, products_in_stock=products_in_stock,
                               orders=orders, form=form)
    else:
        return redirect(url_for('login_admin'))


@app.route('/admin/add', methods=['GET', 'POST'])
def add():
    if isLoggedAdmin():
        form = AddProduct()

        if form.validate_on_submit():
            image = request.files['image']

            imageName = secure_filename(image.filename)
            imageType = image.mimetype

            new_product = Product(name=form.name.data, price=form.price.data, stock=form.stock.data,
                                  description=form.description.data, image=image.read(),
                                  image_name=imageName, image_type=imageType)

            flash("Товар успешно добавлен", "success")
            db.session.add(new_product)
            db.session.commit()

            return redirect(url_for('admin'))

        return render_template('admin/add-product.html', title="Добавить новый товар", admin=True,
                               form=form)
    else:
        return redirect(url_for('login_admin'))


@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
def edit(product_id):
    if isLoggedAdmin():
        form = EditProduct()

        product = db.session.query(Product).filter_by(id=product_id).one()
        form.name.data = product.name
        form.price.data = product.price
        form.stock.data = product.stock
        form.description.data = product.description
        if form.validate_on_submit():
            product.name = request.form['name']
            product.price = request.form['price']
            product.stock = request.form['stock']
            product.description = request.form['description']
            db.session.add(product)
            db.session.flush()
            db.session.commit()
            flash("Товар успешно изменен", "success")
            return redirect(url_for('admin'))

        return render_template('admin/edit-product.html', title="Изменить товар", admin=True,
                               form=form, productId=product_id)
    else:
        return redirect(url_for('login_admin'))


@app.route('/admin/delete/<int:product_id>', methods=['GET', 'POST'])
def deleteProduct(product_id):
    if isLoggedAdmin():
        product = db.session.query(Product).filter_by(id=product_id).one()
        order_item = db.session.query(Order_Item).filter_by(product_id=product_id).all()
        for current_order_item in order_item:
            db.session.delete(current_order_item)
        db.session.delete(product)
        db.session.flush()
        db.session.commit()
        flash("Товар успешно удален", "success")
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('login_admin'))


@app.route('/admin/order/<int:order_id>/delete', methods=['GET', 'POST'])
def deleteOrder(order_id):
    if isLoggedAdmin():
        order = db.session.query(Order).filter_by(id=order_id).one()
        order_item = db.session.query(Order_Item).filter_by(order_id=order_id).all()
        for current_order_item in order_item:
            db.session.delete(current_order_item)
        db.session.delete(order)
        db.session.flush()
        db.session.commit()
        flash("Заказ успешно удален", "success")
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('login_admin'))


@app.route('/admin/order/<order_id>')
def order(order_id):
    if isLoggedAdmin():
        order = Order.query.filter_by(id=int(order_id)).first()
        user = User.query.filter_by(id=order.userId).first()

        return render_template('admin/view-order.html', title="Детали заказа", order=order,
                               user=user, admin=True)
    else:
        return redirect(url_for('login_admin'))


@app.route('/admin/login', methods=["POST", "GET"])
def login_admin():
    form = LoginAdmin()
    if form.validate_on_submit():
        if request.form['user'] == "admin" and request.form['password'] == "12345":
            loginAdminAction()
            flash('Вы успешно авторизовались', "success")
            return redirect(url_for('admin'))
        else:
            flash("Неверная пара логин/пароль", "error")

    return render_template('admin/login.html', title='Авторизация в админ-панель', form=form)


@app.route('/admin/logout', methods=["POST", "GET"])
def logout_admin():
    if not isLoggedAdmin():
        return redirect(url_for('login_admin'))

    logoutAdminAction()

    return redirect(url_for('login_admin'))


def loginAdminAction():
    session['admin_logged'] = 1


def isLoggedAdmin():
    return True if session.get('admin_logged') else False


def logoutAdminAction():
    session.pop('admin_logged', None)


@app.route('/registration', methods=["POST", "GET"])
def registration():
    form = Registration()
    users = User.query.all()
    if form.validate_on_submit():
        try:
            user = User()
            form.populate_obj(user)
            user.password = generate_password_hash(form.password.data)
            for i in range(len(users)):
                if users[i].login == user.login:
                    flash("Пользователь с таким login уже существует", "error")

            db.session.add(user)
            db.session.commit()
            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash("Ошибочка регистрации", "error")

    return render_template('registration.html', title="Регистрация", form=form)


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        flash("Вы уже авторизованы", "success")
        return redirect(url_for('index'))
    form = Login()

    if form.validate_on_submit():
        user = User.query.filter_by(login=request.form['login']).first()
        if user and check_password_hash(user.password, request.form['password']):
            userLogin = UserLogin().create(user)
            rm = True if request.form.get('remember') else False
            login_user(userLogin, remember=rm)
            return redirect(url_for('index'))
        flash("Неверная пара логин/пароль", "error")

    return render_template("login.html", title="Авторизация", form=form)


@app.route("/showImage/<id>")
@login_required
def showImage(id):
    myProduct = Product.query.filter_by(id=id).first()
    return Response(myProduct.image, mimetype=myProduct.image_type)


@app.route("/logout")
def logout():
    logout_user()
    session['cart'] = []
    session.modified = True
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/search', methods=["POST", "GET"])
def searchProducts():
    form = SearchProduct()
    form.search.data = request.args.get('search', '')
    search = request.args.get('search')
    user = None
    if current_user.get_id():
        user = current_user.get_login()
    products = []
    if request.method == 'GET':
        if search:
            products = Product.query.filter(Product.name.contains(search)).all()
            if not products:
                flash("Товаров c данным названием не найдено", "error")

    return render_template('index.html', title="Поиск товара по названию", user=user, form=form,
                           products=products)


if __name__ == '__main__':
    app.run()
