import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import toml

# 读取配置文件
with open('config.toml', 'r') as config_file:
    config = toml.load(config_file)
    
email_config = config['email']

def send_email(subject, body, to_email, attachment_path=None):
    # 从配置文件中获取邮件配置
    sender_email = email_config['sender_email']
    sender_password = email_config['sender_password']
    smtp_server = email_config['smtp_server']
    smtp_port = email_config['smtp_port']

    # 构建邮件
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # 添加邮件正文
    msg.attach(MIMEText(body, 'plain'))

    # 添加附件（如果有）
    if attachment_path:
        with open(attachment_path, "rb") as attachment:
            attachment_part = MIMEApplication(attachment.read(), Name="attachment_name")
            attachment_part['Content-Disposition'] = f'attachment; filename="{attachment_path}"'
            msg.attach(attachment_part)

    # 连接到邮件服务器并发送邮件
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        # server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        
if __name__ == '__main__':
    send_email(
        subject="TEST",
        body="TEST",
        to_email="841500915@qq.com"
    )