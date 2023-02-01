#! /usr/bin/env python3.6
"""
Python 3.6 or newer required.
"""
import json
import os
import stripe

# This is a public sample test API key.
# Don’t submit any personally identifiable information in requests made with this key.
# Sign in to see your own test API key embedded in code samples.
stripe.api_key = 'sk_test_51LySMHFEgyBBpYpU8YzB7WyWM2vWbaR8SbNVxepaNJphN62gfyngwdk8mTYJt55E0dWw894mWvxAq8TLdYvtMKWU00ppzgdG7j'

from flask import Flask, render_template, jsonify, request


app = Flask(__name__, static_folder='public',
            static_url_path='', template_folder='public')


def calculate_order_amount(items):
    # Replace this constant with a calculation of the order's amount
    # Calculate the order total on the server to prevent
    # people from directly manipulating the amount on the client
    return 1400

@app.route('/create-fc-session', methods=['POST'])
def create_fc_session():
    try:
        customer = stripe.Customer.create(email="neerajdaredevil@gmail.com", name="Neeraj")
        session = stripe.financial_connections.Session.create(
            account_holder={"type": "customer", "customer": customer["id"]},
            permissions=["balances", "ownership", "payment_method", "transactions"],
            )

        # data = json.loads(request.data)
        # Create a PaymentIntent with the order amount and currency
        # intent = stripe.PaymentIntent.create(
        #     amount=calculate_order_amount(data['items']),
        #     currency='usd',
        #     automatic_payment_methods={
        #         'enabled': True,
        #     },
        # )
        return jsonify({
            'clientSecret': session['client_secret']
        })
    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route('/create-payment-intent', methods=['POST'])
def create_payment():
    try:
        data = json.loads(request.data)
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=calculate_order_amount(data['items']),
            currency='usd',
            automatic_payment_methods={
                'enabled': True,
            },
        )
        return jsonify({
            'clientSecret': intent['client_secret']
        })
    except Exception as e:
        return jsonify(error=str(e)), 403
if __name__ == '__main__':
    app.run(port=4242)