from ConfigParser import SafeConfigParser, NoOptionError, NoSectionError

class MyConfigParser(SafeConfigParser):
    cfgFileName = ""

    def __init__(self, *args, **kwargs):
        fileName = kwargs.get("fileName")

        print fileName
        super(MyConfigParser, self).__init__(*args, **kwargs)

    def get(self, section, key):
        ret = super(MyConfigParser, self).get(*args, **kwargs)

        ret += " " + fileName



