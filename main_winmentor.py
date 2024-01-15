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


@decorators.time_log
def delete_older_winmentor(days_ago):
    start_time = datetime.datetime.now()
    logging.info(f"Start: {start_time}")

    cutoff_date = start_time - datetime.timedelta(days=days_ago)
    logging.info(f"Cutoff date: {cutoff_date}.")

    # paths_in_which_to_delete = ['d:\\Vectron\\gestoClient\\debug']

    paths_in_which_to_delete = None

    if paths_in_which_to_delete is None:
        paths_in_which_to_delete = [util.getCfgVal("gesto", "trace_folder")]

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

    paths_in_which_to_search = ['d:\\Vectron\\gestoClient\\debug']

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
        logger = None
        # Run
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
        django.setup()

        util.setup_logging(log_details="verify_WM")
        logger = logging.getLogger(name = __name__)

        logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        days_ago = 100
        do_verify_winmentor = 0
        do_delete_older_winmentor = 0

        try:
            # logger.info(sys.argv)
            opts, args = getopt.getopt(sys.argv[1:],"h",["verify_winmentor=",
                                     "delete_older_winmentor=",
                                     "days_ago=",])

            logger.info(opts)
            logger.info(args)

        except getopt.GetoptError:
            print('{} --verify_winmentor=<> --delete_older_winmentor=<> --days_ago=<>'.format(sys.argv[0]))
            sys.exit(2)

        for opt, arg in opts:
            if opt == '-h':
                print('{} --verify_winmentor=<> --delete_older_winmentor=<> --days_ago=<>'.format(sys.argv[0]))
                sys.exit()
            elif opt in ("--verify_winmentor"):
                do_verify_winmentor = bool(int(arg))
            elif opt in ("--delete_older_winmentor"):
                do_delete_older_winmentor = bool(int(arg))
            elif opt in ("--days_ago"):
                days_ago = int(arg)

        logger.info(opts)
        logger.info(args)

        if do_delete_older_winmentor:
            delete_older_winmentor(days_ago)
        elif do_verify_winmentor:
            verify_winmentor()

    except Exception as e:
        print(repr(e))
        if logger is not None:
            logger.exception(repr(e))
        util.newException(e)

    finally:
        if logger is not None:
            logger.info("END")
            logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
