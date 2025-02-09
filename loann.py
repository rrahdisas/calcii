from flask import Flask, render_template, request, redirect, url_for, session
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session['salary'] = float(request.form['salary'])
        session['savings'] = float(request.form['savings'])
        session['extra_income'] = float(request.form['extra_income'])
        session['loans'] = []  # Reset loans list
        return redirect(url_for('add_loans'))
    return render_template('index.html')

@app.route('/add_loans', methods=['GET', 'POST'])
def add_loans():
    if request.method == 'POST':
        if 'delete' in request.form:  # Handle loan deletion
            loan_index = int(request.form['delete'])
            loans = session.get('loans', [])
            if 0 <= loan_index < len(loans):
                del loans[loan_index]
                session['loans'] = loans  # Update session
            return redirect(url_for('add_loans'))

        # Add a new loan
        loan_amount = float(request.form['loan_amount'])
        emi_months = int(request.form['emi_months'])
        current_emi = int(request.form['current_emi'])
        interest = float(request.form['interest'])

        loans = session.get('loans', [])
        loans.append({
            'loan_amount': loan_amount,
            'emi_months': emi_months,
            'current_emi': current_emi,
            'interest': interest
        })
        session['loans'] = loans  # Update session

        return redirect(url_for('add_loans')) if 'add_more' in request.form else redirect(url_for('select_savings'))
    
    return render_template('add_loans.html', loans=session.get('loans', []))

@app.route('/select_savings', methods=['GET', 'POST'])
def select_savings():
    if request.method == 'POST':
        session['savings_percent'] = float(request.form.get('savings_percent', 0))
        return redirect(url_for('summary'))
    return render_template('select_savings.html')

@app.route('/summary', methods=['GET', 'POST'])
def summary():
    salary = session.get('salary', 0)
    savings = session.get('savings', 0)
    extra_income = session.get('extra_income', 0)
    savings_percent = session.get('savings_percent', 0)
    loans = session.get('loans', [])

    if not loans:
        return render_template('summary.html', emi_schedule=[], loans=[])

    available_funds = salary + extra_income + (savings * (savings_percent / 100) if savings > 0 else 0)

    # Get the current month
    current_month = datetime.datetime.now().month

    emi_schedule = []
    max_end_month = max(current_month + loan['emi_months'] - loan['current_emi'] for loan in loans)

    for month in range(current_month, max_end_month + 1):
        total_emi = 0
        for loan in loans:
            start_month = current_month
            end_month = start_month + loan['emi_months'] - loan['current_emi']

            if start_month <= month <= end_month:
                monthly_interest_rate = loan['interest'] / (12 * 100)
                emi = (loan['loan_amount'] * monthly_interest_rate * (1 + monthly_interest_rate) ** loan['emi_months']) / ((1 + monthly_interest_rate) ** loan['emi_months'] - 1)
                total_emi += emi

        extra_needed = max(0, total_emi - available_funds)
        emi_schedule.append({'month': month, 'total_emi': round(total_emi, 2), 'extra_needed': round(extra_needed, 2)})

    return render_template('summary.html', emi_schedule=emi_schedule, loans=loans)

if __name__ == '__main__':
    app.run(debug=True)
