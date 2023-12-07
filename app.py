from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
app.config['CKEDITOR_SERVE_LOCAL'] = True
ckeditor = CKEditor(app)
app.app_context().push()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(20), nullable=False)
    tags = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ArticleForm(FlaskForm):
    title = StringField('Title')
    content = TextAreaField('Content')
    tags = StringField('Tags')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    articles = Article.query.all()
    return render_template('home.html', articles=articles)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # You should hash the password before storing it in the database
        hashed_password = password  # Replace this with a proper password hashing method

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and password == user.password:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))

        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/create_article', methods=['GET', 'POST'])
@login_required
def create_article():
    form = ArticleForm()

    if form.validate_on_submit():
        article = Article(
            title=form.title.data,
            content=form.content.data,
            author=current_user.username,
            tags=form.tags.data,
            user_id=current_user.id
        )
        db.session.add(article)
        db.session.commit()
        flash('Article created successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('create_article.html', form=form)

@app.route('/edit_article/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    form = ArticleForm()

    if form.validate_on_submit():
        article.title = form.title.data
        article.content = form.content.data
        article.tags = form.tags.data
        db.session.commit()
        flash('Article updated successfully!', 'success')
        return redirect(url_for('home'))

    form.title.data = article.title
    form.content.data = article.content
    form.tags.data = article.tags

    return render_template('edit_article.html', form=form, article=article)

@app.route('/delete_article/<int:article_id>')
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    flash('Article deleted successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/search', methods=['GET'])
def search_articles():
    search_term = request.args.get('search', '')
    filter_by = request.args.get('filter', 'title')

    page = request.args.get('page', 1, type=int)
    per_page = 5

    if filter_by == 'title':
        articles = Article.query.filter(Article.title.ilike(f'%{search_term}%')).paginate(page=page, per_page=per_page, error_out=False)
    elif filter_by == 'author':
        articles = Article.query.filter(Article.author.ilike(f'%{search_term}%')).paginate(page=page, per_page=per_page, error_out=False)
    elif filter_by == 'tags':
        articles = Article.query.filter(Article.tags.ilike(f'%{search_term}%')).paginate(page=page, per_page=per_page, error_out=False)

    return render_template('home.html', articles=articles, search_term=search_term, filter_by=filter_by)

if __name__ == '__main__':
    app.run(debug=True)