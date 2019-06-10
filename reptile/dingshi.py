import os
import time
import datetime
import schedule

time_offset=0

def update():
    time_offset=0

def dooffset():
    time_offset=1

def WebCrawlerJD():
    os.system('conda activate stan_env')
    os.system('cd /root/py-web/reptile')
    os.system('nohup python -u JD.py > JD.log 2>&1 &')

def WebCrawlerSN():
    os.system('conda activate stan_env')
    os.system('cd /root/py-web/reptile')
    os.system('nohup python -u SN.py > SN.log 2>&1 &')

def dopreproc():
    os.system('conda activate stan_env')
    os.system('cd /root/py-web/reptile')
    os.system('nohup python -u preproc.py > preproc.log 2>&1 &')

def doeval():
    os.system('conda activate stan_env')
    os.system('cd /root/py-web/reptile')
    os.system('nohup python -u eval.py > eval.log 2>&1 &')

def movelog():
    os.system('cd /root/py-web/reptile')
    current_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    filename1 = current_date + '-JD.log'
    filename2 = current_date + '-JDlog.log'
    os.system('cp JD.log ' + filename1)
    os.system('mv ' + filename1 + ' /root/py-web/output')
    os.system('cp JDlog.log ' + filename2)
    os.system('mv ' + filename2 + ' /root/py-web/log')
    filename3 = current_date + '-SN.log'
    filename4 = current_date + '-SNlog.log'
    os.system('cp SN.log ' + filename3)
    os.system('mv ' + filename3 + ' /root/py-web/output')
    os.system('cp SNlog.log ' + filename4)
    os.system('mv ' + filename4 + ' /root/py-web/log')
    filename5 = current_date + '-preproc.log'
    os.system('cp preproc.log ' + filename5)
    os.system('mv ' + filename5 + ' /root/py-web/output')

def main():
    schedule.every().day.at('01:00').do(dooffset)
    schedule.every().day.at('01:00').do(WebCrawlerJD)
    schedule.every().day.at('01:05').do(WebCrawlerSN)
    schedule.every().day.at('03:30').do(dopreproc)
    schedule.every().day.at('05:00').do(movelog)
    schedule.every().day.at('05:00').do(update)


    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    schedule.every().day.at('01:30').do(dooffset)
    schedule.every().day.at('01:30').do(WebCrawlerJD)
    schedule.every().day.at('01:35').do(WebCrawlerSN)
    schedule.every().day.at('03:30').do(dopreproc)
    schedule.every().day.at('04:30').do(doeval)
    schedule.every().day.at('07:00').do(movelog)
    schedule.every().day.at('07:00').do(update)
    while True:
        schedule.run_pending()
        time.sleep(1)
