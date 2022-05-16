from flask import Flask, render_template, request, url_for, redirect, jsonify, session
import datetime as dt
import configparser
import mysql.connector
import requests, json
import urllib3, urllib.parse
from urllib3.exceptions import NewConnectionError


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config = configparser.ConfigParser()
config.read('Config.ini')

#NetMRI Config Settings
nm_host = config['DEFAULT']['NETMRI_HOST']
nm_url = config['DEFAULT']['NETMRI_URL']
nm_user = config['DEFAULT']['NETMRI_USER']
nm_password = config['DEFAULT']['NETMRI_PASSWORD']
nm_use_ssl = config['DEFAULT']['NETMRI_USE_SSL']
nm_api_version = config['DEFAULT']['NETMRI_API_VERSION']
nm_ssl_verify = config['DEFAULT']['NETMRI_SSL_VERIFY']

db_user =(config['DEFAULT']['DB2_USER'])
db_pass =(config['DEFAULT']['DB2_PASS'])
db_host =(config['DEFAULT']['DB2_HOST'])
db      =(config['DEFAULT']['DB2'])

cnx = None

nm_device_group = "25"

#cnx = mysql.connector.connect(user=db_user, password=db_pass, host=db_host, database=db)
#cursor = cnx.cursor(buffered=True,dictionary=True)

class StatusException(Exception):
    def __init__(self, message):
        self.message = message


app = Flask(__name__)
flask_secret = (config['DEFAULT']['FLASK_SECRET_KEY'])
app.secret_key= flask_secret

@app.route('/discovery')
def discovery():
    if "username" in session:
        print(session['username'])
        rows=[]
        cnx = mysql.connector.connect(user=db_user, password=db_pass, host=db_host, database=db)
        cursor = cnx.cursor(buffered=True,dictionary=True)
        query = 'SELECT * \
        FROM GSAC.nm_discovery;'
        resultValue = cursor.execute("SELECT * FROM GSAC.nm_discovery1 ORDER BY submit_time DESC")
        rows = cursor.fetchall()
        cursor.close()
        cnx.close()
        print(len(rows))
        if len(rows) > 0:
            print(rows[0])
            return render_template('discovery.html', rows=rows)
        else:
            return "No Rows in Database"
    else:
        return redirect(url_for("login"))

@app.route('/discovernow', methods=['GET', 'POST'])
def discovernow():
    if "username" in session:
        if request.method == 'POST':
            #Discovery IP is returned from HTTP:
            discoveryip = request.form['discoveryip']
            print("At Discover Now")

            try:
                print("Trying DiscoverNow")
                url = "https://netmri.sce.com/api/3.5/discovery_statuses/discover_now?ip_address={}".format(discoveryip)

                print(url)

                response = requests.get(url, auth=(nm_user, nm_password), headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False)
                print(response)
                if response.status_code == 200:
                    print(response.text)
                    json_response = json.loads(response.text)
                    discovery_id = json_response['id']
                    address=discoveryip
                    user = session['username']
                    submit_time=dt.datetime.now()
                    values=(discovery_id, user, address, submit_time)
                    print(values)
                    cnx = mysql.connector.connect(user=db_user, password=db_pass, host=db_host, database=db)
                    cursor = cnx.cursor(buffered=True,dictionary=True)
                    sql_insert = '\
                        INSERT INTO GSAC.nm_discovery1 \
                            (discovery_id, \
                            user, \
                            address, \
                            submit_time) \
                            VALUES (%s, %s, %s, %s);'

                    cursor.execute(sql_insert, values)
                    cnx.commit()
                    cursor.close()
                    cnx.close()

                else:
                    return response.text

            except StatusException as e:
                print("Failed to send request: ", e)

            except Exception as e:
                print("Failed to retrieve accounts: ", e)

            #return discovery_id
            return redirect('/discovery')

        else:
            print('--- No POST')
            print(discoveryip)
            return response
    else:
        return render_template("login.html")


@app.route('/discovery_status', methods=['GET', 'POST'])
def discovery_status():
    if request.method == 'POST':
        #Discovery IP is returned from HTTP:
        discoveryip = request.form['discovery_id']

        try:
            url = "https://netmri.sce.com/api/3.5/discovery_statuses/discover_now?id={}".format(discoveryip)
            print(url)

            response = requests.get(url, auth=(nm_user, nm_password), headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False)
            print(response)
            if response.status_code == 200:
                print(response.text)
                json_response = json.loads(response.text)

                output = json_response['output']

                return jsonify({'output':': ' + output})

            else:
                return response.text

        except requests.exceptions.RequestException as error:
            print("Error: ", error)


        #return discovery_id
        return redirect('/discovery')

    else:
        print('--- No POST')
        print(discoveryip)
        return response

@app.route("/login", methods=["POST","GET"])
def login():

    if request.method == "POST":
        # Input from HTML Forms
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        
        # Set the Session Attribute
        session["username"] = username

        # Parse the NetMRI Password
        parsed_pw = urllib.parse.quote_plus(password)

        # Set the NetMRI Authentication Check
        url = "https://{}/api/authenticate?username={}&password={}".format(nm_host, username, parsed_pw)
        response = requests.get(url, headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False)
        print(response)
        if response.status_code == 200:
            # Send to the discovery page (PASSED AUTH)
            return redirect(url_for("discovery"))

        else:
            # Back to login page (FAILED AUTH)
            return render_template("login.html")

    else:
        # GET REQUEST 
        return render_template("login.html")



@app.route('/devices')
def devices():
    if "username" in session:
        print(session['username'])
        return render_template('devices.html')
    else:
        return redirect(url_for("login"))      
        
        

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/table")
def table():
    if "username" in session:
        print(session['username'])
        return render_template('devices.html')
        """
        limit=2100
        try:
            #url="I see you {}".format(nm_host)
            url = "https://{}/api/3.5/devices/find?DeviceGroupID={}&limit={}".format(nm_host, nm_device_group, limit)
            print(url)

            response = requests.get(url, auth=(nm_user, nm_password), headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False)
            print(response)
            if response.status_code == 200:
                #print(response.text)
                json_response = json.loads(response.text)

                devices = json_response['devices']
                print(len(devices))
                return render_template('table.html', devices=devices)

                #return jsonify({'output':': ' + output})

            else:
                return response.text  

        except requests.exceptions.RequestException as error:
            print("Error: ", error) 
        """



@app.route("/device_table")
def device_table():
    if "username" in session:
        print(session['username'])
        limit=2100

        try:
            #url="I see you {}".format(nm_host)
            url = "https://{}/api/3.5/devices/find?DeviceGroupID={}&limit={}".format(nm_host, nm_device_group, limit)
            print(url)

            response = requests.get(url, auth=(nm_user, nm_password), headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False)
            print(response)
            if response.status_code == 200:
                #print(response.text)
                json_response = json.loads(response.text)

                data = {"data": json_response['devices']}

                return (data)

            else:
                print('error')
                return response.text  

        except requests.exceptions.RequestException as error:
            print("Error: ", error) 

@app.route("/table2")
def table2():
    return render_template('table2.html')

            
if __name__ == "__main__":
    app.run(debug=True, port=5050)