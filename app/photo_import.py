#!/usr/bin/env python3
"""
Photo Import for Marta
"""

__author__ = "Sergio Comuñas"
__version__ = "0.2.0"
__license__ = "MIT"

### Library import ###
import ffmpeg
from modules.utils import log, local_filepaths, smb_filepaths, file_time, progress_bar
from smb.SMBConnection import SMBConnection
import pandas as pd
import os
import json
from datetime import datetime
import shutil

def main():
    ## Define log filename
    log_filename = "log/photo_import_log_" + \
                    datetime.now().strftime('%Y%m%d_%H%M%S') + \
                    '.log'
    if os.path.isdir('./log') == False:
                    os.mkdir('./log')
    log('Start Execution with version ' + __version__, log_filename)

    ## Import configuration from file
    log('Get configuration from config.json', log_filename)
    f = open("config.json")
    config = json.load(f)
    f.close()

    ## Get main variables
    dst_folder = config['destination_folder']
    exception_ext = config['exception_ext']
    exception_folders = config['exception_folders']
    source_num = len(config['sources'])

    ## Menu for user to choose an option
    log('Waiting user to choose an option:', log_filename)
    for i in range(source_num):
        source = config['sources'][i]
        print(i, '-', source['name'], '(', source['type'], ')')
    option = int(input())

    src_folder = config['sources'][option]['path']
    src_name = config['sources'][option]['name']
    src_type = config['sources'][option]['type']
    log('Option chosen by the user: ' + str(option) + ' - ' + src_name + ' (' + src_type + ')', log_filename)

    ## Menu for choose the dates
    log('Waiting user to choose start date (YYYY-MM-DD):', log_filename)
    date_chosen = input()
    start_date = datetime.strptime(date_chosen, '%Y-%m-%d')
    log('Start date chosen by the user: ' + date_chosen, log_filename)
    log('Waiting user to choose end date (YYYY-MM-DD):', log_filename)
    date_chosen = input()
    end_date = datetime.strptime(date_chosen + ' 23:59:59','%Y-%m-%d %H:%M:%S')
    log('End date chosen by the user: ' + date_chosen, log_filename)

    # Get file list
    log('Get file list', log_filename)
    print('--------------------')
    files, roots, folders, extensions, file_count = local_filepaths(src_folder, exception_folders, exception_ext)
    empty_column = [''] * len(roots) 
    file_df = pd.DataFrame({
        "folder": roots,
        "file": files,
        "extension": extensions,
        'source': empty_column,
        'destination': empty_column,
        'date_type': empty_column,
        'date_time': empty_column
        })
    print('--------------------')
    log(str(file_df.shape[0]) + ' files found', log_filename)

    # Complete file list with dates based on exif or file creation date
    log('Fill dates on file list', log_filename)
    for index, row in file_df.iterrows():
        row['source'] = row['folder'] + '/' + row["file"]
        row['date_time'], row['date_type'] = file_time(row['source'])
        row['destination'] = dst_folder + '/' + \
                            row['date_time'].strftime("%Y%m%d/%Y%m%d_%H%M%S_") + \
                            str(index) + row['extension']
        progress_bar(index, file_df.shape[0])
    print()
    value_not_found = file_df[file_df['date_type'] == 'not_found'].shape[0]
    log(str(value_not_found) + ' files will be not copied because have no date', log_filename)

    # Fitering dates using parameters entered
    log('Filtering images on dates selected', log_filename)
    file_df_filtered = file_df[(file_df['date_time'] >= start_date) & (file_df['date_time'] <= end_date)]
    file_df_filtered.reset_index(drop=True, inplace=True)
    log(str(file_df_filtered.shape[0]) + ' files remaining', log_filename)
    
    # Copy files
    log('Start copying files', log_filename)
    for index, row in file_df_filtered.iterrows():
        # Create folder if doesn't exist
        dst_path = dst_folder + '/' + \
                    row['date_time'].strftime("%Y%m%d")
        if os.path.isdir(dst_path) == False:
                    os.mkdir(dst_path)
        # Copy files
        shutil.copy2(row['source'], row['destination'])
        progress_bar(index, file_df_filtered.shape[0])
    print()
    log('End copying files', log_filename)
    print('Press ENTER to finish')
    input()

if __name__ == "__main__":
    main()
