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