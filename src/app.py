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

proxies = {
        "http": "",
        "https": "",
        }

#cnx = mysql.connector.connect(user=db_user, password=db_pass, host=db_host, database=db)
#cursor = cnx.cursor(buffered=True,dictionary=True)

class StatusException(Exception):
    def __init__(self, message):
        self.message = message


app = Flask(__name__)
flask_secret = (config['DEFAULT']['FLASK_SECRET_KEY'])
app.secret_key= flask_secret
currentChassis = ""



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

                response = requests.get(url, auth=(nm_user, nm_password), headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False, proxies=proxies)
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

            response = requests.get(url, auth=(nm_user, nm_password), headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False, proxies=proxies)
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
        try:
            # Set the NetMRI Authentication Check
            url = "https://{}/api/authenticate?username={}&password={}".format(nm_host, username, parsed_pw)
            response = requests.get(url, headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False, proxies=proxies)
            print(response)
            if response.status_code == 200:
                # Send to the discovery page (PASSED AUTH)
                return redirect(url_for("discovery"))

            else:
                # Back to login page (FAILED AUTH)
                return render_template("login.html")

        except requests.exceptions.RequestException as error:
            print("Error: ", error)

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



@app.route("/device_table")
def device_table():
    if "username" in session:
        print(session['username'])
        limit=2000
        select="DeviceID,DeviceName,DeviceIPDotted,DeviceAssurance,DeviceSysLocation,DeviceModel"
        
        try:
            url = "https://{}/api/3.5/devices/find?DeviceGroupID={}&limit={}&select={}".format(nm_host, nm_device_group, limit, select)
            print(url)

            response = requests.get(url, auth=(nm_user, nm_password), headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False, proxies=proxies)
            print(response)
            if response.status_code == 200:
                json_response = json.loads(response.text)
                data = {"data": json_response['devices']}

                for row in data['data']:
                    row.update({'DeviceName': row['DeviceName'].upper() })

                return (data)

            else:
                print('error')
                return response.text

        except requests.exceptions.RequestException as error:
            print("Error: ", error)


@app.route("/chassis_table", methods=["POST","GET"])
def chassis_table():

    if request.method == 'POST':
        #print(request.json)
        print("At Post")
        parameters = dict(request.form)
        print(parameters['device_id'])
        deviceid = parameters['device_id']


        if "username" in session:
            print(session['username'])
            nonChassisClass=[{}]
            chassisLocater = "&PhysicalClass=chassis"

            try:
                url = "https://{}/api/3.5/device_physicals/find?DeviceID={}{}".format(nm_host, deviceid, chassisLocater)
                print(url)

                response = requests.get(url, auth=(nm_user, nm_password), headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False, proxies=proxies)
                print(response)
                if response.status_code == 200:

                    json_response = json.loads(response.text)

                    data = {"data": json_response['device_physicals']}
                    print(data)
                    return (data)

                else:
                    print('error')
                    return response.text

            except requests.exceptions.RequestException as error:
                print("Error: ", error)

@app.route('/update_chassis', methods=['GET', 'POST'])
def update_chassis():
    print("@ update_chassis")
    if "username" in session:
        if request.method == 'POST':
            parameters = dict(request.form)
            print(parameters)
            print("CRQ for this Chassis {}".format(parameters['install_record']))
            custom_fields = {
                'data_tag' : 'custom_device_tag',
                'install_record' : 'custom_asset_install_record',
                'install_date' : 'custom_asset_install_date',
                'rack' : 'custom_rack',
                'rack_elevation' : 'custom_rack_pos',
                'rack_units' : 'custom_rack_units'
                 }

            physical_id = parameters['physical_id']

            try:
                url = "https://{}/api/3.5/device_physicals/find?DevicePhysicalID={}".format(nm_host, physical_id)
                print(url)

                response = requests.get(url, auth=(nm_user, nm_password), headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False, proxies=proxies)
                print(response)
                if response.status_code == 200:
                    #print(response.text)
                    json_response = json.loads(response.text)

                    data = json_response['device_physicals'][0]
                    print(data)
                    print(data['custom_device_tag'])

                else:
                    print('error')
                    
                    #return response.text

            except requests.exceptions.RequestException as error:
                print("Error: ", error)



            for key,value in custom_fields.items():
                print(key,value)
                # CHECK IF COMPONENTS ATTRIBUTES VALUE MATCHES THE VALUE FROM THE POST PARAMETERS
                if data[value] == parameters[key]:
                    print("Match -> SideKick: {}  NetMRI {}".format(parameters[key], data[value]))

                else:
                    print("Don't Match -> SideKick: {}  NetMRI {}".format(parameters[key], data[value]))
                    
                    try:
                        url = "https://{}/api/3.5/device_physicals/update_custom_field?DevicePhysicalID={}&{}={}".format(nm_host, data['DevicePhysicalID'], value, parameters[key])
                        print(url)
                        response = requests.get(url, auth=(nm_user, nm_password), headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False, proxies=proxies)
                        

                        if response.status_code == 200:
                            print(response.status_code)
                            #print(response.text)
                            #json_response = json.loads(response.text)
                            #data = json_response
                            #print(data)


                        else:
                            print('error')
                            print(response.status_code)
                            #return response.text
                    
                    except requests.exceptions.RequestException as error:
                        print("Error: ", error)
                 

                print()

            return (request.form)


@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        #Discovery IP is returned from HTTP:
        device_id = request.form['device_id']

        try:
            url = "https://netmri.sce.com/api/3.5/infra_devices/running_config_text?DeviceID={}".format(device_id)
            print(url)

            response = requests.get(url, auth=(nm_user, nm_password), headers={"Content-Type" : "application/json", "Accept" : "application/json"}, verify=False, proxies=proxies)
            print(response)
            if response.status_code == 200:
                print(response.text)
                json_response = json.loads(response.text)

                output = json_response['running_config_text']

                return jsonify({'running_config_text':': ' + output})

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



@app.route("/table2")
def table2():
    return render_template('table2.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=5051)
