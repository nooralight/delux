from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.base.exceptions import TwilioRestException
from flask import Flask, request,session,render_template,redirect,url_for, send_file
from flask_session import Session
from datetime import timedelta
from mongoengine import *
import datetime

import os
from dotenv import load_dotenv
load_dotenv()

account_sid = os.getenv('ACCOUNT_SID')
auth_token = os.getenv('AUTH_TOKEN')
phone_number = os.getenv('PHONE_NUMBER')
messaging_sid=os.getenv('MESSAGING_SID')
client = Client(account_sid, auth_token)

app = Flask(__name__)
app.config['secret_key'] = '6000d5d9e4405020d527f0587538vdhr'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
connect(host="mongodb://127.0.0.1:27017/delux?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+1.10.1")
class User(Document):
    id = SequenceField(primary_key=True)
    whatsapp_number = StringField(required=True)
    created_at= DateTimeField()

class Chat_history(Document):
    id = SequenceField(primary_key=True)
    whatsapp_number = StringField(required=True)
    user_reply = StringField(default = "no message")
    bot_message = StringField(default="no message")
    created_at= DateTimeField()

class Delux_admin(Document):
    id = SequenceField(primary_key=True)
    email = EmailField()
    password = StringField()

def convert_to_html(sentence):
    html_sentence = ""
    start_bold = False
    start_italic = False
    start_strike = False
    start_pre = False
    code_count = 0
    for char in sentence:
        #print(char+"\n")
        if char == "*":
            if not start_bold:
                html_sentence += "<b>"
                start_bold = True
            else:
                html_sentence += "</b>"
                start_bold = False

        elif char == "\n":
            html_sentence += "<br>"

        elif char == "_":
            if not start_italic:
                html_sentence += "<i>"
                start_italic = True
            else:
                html_sentence += "</i>"
                start_italic = False
        
        elif char == "~":
            if not start_strike:
                html_sentence += "<s>"
                start_strike = True
            else:
                html_sentence += "</s>"
                start_strike = False
        
        elif char == "`":
            code_count += 1
            if code_count == 3 and not start_pre:
                html_sentence += "<code style=\"color:black\">"
                start_pre = True
                code_count = 0

            elif code_count == 3 and start_pre:
                html_sentence += "</code>"
                start_pre = False
                code_count =0
        else:
            html_sentence += char
    return html_sentence

@app.route('/media/<filename>')
def serve_image(filename):
    print("Incomed Successfully!")
    pwd = os.getcwd()
    image_path = "/var/www/html/static/"+filename 
    try:
        print('done sending pic!')
        return send_file(image_path, mimetype='image/jpg')
    except:
        print("Not successfull")

@app.route('/login', methods=['GET','POST'])
def gotoLogin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Delux_admin.objects(email=email, password=password).first()
        if user:
            # Redirect to the index page if the email and password match
            # Set the user_id in the session
            session['user_id'] = str(user.id)
            session['user']= 'available'
            return redirect('/')
        else:
            # Return to the login page if the email and password don't match
            return render_template('login.html')
    # Render the login page if the request method is GET
    return render_template('login.html')

@app.route('/', methods=['GET','POST'])
def index():
    if 'user_id' not in session:
        # Redirect to the login route if user_id is not set
        return redirect('/login')
    users = User.objects()
    # Send the users as context to the index.html template
    return render_template('registered_users.html', users=users)


# Route to retrieve chat history based on whatsapp_number
@app.route('/chat_history',methods=['GET','POST'])
def get_chat_history():
    if 'user_id' not in session:
        # Redirect to the login route if user_id is not set
        return redirect('/login')
    # Query the Chat_history collection for matching objects
    chat_history = Chat_history.objects().order_by("-_id")

    # Send the chat history as context to the chat_history.html template
    return render_template('index.html', chat_history=chat_history)

@app.route('/send_message',methods=['GET','POST'])
def send_msg():
    if 'user_id' not in session:
        # Redirect to the login route if user_id is not set
        return redirect('/login')
    if request.method == 'POST':
        message = request.form['message']
        selected_checkboxes = request.form.getlist('event')
        file = request.files['file']
        if message:
            print("Real message: "+message)
            wp_message = message.replace('\n', '\\n')
            #edited_message = convert_to_html(message)
            
            print("HTML message: "+wp_message)
            if file:
                filename = file.filename
                image_path = "/var/www/html/media/"+filename
                file.save(image_path)
                pic_url="http://145.14.157.164/media/"+filename
                for number in selected_checkboxes:
                    message_created=client.messages.create(
                        from_=phone_number,
                        body=wp_message,
                        media_url = pic_url,
                        to=number
                    )
                return "okay"
            else:
                for number in selected_checkboxes:
                    message_created=client.messages.create(
                        from_=phone_number,
                        body=wp_message,
                        to=number
                    )
                return redirect("/")    
    else:
        users = User.objects()
        return render_template("message.html",users=users)
    # if request.method == 'POST':
    #     message = request.form['message']
    #     users = User.objects()
    #     for user in users:
    #         message_created=client.messages.create(
    #             from_=phone_number,
    #             body=message,
    #             to=user.whatsapp_number
    #         )
    #     print("Done sending message to all")
    #     return redirect('/')
    # else:
    #     return render_template("send_message_to_all.html")
    
# @app.route('/confirm/',methods=['GET','POST'])
# def confirm():
#     pic_url = None
#     if request.method == 'POST':
#         selected_checkboxes = request.form.getlist('event')
#         message = request.form['message']
#         msg = message.replace('\\n','\n')
#         print("Sending message: "+message)
#         if "pic_url" in request.form:
#             pic_url = request.form['pic_url']
#         for number in selected_checkboxes:
#             if pic_url:
#                 message_created=client.messages.create(
#                     from_=phone_number,
#                     body=msg,
#                     media_url = pic_url,
#                     to=number
#                 )
#             else:
#                 message_created=client.messages.create(
#                     from_=phone_number,
#                     body=msg,
#                     to=number
#                 )
#         print(selected_checkboxes)
#         return redirect('/')
#     else:
#         return render_template("send_message_to_all.html")

## Setting page
@app.route('/settings')
def settingAdmin():
    if 'user_id' not in session:
        # Redirect to the login route if user_id is not set
        return redirect('/login')
    user_id = session.get('user_id')
    user = Delux_admin.objects(id=user_id).first()
    return render_template("setting.html",user=user)

@app.route('/report')
def reportPage():
    if 'user_id' not in session:
        # Redirect to the login route if user_id is not set
        return redirect('/login')
    return render_template("report.html")

# Logout route
@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    # Redirect to the login page or any other public route
    return redirect(url_for('gotoLogin'))

if __name__ == "__main__":
    app.run(debug=True,port=8000)