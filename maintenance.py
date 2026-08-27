import os
import datetime
import logging
import settings
import util
import winmentor
import decorators



@decorators.time_log
def delete_old_trace_files(days_ago):
    start_time = datetime.datetime.now()
    logging.info(f"Start: {start_time}")

    cutoff_date = start_time - datetime.timedelta(days=days_ago)
    logging.info(f"Cutoff date: {cutoff_date}.")

    trace_folders = [util.getCfgVal("gesto", "trace_folder")]

    for folder_path in trace_folders:
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


def read_last_line(filepath, block_size=1024):
    logging.info(f"{filepath=}")

    with open(filepath, 'rb') as file:
        file.seek(0, 2)  # Move to the end of the file
        file_size = file.tell()
        buffer = b''
        position = file_size
        while position >= 0:
            offset = max(0, position - block_size)
            file.seek(offset)
            chunk = file.read(position - offset)
            buffer = chunk + buffer
            lines = buffer.split(b'\n')
            if len(lines) > 1:
                return lines[-2].decode('utf-8')
            position -= block_size
        return buffer.decode('utf-8') if buffer else None


@decorators.time_log
def verify_last_run_finished(log_details=settings.MAINTENANCE_LOG_DETAILS):
    cutoff_date = datetime.datetime.now() - datetime.timedelta(minutes=10)
    logging.info(f"{cutoff_date=}")

    trace_folders = [util.getCfgVal("gesto", "trace_folder")]

    found = False

    for folder_path in trace_folders:
        files = os.listdir(folder_path)
        tot = len(files)
        logging.info(f"{tot} files in folder")

        current_prefix = datetime.datetime.now().strftime('%Y_%m_%d__%H_%M')
        logging.info(f"{current_prefix=}")

        files_sorted = sorted(files, reverse=True)

        for file in files_sorted:
            if log_details in file:
                continue
            else:
                if file.startswith(current_prefix):
                    continue

                with open(f"{folder_path}\\{file}", 'r') as f:
                    content = f.read()
                    if settings.DOC_IMP_SERVER_RUNNING in content:
                        logging.info(f"{settings.DOC_IMP_SERVER_RUNNING}, mesajul e in log")
                        continue

                last_line = read_last_line(f"{folder_path}\\{file}")
                logging.info(last_line)

                if settings.TASK_FINISHED not in last_line:
                    logging.info("Taskul NU s-a terminat cu succes")
                    continue

                break

        logging.info(file)

        file_path = os.path.join(folder_path, file)
        creation_time = os.path.getmtime(file_path)
        creation_datetime = datetime.datetime.fromtimestamp(creation_time)
        if creation_datetime > cutoff_date:
            found = True

            logging.info(f"Log file found, {file_path} created on {creation_datetime}")

    if not found:
        # subiectul spune ca ceva e blocat; corpul spune de cat timp, ca sa se vada
        # din notificare daca e o rulare in curs sau un import intepenit de ore
        now = datetime.datetime.now()
        started_at = winmentor.WinMentor.docImpServerStartedAt()
        body = util.doc_imp_server_status(started_at, now)
        logging.info(body)

        # cat timp DocImpServer sta in bugetul rularii, lipsa unui run incheiat inseamna
        # doar ca unul e in curs; alarma o dam abia cand trece de prag, ca si main.py
        if started_at is not None:
            timeout = util.run_timeout()
            running_for = (now - started_at).total_seconds()

            if running_for <= timeout:
                logging.info("Sub pragul de {} s, e o rulare in curs".format(timeout))

                return

        company = util.get_companies()[0]["companyName"]
        subject = f"WinMentor blocat la - {company}"

        util.send_push_notification(subject, body, True)
