import smtplib


gmail_user = 'susanto.shipping.corp@gmail.com'  
gmail_password = 'SWEN90016'
server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
server.ehlo()
server.login(gmail_user, gmail_password)

def send_email(target_email, message):

    sent_from = gmail_user  
    to = [target_email, 'susanto.shipper@google.com']  
    subject = 'About Shipping Order'  
    body = message

    email_text = """\  
    From: %s  
    To: %s  
    Subject: %s
    
    %s
    """ % (sent_from, ", ".join(to), subject, body)
    try:
        print('##debug print: start sending email')
        server.sendmail(sent_from, to, email_text)
        print('##debug print: email sent')
    except:
        print('email error !!!!')

if __name__ == '__main__':
    send_email('bluan@student.unimelb.edu.au', 'hello! test test test ...')
