import datetime
import collections
from django.core.mail import EmailMessage

def isArray(var):
    return isinstance(var, collections.Iterable) and (not isinstance(var, basestring))

def retToFileArray(ret, filename):
    ret = ret[0]
    retCnt = len(ret)

    thefile = open(filename+".txt", 'w')
    for ctr, r in enumerate(ret, start=1):
        thefile.write("{}/{} - {}\n".format(ctr, retCnt, r))


def send_email(subject, msg, toEmails=None, bccEmails=None, location=True, isGestoProblem=False):
    email = EmailMessage(subject, msg, to=toEmails, bcc=bccEmails)
    email.send()


def printArray(array):
    print ""
    for item in array:
        print item

    print ""


def defaultJSON(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')


def getTimestamp(date):
    if isinstance(date, str):
        date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    elif not isinstance(date, datetime.datetime):
        date = datetime.datetime.combine(date, datetime.datetime.min.time())

    ret = int((date - datetime.datetime(1970, 1, 1)).total_seconds())
    return ret
