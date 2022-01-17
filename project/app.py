from datetime import datetime
from site import execusercustomize

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from datetime import datetime

pwd = {"dbproj":"dbproj1"}

rate = 15


app = Flask(__name__)

#Connect to database
db = SQL("sqlite:///D:\project/vpms.db")

#Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/", methods = ["POST","GET"])
def index():
    if not session.get("user"):
        return redirect("/login")
    
    else:
        return render_template("home.html")

@app.route("/login", methods = ["POST","GET"])
def login():
    if request.method=="GET":
        return render_template("index.html")
    else:
        name = request.form.get("name")
        password = request.form.get("password")
        if not name or not password:
            return render_template("failure1.html", message = "Please enter login details")
        elif name not in pwd or pwd[name] != password:
            return render_template("failure1.html", message = "Invalid Username or password")
        else:
            session["user"] = name
            return redirect("/")

@app.route("/bill", methods = ["POST","GET"])
def bill():
    if not session.get("user"):
        return redirect("/")

    Exit_time = datetime.now()
    Slip_id = request.form.get("Slip_id")
    Sid = request.form.get("Sid")
    Cid = request.form.get("Cid")
    # Entry_dict = db.execute("select Entry_time from Parking_slip where Slip_id=(?)", Slip_id)
    # Entry_time = Entry_dict[0]["Entry_time"]
    db.execute("Update Parking_slip set Exit_time=(?), has_paid='Yes' where Slip_id=(?)", Exit_time, Slip_id)
    db.execute("update Parking_slot set Is_available='Yes' where Sid=(?)", Sid)
    Reg_pass = db.execute("Select * from Regular_pass where Cid = (?) and ((julianday(Expiration_date)-julianday(?))*1440)>0", Cid, Exit_time)
    if Reg_pass:
        message = "Customer has valid pass"
        return render_template("bill.html", amount = 0, message = message)
    else:

        time_dict = db.execute("Select round((julianday(Exit_time)-julianday(Entry_time))*1440) as Total_time from Parking_slip where Slip_id = (?)", Slip_id)
        total_time = round(time_dict[0]["Total_time"],3)
        amount = rate * total_time
        if amount == 0:
            amount += 15
            return render_template("bill.html", amount = amount, message = None)
        else:
            return render_template("bill.html", amount = amount, message = None)

@app.route("/insert", methods = ["POST"])
def insert():
    if not session.get("user"):
        return redirect("/login")
    Entry_time = datetime.now()
    try:
        Cid = int(request.form.get("Cid"))
    except:
        return render_template("failure.html", message = "Invalid Customer ID")
    Sid = int(request.form.get("Sid"))
    Sid = int(request.form.get("Sid"))
    Vehicle_type1 = request.form.get("Vehicle_type")
    Vehicle_type = "%"+Vehicle_type1+"%"
    entries = db.execute("Select * from Parking_slip where Exit_time is NULL")
    for entry in entries:
        if entry["Cid"] == Cid:
            return render_template("failure.html", message="Customer has outstanding bills")
    entries1 = db.execute("select * from Customer where Cid=(?)", Cid)
    entries2 = db.execute("select * from Customer where Cid=(?) and Vehicle_type like (?)", Cid, Vehicle_type)
    if not entries1:
        message = "Invalid entry, Customer doesn't exist"
        return render_template("failure.html", message = message)
    elif not entries2:
        message = "Invalid entry, Customer does not own "+Vehicle_type1+" as per records. Please create new cuustomer entry"
        return render_template("failure.html", message = message)
    else:
        db.execute("update Parking_slot set Is_available = 'No' where Sid =(?)", Sid)
        db.execute("insert into Parking_slip (has_paid, Entry_time, Cid, Sid) values(?,?,?,?)", "No", Entry_time, Cid, Sid)
        return redirect("/logs")

@app.route("/logs", methods = ["POST","GET"])
def logs():

    if not session.get("user"):
        return redirect("/login")


    else:
        slips1 = db.execute("select Parking_slip.Cid as P_Cid, Customer.Cid as C_Cid, * from Parking_slip, Customer where P_Cid= C_Cid and Exit_time is NULL")
        slips2 = db.execute("select Parking_slip.Cid as P_Cid, Customer.Cid as C_Cid, * from Parking_slip, Customer where P_Cid= C_Cid and Exit_time is not NULL")
        return render_template("logs.html", slips1 = slips1, slips2 = slips2)

@app.route("/customers", methods = ["POST", "GET"])
def customers():
    if not session.get("user"):
        return redirect("/login")
    else:
        entries = db.execute("select * from Customer")
        return render_template("customers.html", entries = entries)



@app.route("/register", methods = ["POST","GET"])
def register():
    if not session.get("user"):
        return redirect("/login")
    elif request.method=="GET":
        return render_template("register.html")
    else:
        Name = request.form.get("Name")
        Vehicle_no = request.form.get("Vehicle_no")
        Vehicle_type = request.form.get("Vehicle_type")
        Contact_no = request.form.get("Contact_no")
        if not Name or not Vehicle_no or Vehicle_type == "Vehicle type" or not Contact_no:
            message = "Invalid entry, please enter appropriate values"
            return render_template("failure.html", message = message)
        else:
            try:
                db.execute("insert into Customer(Name,Vehicle_no, Vehicle_type,Contact_no) values(?,?,?,?)", Name, Vehicle_no, Vehicle_type, Contact_no)
                return render_template("home.html")
            except :
                message = "Invalid entry, possibly violating constraints"
                return render_template("failure.html", message = message)


        

@app.route("/allot", methods = ["POST","GET"])
def allot():
    if not session.get("user"):
        return redirect("/login")
    elif request.method == "GET":
        return render_template("type.html")
    else:
        Vehicle_type = request.form.get("type")
        if Vehicle_type == "Select":
            return render_template("failure.html", message = "Please enter Vehicle type")
        available = db.execute("select Sid, Wing_code, Parking_slot.Fid as Pfid, Floor.Fid as Ffid from Parking_slot, Floor where Pfid = Ffid and Is_available = 'Yes' and Vehicle_type = (?)", Vehicle_type)
        if not available:
            return render_template("failure.html", message = "No slot available")
        else:
            Fid = available[0]["Ffid"]
            Sid = available[0]["Sid"]
            Wing_code = available[0]["Wing_code"]
            return render_template("confirm.html", Sid = Sid, Wing_code=Wing_code, Fid=Fid, Vehicle_type = Vehicle_type)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")