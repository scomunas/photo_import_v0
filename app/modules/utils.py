from datetime import datetime
import os
import exifread
import sys

### Log ###
def log(text, file):
    current_date = datetime.now()
    message = current_date.strftime('%Y-%m-%d %H:%M:%S') + ' | ' + text
    print(message)
    with open(file, 'a') as fh:
        fh.write(message + "\n")

### Progress Bar ###
def progress_bar(count_value, total):
    bar_length = 50
    filled_up_Length = int(round(bar_length* count_value / float(total)))
    percentage = round(100.0 * count_value/float(total),1)
    bar = '=' * filled_up_Length + '-' * (bar_length - filled_up_Length)
    sys.stdout.write('[%s] %s %s%s\r' %(bar, count_value, percentage, '%'))
    sys.stdout.flush()

### Función para obtener la lista de ficheros en una carpeta local ###
def local_filepaths(folder, exception_folders, exception_ext):
    file_list = []
    root_list = []
    folder_list = []
    extension_list = []
    file_count = 0

    for filename in os.listdir(folder):
        path = folder + "/" + filename

        if os.path.isfile(path):
            extension = str(os.path.splitext(filename)[1]).lower()
            if extension not in exception_ext:
                file_list.append(filename)
                root_list.append(folder)
                folder_list.append(os.path.basename(folder))
                extension_list.append(extension)
                file_count += 1
                # print("Fichero " + filename + " añadido a la lista")
            else:
                # print("Fichero " + filename + " *****DESCARTADO*****")
                file_count = file_count
        elif os.path.isdir(path):
            if filename not in exception_folders:
                file_append, root_append, folder_append, extension_append, count_append = local_filepaths(path, exception_folders, exception_ext)
                file_list = file_list + file_append
                root_list = root_list + root_append
                folder_list = folder_list + folder_append
                extension_list = extension_list + extension_append
                file_count = file_count + count_append

    print(file_count, 'files found in folder:', folder)

    return file_list, root_list, folder_list, extension_list, file_count

### Función para obtener la lista de ficheros en un NAS con smb ###
def smb_filepaths(folder, resource, nas_conn, exception_folders, exception_ext):
    file_list = []
    root_list = []
    folder_list = []
    extension_list = []
    file_count = 0

    # print("Analizando carpeta: " + folder)
    filenames = nas_conn.listPath(resource, folder)

    for filename in filenames:
        path = folder + "/" + filename.filename
        # print("Analizando fichero: " + path)

        if filename.isDirectory:
            if filename.filename not in exception_folders:
                file_append, root_append, folder_append, extension_append, count_append = smb_filepaths(path, resource, nas_conn, exception_folders, exception_ext)
                file_list = file_list + file_append
                root_list = root_list + root_append
                folder_list = folder_list + folder_append
                extension_list = extension_list + extension_append
                file_count = file_count + count_append
        else:
            extension = str(os.path.splitext(filename.filename)[1]).lower()
            if extension not in exception_ext:
                file_list.append(filename.filename)
                root_list.append(folder)
                folder_list.append(os.path.basename(folder))
                extension_list.append(extension)
                file_count += 1
                # print("Fichero " + filename.filename + " añadido a la lista")
            else:
                # print("Fichero " + filename.filename + " *****DESCARTADO*****")
                file_count = file_count

    return file_list, root_list, folder_list, extension_list, file_count

### Obtain file time from metadata or exif ###
def file_time(path):
    extension = path.split('.')[len(path.split('.')) - 1]
    extension = extension.lower()
    time = ''
    date_type = ''
    try:
        if extension == "jpg" or extension == "jpeg" or extension == "png" or extension == "tiff":
            with open(path, 'rb') as fh:
                tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal", details=False)
            if 'EXIF DateTimeOriginal' in tags.keys():
                tags_temp = str(tags['EXIF DateTimeOriginal']).replace(' 24:', ' 00:') # Bug de Exif que pone las 00h como 24h
                time = datetime.strptime(tags_temp, '%Y:%m:%d %H:%M:%S')
                date_type = 'exif'

        if time == '':
            file_time = os.path.getmtime(path)
            time = datetime.fromtimestamp(file_time)
            date_type = 'creation'
    except:
        time = datetime.strptime('2000-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        date_type = 'not_found'

    return time, date_type