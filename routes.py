from flask import Flask, render_template,url_for,request,flash,redirect,session, current_app,make_response
from application import RegistrationForm,LoginForm, Addproducts
from database import db, User, Brand, Category, Addproduct
from forms import (CustomerRegisterForm,CustomerLoginFrom,CustomerAddressForm,ResetPasswordForm,RequestResetForm)
from model import Register,CustomerOrder,CustomerAddress
from app import app,login_manager
from flask_login import login_required, current_user, logout_user, login_user
import secrets
import pdfkit
import os
from flask_mail import Mail,Message

mail=Mail(app)

@app.route('/customer/register', methods=['GET','POST'])
def customer_register():
    form = CustomerRegisterForm()
    if form.validate_on_submit():
        register = Register(name=form.name.data, username=form.username.data, email=form.email.data,password=form.password.data,country=form.country.data, city=form.city.data,contact=form.contact.data, address=form.address.data, zipcode=form.zipcode.data)
        db.session.add(register)
        flash(f'Welcome {form.name.data} Thank you for registering', 'success')
        db.session.commit()
        return redirect(url_for('customerLogin'))
    return render_template('customer/register.html', form=form)




@app.route('/customer/login', methods=['GET','POST'])
def customerLogin():
    form = CustomerLoginFrom()
    if form.validate_on_submit():
        user = Register.query.filter_by(email=form.email.data).first()
        if user and user.password==form.password.data:

            login_user(user)
            flash('You are login now!', 'success')
            next = request.args.get('next')
            return redirect(next or url_for('home'))
        flash('Incorrect email and password','danger')
        return redirect(url_for('customerLogin'))    
    return render_template('customer/login.html',form=form)

@app.route('/customer/logout')
def customer_logout():
	logout_user()
	return redirect(url_for('home'))



@app.route('/getorder')
@login_required
def get_order():
    if current_user.is_authenticated:
        customer_id = current_user.id
        invoice = secrets.token_hex(5)
        try:
            order = CustomerOrder(invoice=invoice,customer_id=customer_id,orders=session['Shoppingcart'])
            db.session.add(order)
            db.session.commit()
            session.pop('Shoppingcart')
            flash('Your order has been sent successfully','success')
            return redirect(url_for('orders',invoice=invoice))
        except Exception as e:
            print(e)
            flash('Some thing went wrong while get order', 'danger')
            return redirect(url_for('getCart'))

'''@app.route('/customer/address', methods=['GET','POST'])
@login_required
def CustomerAddress():
    form = CustomerAddressForm()
    if request.method== 'POST':
        zipcode=form.zipcode.data
        area=form.area.data
        email = form.email.data
        city = form.city.data
        name = form.name.data
        contact_no = form.contact_no.data
        addree = CustomerAddress(zipcode=zipcode, area=area, email=email, city=city, name=name, contact_no=contact_no)
        db.session.add(addree)
        db.session.commit()
        flash(f'The custmer {name} Address is added to your database','success')
        return redirect('admin')
        
    return render_template('customer/address.html',form=form)
'''
@app.route('/customer/address', methods=['GET','POST'])
def customer_address():
    form = CustomerAddressForm()
    if form.validate_on_submit():
        address = CustomerAddress(zipcode=form.zipcode.data, area=form.area.data, email=form.email.data, city=form.city.data, name=form.name.data, contact_no=form.contact_no.data)
        db.session.add(address)
        flash(f'Welcome {form.name.data} Thank you for adding address', 'success')
        db.session.commit()
        return render_template('customer/address.html', form=form)
    return render_template('customer/address.html', form=form)


@app.route('/orders/<invoice>')
@login_required
def orders(invoice):
    if current_user.is_authenticated:
        grandTotal = 0
        subTotal = 0
        customer_id = current_user.id
        customer = Register.query.filter_by(id=customer_id).first()
        orders = CustomerOrder.query.filter_by(customer_id=customer_id).order_by(CustomerOrder.id.desc()).first()
        for _key, product in orders.orders.items():
            discount = (product['discount']/100) * float(product['price'])
            subTotal += float(product['price']) * int(product['quantity'])
            subTotal -= discount
            tax = ("%.2f" % (.06 * float(subTotal)))
            grandTotal = ("%.2f" % (1.06 * float(subTotal)))

    else:
        return redirect(url_for('customerLogin'))
    return render_template('customer/order.html', invoice=invoice, tax=tax,subTotal=subTotal,grandTotal=grandTotal,customer=customer,orders=orders)





@app.route('/get_pdf/<invoice>', methods=['POST'])
@login_required
def get_pdf(invoice):
    if current_user.is_authenticated:
        grandTotal = 0
        subTotal = 0
        customer_id = current_user.id
        if request.method == "POST":
            customer = Register.query.filter_by(id=customer_id).first()
            orders = CustomerOrder.query.filter_by(customer_id=customer_id, invoice=invoice).order_by(CustomerOrder.id.desc()).first()
            for _key, product in orders.orders.items():
                discount = (product['discount']/100) * float(product['price'])
                subTotal += float(product['price']) * int(product['quantity'])
                subTotal -= discount
                tax = ("%.2f" % (.06 * float(subTotal)))
                grandTotal = float("%.2f" % (1.06 * subTotal))
            rendered =  render_template('customer/pdf.html', invoice=invoice, tax=tax,grandTotal=grandTotal,customer=customer,orders=orders)
            pdf = pdfkit.from_string(rendered, False)
            response = make_response(pdf)
            response.headers['content-Type'] ='application/pdf'
            response.headers['content-Disposition'] ='inline; filename='+invoice+'.pdf'
            return response
    return request(url_for('orders'))



@app.route('/orderlist')
def orderlist():
    order=CustomerOrder.query.all()
    return render_template('orderlist.html',order=order)

def send_reset_email(user):
    token=user.get_reset_token()
    msg= Message('Password reset request',sender='prabhakarsemwal1744@gmail.com',recipients=[user.email])
    msg.body=f''' To Reset your password,visit the folloing link :
    {url_for('reset_token',token=token ,_external=True)}
    if you do not make this request then simply ignore this email and no change '''


@app.route('/reset_password', methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))

    form=RequestResetForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email send by the instruction to reset your password','__info__')
        return(redirect(url_for('admin')))
    return render_template('customer/reset_request.html',title='Reset Password',form=form)


@app.route('/reset_password/<token>', methods=['GET','POST'])
def reset_token(token):
    
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    
    user=User.varify_reset_token(token) 

    if user is None:
        flash ('that is invalid or expired token ','warning')
        return redirect(url_for('reset_request'))
    form=ResetPasswordForm()
    if form.validate_on_submit():
        register = Register(name=form.name.data, username=form.username.data, email=form.email.data,password=form.password.data,country=form.country.data, city=form.city.data,contact=form.contact.data, address=form.address.data, zipcode=form.zipcode.data)
        db.session.add(register)
        flash(f'Welcome {form.name.data} Thank you for registering', 'success')
        db.session.commit()
    return redirect(url_for('customerLogin'))
    return render_template('customer/reset_token.html',title='Reset Password',form=form)




if __name__ == '__main__':
	app.run(debug=True)