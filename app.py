from flask import Flask,Blueprint,redirect,url_for,render_template,request,session
from werkzeug.security import generate_password_hash,check_password_hash
from models import db,User

app=Flask(__name__)

app.config["SECRET_KEY"]="anythingworksherefornow"
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///database.db"

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signin",methods=["GET","POST"])
def signin():
    if request.method=="GET":
        return render_template("signin.html")
    
    elif request.method=="POST":
       
        username=request.form.get("username")
        userpassword=request.form.get("userpassword")        
        signinerror=""
        passworderror=""
        if username=="":
            signinerror="Email Required"
        if userpassword=="":
            passworderror="Password Required"
        if signinerror or passworderror:
            return render_template("signin.html",signinerror=signinerror,passworderror=passworderror,username=username,password=userpassword)
        else:
            return request.form

@app.route("/register",methods=["GET","POST"])    
def register():
    if request.method=="GET":
        return render_template("register.html")
    
    elif request.method=="POST":
        firstname=request.form.get("firstname")
        lastname=request.form.get("lastname")
        email=request.form.get("email")
        password=request.form.get("password")
        confirm_password=request.form.get("confirm_password")

        firstnameerror=""
        emailerror=""
        passworderror=""
        confirmpassworderror=""


        if firstname == "":
            firstnameerror = "Name Required"
            print("fn working")
        
        if email == "":
            emailerror = "Email Required"
            print("email owrking")

        

        if password=="":
            passworderror="Password Required!"
            print("whatever")

        elif confirm_password=="":
            confirmpassworderror="Confirm password required"
            print("cp working")
        
        elif password!=confirm_password:
            confirmpassworderror="Password doesn't match"
            print("match working")


        if firstnameerror or passworderror or emailerror or confirmpassworderror:
             return render_template("register.html",
                                firstname=firstname,
                                lastname=lastname,
                                email=email,
                                password=password,
                                confirm_password=confirm_password,
                                confirmpassworderror=confirmpassworderror, 
                                firstnameerror=firstnameerror,
                                emailerror=emailerror,
                                passworderror=passworderror)
        else:
            if lastname=="":
                lastname=None
            user=User(firstname=firstname,
                      lastname=lastname,
                      email=email,
                      password=generate_password_hash(password),
                      type="student")
            db.session.add(user)
            db.session.commit()

            return redirect("/signin")
        

