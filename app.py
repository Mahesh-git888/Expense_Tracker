import os





from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
db = SQLAlchemy(app)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    filter_type = request.args.get('type')
    filter_category = request.args.get('category')
    filter_month = request.args.get('month')  # format: YYYY-MM

    transactions = Transaction.query

    if filter_type:
        transactions = transactions.filter_by(type=filter_type)
    if filter_category:
        transactions = transactions.filter_by(category=filter_category)
    if filter_month:
        year, month = map(int, filter_month.split('-'))
        transactions = transactions.filter(
            db.extract('year', Transaction.date) == year,
            db.extract('month', Transaction.date) == month
        )

    transactions = transactions.order_by(Transaction.date.desc()).all()

    income = sum(t.amount for t in transactions if t.type == 'income')
    expense = sum(t.amount for t in transactions if t.type == 'expense')
    balance = income - expense

    return render_template('index.html',
        transactions=transactions,
        income=income, expense=expense, balance=balance,
        filter_type=filter_type, filter_category=filter_category, filter_month=filter_month
    )


@app.route('/add', methods=['POST'])
def add_transaction():
    amount = float(request.form['amount'])
    type_ = request.form['type']
    category = request.form['category']
    description = request.form['description']
    new_trx = Transaction(amount=amount, type=type_, category=category, description=description)
    db.session.add(new_trx)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_transaction(id):
    trx = Transaction.query.get_or_404(id)
    db.session.delete(trx)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
