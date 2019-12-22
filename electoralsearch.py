from flask import Flask, request, jsonify
import time
from PIL import Image
from selenium.webdriver import Chrome
from selenium.webdriver.support.select import Select
import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders
import sys

app = Flask(__name__)


def sendEmail(img_name, toaddr):
	fromaddr = "seleniumscrape@gmail.com"

	# instance of MIMEMultipart 
	msg = MIMEMultipart() 
	   
	msg['From'] = fromaddr 
	msg['To'] = toaddr 

	# storing the subject  
	msg['Subject'] = "Captcha Image"
	  
	# string to store the body of the mail 
	body = "Please Read the captcha and put in below link <br/>  http:13.233.173.135/captcha"
	  
	# attach the body with the msg instance 
	msg.attach(MIMEText(body, 'plain')) 
	  
	# open the file to be sent  
	filename = img_name
	attachment = open(img_name, "rb") 
	  
	# instance of MIMEBase and named as p 
	p = MIMEBase('application', 'octet-stream') 
	  
	# To change the payload into encoded form 
	p.set_payload((attachment).read()) 
	  
	# encode into base64 
	encoders.encode_base64(p) 
	   
	p.add_header('Content-Disposition', "attachment; filename= %s" % filename) 
	  
	# attach the instance 'p' to instance 'msg' 
	msg.attach(p) 
	  
	# creates SMTP session 
	s = smtplib.SMTP('smtp.gmail.com', 587) 
	  
	# start TLS for security 
	s.starttls() 
	  
	# Authentication 
	s.login(fromaddr, "selenium@123") 
	  
	# Converts the Multipart msg into a string 
	text = msg.as_string() 
	  
	# sending the mail 
	s.sendmail(fromaddr, toaddr, text) 
	  
	# terminating the session 
	s.quit()

def get_captcha_text(img_name,size):
    im = Image.open(img_name) # uses PIL library to open image in memory

    left = 266
    top = 345
    right = 266 + size['width']
    bottom = 345 + size['height']

    im = im.crop((left, top, right, bottom)) # defines crop points
    im.save(img_name)

def getData(epic_number, toaddr):
	try:
		global driver
		driver = Chrome("/usr/bin/chromedriver")
		driver.get('https://electoralsearch.in/')
		driver.set_window_size(1120, 850)

		# click on welcome button
		welcome_button = driver.find_elements_by_xpath("//*[@id='welcomeDialog']/div/div/div/input")[0]
		welcome_button.click()

		# and click on epic tab
		search_by_epic_number = driver.find_elements_by_xpath("//*[@role='tablist']/li[2]")[0]
		search_by_epic_number.click()

		# fill up the epic number
		text = driver.find_element_by_id('name')
		text.send_keys(epic_number)

		# # select state if you want
		# select_state=Select(driver.find_element_by_id('epicStateList'))
		# select_state.select_by_visible_text('Gujarat')
		element = driver.find_element_by_id('captchaEpicImg')
		# print (text.get_attribute('src'))
		location = element.location    
		size = element.size
		img_name = epic_number+'.png'
		driver.save_screenshot(img_name)
		get_captcha_text(img_name, size)
		sendEmail(img_name, toaddr)
	
	except Exception as e:
		driver.quit()


@app.route('/', methods=['POST'])
def enterEpicNumber():
	try:
		epic_number = request.json['epic_number']
		toaddr = request.json['toaddr']
		getData(epic_number, toaddr)
		return jsonify({'status': 'success', 'message': 'Please check Your Mail'})

	except Exception as e:
		return jsonify({'status': 'error', 'message': 'Please Try agian'})


@app.route('/captcha', methods=['POST', "GET"])
def entercaptcha():
	global driver
	try:
		captcha_text = request.json['captcha_text']
		text = driver.find_element_by_id('txtEpicCaptcha')
		text.send_keys(captcha_text)
		
		# click on submit button
		epic_submit = driver.find_element_by_id('btnEpicSubmit')
		epic_submit.click()
		time.sleep(3)

		# fetch all epic data
		epic_data = driver.find_elements_by_xpath("//*[@id='resultsTable']/tbody/tr/td/form/input[@type='hidden']")

		a, data = {}, {}

		for i in epic_data:
			k = i.get_attribute('name')
			v = i.get_attribute('value')
			a[k] = v
		# print (a)

		# store all information in data
		data['id'] = a['id']
		data['EPIC_No'] = a['epic_no']
		data['Name'] = a['name']
		data['Gender'] = a['gender']
		data['Age'] = a['age']
		data["Father's/Husband's_Name"] = a['rln_name']
		data['last_update'] = a['last_update']
		data['District'] = a['district']
		data['State'] = a['state']
		data['Assembly_Constituency-Assembly_Constituency_Number'] = a['ac_name'] + a['ac_no']
		data['Parliamentary_Constituency'] = a['pc_name']
		data['Polling_Station'] = a['ps_name']
		data['Serial_No'] = a['slno_inpart']
		data['Part_Number'] = a['part_no']
		data['Part_Name'] = a['part_name']

		# finally convert all information to json
		driver.quit()
		return jsonify({'status': 'success', 'message': 'Successfully Listed','data': data})

	except Exception as e:
		driver.quit()
		return jsonify({'status': 'error', 'message': 'Please Try agian'})

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')
