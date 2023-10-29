import sys, getopt
import django
import os
import datetime
import logging
import logging.config
import settings
import json
from datetime import datetime as dt
import util
import inspect
import decorators

# logging.basicConfig(filename='delete_older_winmentor.log', level=logging.INFO)

LOG_DETAILS="verify_WM"

def setup_logging(
        default_path='logging.json',
        default_level=logging.INFO,
        env_key='LOG_CFG'
        ):
    """ Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)

            # Search for hadlers with "folder" and set the
            # .. log file with current date in that folder
            for _, dhandler in config["handlers"].items():
                folder = dhandler.pop("folder", None)
                if folder:
                    path = os.path.join(
                            folder,
                            dt.strftime(dt.now(), f"%Y_%m_%d__%H_%M__{LOG_DETAILS}.log")
                            )

                    if os.path.exists(path):
                        path = os.path.join(
                            folder,
                            dt.strftime(dt.now(), f"%Y_%m_%d__%H_%M__%f__{LOG_DETAILS}.log")
                            )

                    if not os.path.exists(folder):
                        os.mkdir(folder)
                    dhandler["filename"] = path

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


@decorators.time_log
def delete_older_winmentor(days_ago):
    start_time = datetime.datetime.now()
    logging.info(f"Start: {start_time}")

    cutoff_date = start_time - datetime.timedelta(days=days_ago)
    logging.info(f"Cutoff date: {cutoff_date}.")

    paths_in_which_to_delete = ['c:\WME\Vectron\gestoClientWME\debug']

    for folder_path in paths_in_which_to_delete:
        files = os.listdir(folder_path)
        tot = len(files)
        logging.info(f"{tot} files in folder")

        for ctr, file_name in enumerate(files, start=1):
            file_path = os.path.join(folder_path, file_name)
            creation_time = os.path.getmtime(file_path)
            creation_datetime = datetime.datetime.fromtimestamp(creation_time)
            if creation_datetime < cutoff_date:
                os.remove(file_path)
                logging.info(f"{ctr}, delete file {file_path} created on {creation_datetime}")

                # if ctr == 100:
                #     break

    end_time = datetime.datetime.now()
    logging.info(f"End: {end_time}")
    logging.info(f"Duration: {end_time-start_time}")


@decorators.time_log
def verify_winmentor():
    cutoff_date = dt.now() - datetime.timedelta(minutes=10)
    logging.info(f"Cutoff date: {cutoff_date}.")

    paths_in_which_to_search = ['d:\Vectron\gestoClient\debug']

    found = False

    for folder_path in paths_in_which_to_search:
        files = os.listdir(folder_path)
        tot = len(files)
        logging.info(f"{tot} files in folder")

        files_sorted = sorted(files, reverse=True)

        logging.info(f"{tot} files in folder")

        for file in files_sorted:
            if LOG_DETAILS in file:
                continue
            else:
                break

        logging.info(file)

        file_path = os.path.join(folder_path, file)
        creation_time = os.path.getmtime(file_path)
        creation_datetime = datetime.datetime.fromtimestamp(creation_time)
        if creation_datetime > cutoff_date:
            found = True

            logging.info(f"Log file found, {file_path} created on {creation_datetime}")

    if not found:
        company = util.getCfgVal("winmentor", "companyName")
        txtMail = f"WinMentor blocat la - {company}"

        util.send_email(subject = txtMail, msg = txtMail)


if __name__ == "__main__":
    try:
        # Run
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
        django.setup()

        setup_logging()
        logger = logging.getLogger(name = __name__)

        logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        days_ago = 100

        try:
            # logger.info(sys.argv)
            opts, args = getopt.getopt(sys.argv[1:],"h",["days_ago=",
                                    ])

            logger.info(opts)
            logger.info(args)

        except getopt.GetoptError:
            print('{} --days_ago=<>'.format(sys.argv[0]))
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print('{} --days_ago=<>'.format(sys.argv[0]))
                sys.exit()
            elif opt in ("--days_ago"):
                days_ago = int(arg)

        # delete_older_winmentor(days_ago)
        verify_winmentor()

    except Exception as e:
        print(repr(e))
        logger.exception(repr(e))
        util.newException(e)

    finally:
        logger.info("END")
        logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))



