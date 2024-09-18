'''
Server_mailmoinitor.py
-Hackbit
-2024/9/18
'''
import smtplib  
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart  
import psutil  
import time  
import os  
  
# 邮件配置  
'''
SMTP_SERVER:      发件邮箱服务器
SMTP_PORT:        使用587端口(非ssl端口)
SMTP_USER:        发件邮箱
SMTP_PASSWORD:    发件邮箱的密钥
RECIPIENT:        接收邮件邮箱
SENDER:           邮件标题
'''
SMTP_SERVER = 'smtp.xxx.com'
SMTP_PORT = 587
SMTP_USER = 'xxx@xxx.com'
SMTP_PASSWORD = 'xxxxx'
RECIPIENT = 'xxx@xxx.com'
SENDER = 'System Monitor <xxx@xxx.com>' 
  
# 阈值设置(超过正常值会发送预警邮件)
THRESHOLD_CPU = 90
THRESHOLD_MEM = 80
THRESHOLD_DISK = 90
  
def send_email(subject, body):  
    msg = MIMEMultipart()  
    msg['From'] = SENDER  
    msg['To'] = RECIPIENT  
    msg['Subject'] = subject  
    msg.attach(MIMEText(body, 'plain'))  
  
    try:  
        '''
        使用STARTTLS，而不是SSL
        '''
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)  
        server.starttls()  
        server.login(SMTP_USER, SMTP_PASSWORD)  
        server.sendmail(SENDER, RECIPIENT, msg.as_string())  
        server.quit()  
        print("Email sent successfully!")  
    except Exception as e:  
        print(f"Failed to send email: {e}")  
  
def get_system_info():  
    '''获取系统负载/占用信息
    :cpu_percent:         CPU占用率
    :memory:              虚拟内存
    :memory_total:        总内存
    :memory_used:         已用内存
    :memory_percent:      内存使用率
    :disk_usage:total:    磁盘容量
    :disk_usage:used:     已用磁盘容量
    :disk_usage:percent:  磁盘占用率
    ''' 
    #CPU占用
    cpu_percent = psutil.cpu_percent(interval=1)  

    # 内存信息
    memory = psutil.virtual_memory()  
    memory_total = round(memory.total / (1024.0 ** 3), 2)  # 转换为GB  
    memory_used = round(memory.used / (1024.0 ** 3), 2)  
    memory_percent = memory.percent  
  
    # 磁盘信息  
    disk_usage = {}  
    for p in psutil.disk_partitions():  
        usage = psutil.disk_usage(p.mountpoint)  
        disk_usage[p.mountpoint] = {  
            'total': round(usage.total / (1024.0 ** 3), 2),  
            'used': round(usage.used / (1024.0 ** 3), 2),  
            'percent': usage.percent  
        }  
  
    # 检查特定挂载点(默认注释掉，需要可以取消注释)  
    #share_online = os.path.ismount('/mnt/你的挂载点')  
  
    # 网卡传输信息(获取接收和发送的字节数)
    '''
    :bytes_sent：    自系统启动以来通过所有网络接口发送的总字节数
    :bytes_recv：    自系统启动以来通过所有网络接口接收的总字节数
    :packets_sent：  发送的总数据包数(可选，取决于操作系统和psutil版本)
    :packets_recv：  接收的总数据包数(可选，取决于操作系统和psutil版本)
    :errin：         接收时发生的错误总数(可选)
    :errout：        发送时发生的错误总数(可选)
    :dropin：        接收时丢弃的数据包总数(可选)
    :dropout：       发送时丢弃的数据包总数(可选)
    '''
    net_io = psutil.net_io_counters()  
    bytes_sent = net_io.bytes_sent  
    bytes_recv = net_io.bytes_recv  
  
    # 邮件内容  
    body = f"""  
    CSEC-UbuntuServer
    System Monitor Report  
    ================================  
    {'-' * 20} 
    CPU Usage: {cpu_percent}%  
  
    {'-' * 20} 
    Memory:  
    - Total: {memory_total} GB  
    - Used: {memory_used} GB  
    - Usage: {memory_percent}%  
  
    {'-' * 20} 
    Disk Usage:  
     
    """  
    
    #写入信息
    for mount, info in disk_usage.items():  
        body += f"{mount}:\n"  
        body += f"  - Total: {info['total']} GB\n"  
        body += f"  - Used: {info['used']} GB\n"  
        body += f"  - Usage: {info['percent']}%\n"  

    '''如果有挂载点，在下面加入这几行：
    {'-' * 20}   
     Mount Point:  
    - Online: {'Yes' if share_online else 'No'}  
    '''
    body += f"""                               
    {'-' * 20} 
    Network I/O:  
    - Bytes Sent: {bytes_sent} bytes  
    - Bytes Received: {bytes_recv} bytes  
  
                       End   
    ================================ 
    """  
  
    return body, cpu_percent > THRESHOLD_CPU, memory_percent > THRESHOLD_MEM, any(info['percent'] > THRESHOLD_DISK for info in disk_usage.values())  
  
def main():  
    last_check = time.time()  #初始化时间戳
    while True:  
        body, cpu_high, mem_high, disk_high = get_system_info()  #获取系统信息
        subject = "System Monitor Report"  #常规
        if cpu_high or mem_high or disk_high:  
            subject = "System Alert: High Usage Detected"  #异常(高占用率)
            send_email(subject, body)  
        elif time.time() - last_check > 3600:  # 正常报告发送时间间隔(默认每小时一次)  
            send_email(subject, body)  
            last_check = time.time()  
  
        time.sleep(60)  # 默认每分钟检查一次  
  
if __name__ == "__main__":  
    main()
