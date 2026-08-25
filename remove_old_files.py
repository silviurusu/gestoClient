""" Sterge fisierele de trace mai vechi de --days_ago zile (implicit 100).

    Punct de intrare pentru task-urile programate; echivalent cu
    main_winmentor.py --delete_older_winmentor=1 --days_ago=<>
"""
import sys
import main_winmentor

if __name__ == "__main__":
    main_winmentor.main(["--delete_older_winmentor=1"] + sys.argv[1:])
