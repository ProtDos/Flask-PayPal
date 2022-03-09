from flask import Flask, url_for, redirect, request

from config import config, interface

app = Flask(__name__)

@app.route("/")
def index():
    return """
        <a href="%s">
            <img src="https://www.paypalobjects.com/en_US/i/btn/btn_xpressCheckout.gif">
        </a>
        """ % url_for('paypal_redirect')

@app.route("/paypal/redirect")
def paypal_redirect():
    product_id = 0
    name = "Basic-DDoS-Protection"
    description = "basic description"
    frequency = 'MONTH'
    total_cycles = '0'
    price = '9.99'
    currency = 'USD',
    setup_fee = "0"
    setup_currency = "USD"
    tax_percentage = "0"

    kw = {
        "product_id": product_id,
        "name": name,
        "description": description,
        "status": "ACTIVE",
        "billing_cycles": [

            {
                "frequency": {
                    "interval_unit": frequency,
                    "interval_count": 1
                },
                "tenure_type": "REGULAR",
                "sequence": 1,
                "total_cycles": total_cycles,
                "pricing_scheme": {
                    "fixed_price": {
                        "value": price,
                        "currency_code": currency
                    }
                }
            }
        ],
        "payment_preferences": {
            "auto_bill_outstanding": "true",
            "setup_fee": {
                "value": setup_fee,
                "currency_code": setup_currency
            },
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3
        },
        "taxes": {
            "percentage": tax_percentage,
            "inclusive": "false"
        }
    }

    setexp_response = interface.set_express_checkout(**kw)
    return redirect(interface.generate_express_checkout_redirect_url(setexp_response.token))

@app.route("/paypal/confirm")
def paypal_confirm():
    getexp_response = interface.get_express_checkout_details(token=request.args.get('token', ''))

    if getexp_response['ACK'] == 'Success':
        return """
            Everything looks good! <br />
            <a href="%s">Click here to complete the payment.</a>
        """ % url_for('paypal_do', token=getexp_response['TOKEN'])
    else:
        return """
            Oh noes! PayPal returned an error code. <br />
            <pre>
                %s
            </pre>
            Click <a href="%s">here</a> to try again.
        """ % (getexp_response['ACK'], url_for('index'))


@app.route("/paypal/do/<string:token>")
def paypal_do(token):
    getexp_response = interface.get_express_checkout_details(token=token)
    kw = {
        'amt': getexp_response['AMT'],
        'paymentaction': 'Sale',
        'payerid': getexp_response['PAYERID'],
        'token': token,
        'currencycode': getexp_response['CURRENCYCODE']
    }
    interface.do_express_checkout_payment(**kw)

    return redirect(url_for('paypal_status', token=kw['token']))

@app.route("/paypal/status/<string:token>")
def paypal_status(token):
    checkout_response = interface.get_express_checkout_details(token=token)

    if checkout_response['CHECKOUTSTATUS'] == 'PaymentActionCompleted':
        # Here you would update a database record.
        return """
            Awesome! Thank you for your %s %s purchase.
        """ % (checkout_response['AMT'], checkout_response['CURRENCYCODE'])
    else:
        return """
            Oh no! PayPal doesn't acknowledge the transaction. Here's the status:
            <pre>
                %s
            </pre>
        """ % checkout_response['CHECKOUTSTATUS']

@app.route("/paypal/cancel")
def paypal_cancel():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)
