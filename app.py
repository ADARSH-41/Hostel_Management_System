from flask import Flask,redirect,url_for,render_template,request,flash,session,abort
from flask_session import Session
from key import secret_key,salt1,salt2
import flask_excel as excel
from s_token import token
from cmail import sendmail
from itsdangerous import URLSafeTimedSerializer as u
import mysql.connector
from io import BytesIO
import os

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
# mydb = mysql.connector.connect(host='localhost',user='root',password='19178',db='hostelmgmt')
db=os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']
with mysql.connector.connect(host=host,user=user,password=password,db=db) as conn:
    cursor=conn.cursor(buffered=True)
    cursor.execute('create table if not exists admins(username varchar(50) primary key,password varchar(50))')
    cursor.execute('insert into admins values("nallaadarsh81199@gmail.com","20VV1A1241")')
    cursor.execute('insert into admins values("praveenpandala915@gmail.com","20VV1A1247")')
    cursor.execute('insert into admins values("animireddiramesh@gmail.com","21VV5A1267")')
    cursor.execute('insert into admins values("eshwarsir@codegnan","eshwarsir")')
    cursor.execute('create table if not exists residents(fname varchar(50),lname varchar(50),email varchar(50) primary key,password varchar(50),mobile varchar(20),email_status enum("confirmed","not confirmed") default "not confirmed")')
    cursor.execute('create table if not exists residentdata(rid int primary key auto_increment,name varchar(50),phone varchar(20),mail varchar(50),block varchar(2),room int,fee int)')
    cursor.execute('alter table residentdata auto_increment=1101')
    cursor.execute('create table if not exists workersdata(wid int auto_increment primary key,name varchar(50),mobile varchar(20),mailid varchar(50),block varchar(2),role varchar(30),shift int)')
    cursor.execute("create table if not exists leaverequests(reqid int auto_increment primary key,sid int,reason varchar(100),reqdate timestamp default current_timestamp on update current_timestamp,letter longblob,status enum('pending','granted','rejected') default 'pending',foreign key(sid) references residentdata(rid))")
    cursor.execute("create table if not exists complaints(cid int auto_increment primary key,reid int,complaint varchar(100),attachments longblob,cdate timestamp default current_timestamp on update current_timestamp,foreign key(reid) references residentdata(rid))")
mydb = mysql.connector.connect(host=host,user=user,password=password,db=db)

@app.route('/')
def home():
    return render_template('loginHome.html')

@app.route('/studentlogin',methods=['GET','POST'])
def slogin():
    if session.get('user'):
        return redirect(url_for('profile'))
    if request.method=='POST':
        username=request.form['sname']
        password=request.form['spass']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from residents where email=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.execute('select count(*) from residents where email=%s and password=%s',[username,password])
            pcount = cursor.fetchone()[0]
            if pcount==1:
                session['user']=username
                cursor.execute('select email_status from residents where email=%s',[username])
                status=cursor.fetchone()[0]
                cursor.close()
                if status!='confirmed':
                    return redirect(url_for('inactive'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                cursor.close()
                flash('Wrong Password')
                return render_template('Slogin.html')
        else:
            cursor.close()
            flash('Invalid Username')
            return render_template('Slogin.html')
    return render_template('Slogin.html')

@app.route('/studentregistration',methods=['GET','POST'])
def sregister():
    if request.method=='POST':
        fname = request.form['sfname']
        lname = request.form['slname']
        email = request.form['smail']
        pwd = request.form['spass']
        rpwd = request.form['rspass']
        mobile = request.form['mobile']
        cursor = mydb.cursor(buffered=True)
        try:
            if pwd==rpwd:
                cursor.execute('insert into residents(fname,lname,email,password,mobile) values(%s,%s,%s,%s,%s)',(fname,lname,email,pwd,mobile))
                mydb.commit()
                flash('Registration Sucessful. Check mail inbox for verification mail')
            else:
                flash("Password and Re-Password are not same.Please Register again")
        except mysql.connector.IntegrityError:
            flash('Mail ID already in use')
        else:
            cursor.close()
    return render_template('Sregistration.html')

@app.route('/adminlogin',methods=['GET','POST'])
def admin():
    if session.get('auser'):
        return render_template('adminScreen.html')
    if request.method=='POST':
        adminname = request.form['aname']
        adminpass = request.form['apass']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from admins where username=%s',[adminname])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.execute('select count(*) from admins where username=%s and password=%s',[adminname,adminpass])
            pcount=cursor.fetchone()[0]
            if pcount==1:
                cursor.close()
                session['auser'] = adminname
                return redirect(url_for('console'))
            else:
                cursor.close()
                flash('Wrong Adminkey')
                return render_template('adminlogin.html')
        else:
            cursor.close()
            flash('Invalid AdminID')
            return render_template('adminlogin.html')
    return render_template('adminlogin.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=u(secret_key)
        email=serializer.loads(token,salt=salt1,max_age=120)
    except Exception as e:
        #print(e)
        abort(404,'Link expired')
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from residents where email=%s',[email])
        status=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            flash('Email already confirmed')
            return redirect(url_for('slogin'))
        else:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("update residents set email_status='confirmed' where email=%s",[email])
            mydb.commit()
            flash('Email confirmation success')
            return redirect(url_for('slogin'))

@app.route('/inactive')
def inactive():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from residents where email=%s',[username])
        status = cursor.fetchone()[0]
        if status=='confirmed':
            return redirect(url_for('profile'))
        else:
            return render_template('inactive.html')
    else:
        return redirect(url_for('slogin'))
    
@app.route('/resendconfirmation')
def resend():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from residents where email=%s',[username])
        status=cursor.fetchone()[0]
        cursor.execute('select email from residents where email=%s',[username])
        email=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            flash('Email already confirmed')
            return redirect(url_for('profile'))
        else:
            subject='Email Confirmation'
            confirm_link=url_for('confirm',token=token(email,salt1),_external=True)
            body=f"Please confirm your mail-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Confirmation link sent check your email')
            return redirect(url_for('inactive'))
    else:
        return redirect(url_for('login'))

@app.route('/logoutstudent')
def slogout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('slogin'))
    else:
        return redirect(url_for('slogin'))

@app.route('/logoutadmin')
def alogout():
    if session.get('auser'):
        session.pop('auser')
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('admin'))
    
@app.route('/forgetpassword',methods=['GET','POST'])
def sforgot():
    if request.method=='POST':
        email = request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from residents where email=%s',[email])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select email_status from residents where email=%s',[email])
            status=cursor.fetchone()[0]
            cursor.close()
            if status=='not confirmed':
                flash('Please Confirm Your Email First...')

    return render_template('forget.html')

@app.route('/reset/<token>',methods=['GET','POST'])
def reset(token):
    try:
        serializer=u(secret_key)
        email=serializer.loads(token,salt=salt2,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update users set password=%s where email=%s',[newpassword,email])
                mydb.commit()
                flash('Reset Successful')
                return redirect(url_for('login'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')

@app.route('/guestmode')
def guest():
    return render_template('home.html')

@app.route('/yourdashboard')
def dashboard():
    if session.get('user'):
        resident = session.get('user')
        return render_template('studentDashboard.html')
    else:
        return redirect(url_for('slogin'))
    
@app.route('/adminconsole')
def console():
    if session.get('auser'):
        return render_template('adminScreen.html')
    else:
        return redirect(url_for('admin'))
    
@app.route('/servicespricing')
def pricing():
    return render_template('pricing.html')

@app.route('/contact_us')
def contact():
    return render_template('developers.html')

#admin previliges

@app.route('/residentsdata')
def residents():
    if session.get('auser'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from residentdata')
        data=cursor.fetchall()
        cursor.close()
        return render_template('residentsdata.html',data=data)
    else:
        return redirect(url_for('admin'))
    
@app.route('/workersdata')
def workers():
    if session.get('auser'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from workersdata')
        data = cursor.fetchall()
        cursor.close()
        return render_template('workersdata.html',data=data)
    else:
        return redirect(url_for('admin'))
    
@app.route('/roomallocations')
def ralloc():
    if session.get('auser'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select rid,name,block,room from residentdata')
        data=cursor.fetchall()
        cursor.execute('select count(*) from residentdata')
        count=cursor.fetchone()[0]
        cursor.close()
        return render_template('rooms_allocation.html',data=data,total=100,count=count)
    else:
        return redirect(url_for('admin'))
@app.route('/newallocation',methods=['GET','POST'])
def newalloc():
    if session.get('auser'):
        if request.method=='POST':
            name=request.form['rname']
            phone=request.form['phone']
            mail=request.form['mail']
            block=request.form['block']
            room=request.form['room']
            if block=='A':
                fee=150000
            elif block=='B':
                fee=100000
            elif block=='C':
                fee=75000
            elif block=='D':
                fee=50000
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into residentdata(name,phone,mail,block,room,fee) values(%s,%s,%s,%s,%s,%s)',[name,phone,mail,block,room,fee])
            mydb.commit()
            cursor.close()
            flash('Room Alloted Successfully')
            return render_template('newAllocation.html')
        else:
            return render_template('newAllocation.html')
    else:
        return render_template('newAllocation.html')
        
        
@app.route('/leaverequests')
def leave():
    if session.get('auser'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select reqid,sid,name,block,room,reason,reqdate,letter,status from residentdata inner join leaverequests on residentdata.rid=leaverequests.sid')
        data=cursor.fetchall()
        cursor.close()
        return render_template('leaveRequests.html',data=data)
    else:
        alogout()
        return redirect(url_for('admin'))

@app.route('/leaveacceptd',methods=['GET','POST'])
def laccept():
    if session.get('auser'):
        if request.method=='POST':
            id=request.form['accept']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update leaverequests set status="granted" where reqid=%s',[id])
            mydb.commit()
            cursor.close()
            flash('leave granted')
            return redirect(url_for('leave'))
        else:
            return redirect(url_for('leave'))
    else:
        return redirect(url_for('admin'))
    
@app.route('/leaverejected',methods=['GET','POST'])
def lreject():
    if session.get('auser'):
        if request.method=='POST':
            id=request.form['reject']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update leaverequests set status="rejected" where reqid=%s',[id])
            mydb.commit()
            cursor.close()
            flash('leave rejected')
            return redirect(url_for('leave'))
        else:
            return redirect(url_for('leave'))
    else:
        return redirect(url_for('admin'))

@app.route('/complaintsbox')
def complaint():
    if session.get('auser'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select cid,reid,block,room,complaint,attachments,cdate from residentdata inner join complaints on residentdata.rid=complaints.reid')
        data=cursor.fetchall()
        cursor.close()
        return render_template('complaints.html',data=data)
    else:
        return redirect(url_for('admin'))
    
#resident previliges
@app.route('/residentprofile')
def profile():
    if session.get('user'):
        email = session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from residentdata where mail=%s',[email])
        data = list(cursor.fetchall())
        cursor.close()
        return render_template('studentProfile.html',i=data)
    else:
        return redirect(url_for('slogin'))
    
@app.route('/payfeedue',methods=['GET','POST'])
def payfee():
    if session.get('user'):
        email=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select fee from residentdata where mail=%s',[email])
        feedue=cursor.fetchone()[0]
        cursor.close()
        if request.method=='POST':
            email=session.get('user')
            id=request.form['rid']
            id=id[6:]
            amount = int(request.form['amount'])
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select fee from residentdata where rid=%s',[id])
            feedue=cursor.fetchone()[0]
            try:
                if feedue>=amount:
                    feedue=feedue-amount
                else:
                    feedue=0
                    flash('You paid excess. Noworries excess amount will be transferred towards next term')
                cursor.execute('update residentdata set fee=%s where rid=%s and mail=%s',[feedue,id,email])
                mydb.commit()
                cursor.close()
                return render_template('studentFee.html',feedue=feedue)
            except mysql.connector.IntegrityError:
                flash('Fee Payment Unsuccessful')
                return render_template('studentFee.html',feedue=feedue)
        return render_template('studentFee.html',feedue=feedue)
    else:
        return redirect(url_for('slogin'))
    
@app.route('/requestleave',methods=['GET','POST'])
def sleave():
    if session.get('user'):
        email=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select rid from residentdata where mail=%s',[email])
        id=cursor.fetchone()[0]
        cursor.execute('select reqid,reason,reqdate,letter,status from leaverequests where sid=%s',[id])
        data=cursor.fetchall()
        cursor.close()
        if request.method=='POST':
            rid=request.form['rid']
            reason=request.form['reason']
            letter=request.form['letter']
            rid=int(rid[6:])
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into leaverequests(sid,reason,letter) values(%s,%s,%s)',[rid,reason,letter])
            mydb.commit()
            cursor.close()
            flash('Request Submitted Successfully. Revisit this tab regularly for request update')
            return render_template('studentLeave.html',data=data)
        else:
            return render_template('studentLeave.html',data=data)
    else:
        return redirect(url_for('slogin'))

@app.route('/yourcomplaint',methods=['GET','POST'])
def scomplaint():
    if session.get('user'):
        email=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select rid from residentdata where mail=%s',[email])
        id=cursor.fetchone()[0]
        cursor.execute('select cid,complaint,attachments,cdate from complaints where reid=%s',[id])
        data=cursor.fetchall()
        if request.method=='POST':
            rid=request.form['rid']
            rid=rid[6:]
            complaint=request.form['complaint']
            attachments=request.form['attachments']
            atdata=attachments
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into complaints(reid,complaint,attachments) values(%s,%s,%s)',[rid,complaint,atdata])
            mydb.commit()
            cursor.close()
            flash('Complaint Filed Successfully...')
            return render_template('studentComplaint.html',data=data)
        return render_template('studentComplaint.html',data=data)
    else:
        return redirect(url_for('slogin'))


@app.route('/roommates')
def roommates():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        username=session.get('user')
        cursor.execute('select block,room from residentdata where mail=%s',[username])
        data1=cursor.fetchall()
        block=data1[0][0]
        room=data1[0][1]
        cursor.execute('select rid,name,phone,mail from residentdata where block=%s and room=%s',[block,room])
        data=cursor.fetchall()
        return render_template('roomMates.html',data=data)
    else:
        return redirect(url_for('slogin'))

if __name__=='__main__':
    app.run()