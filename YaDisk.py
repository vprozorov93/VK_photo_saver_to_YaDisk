import requests
import os
import json
from datetime import datetime
from progress.bar import IncrementalBar


class YaUploader:
    url = 'https://cloud-api.yandex.net/'

    def __init__(self, token: str):
        """
        Инициализируем объект класса с токеном для API
        :param token:
        """
        self.token = token

    def get_headers(self):
        """
        Метод для получения статичных headers под запросы
        :return: Возвращает headers для выполнения запросов
        """
        return {'Accept': 'application/json', 'Authorization': f'OAuth {self.token}'}

    def get_files_list(self):
        """
        Получаем список файлов на ЯндексДиске
        :return: Возвращает список файлов в json формате
        """
        files_url = f'{self.url}v1/disk/resources/files/'
        headers = self.get_headers()
        response = requests.get(files_url, headers)
        return response.json()

    def _get_upload_link(self, disk_file_path):
        """
        Вспомогательный метод получения ссылки для загрузки на Яндекс.Диск. Требуется для совершения выгрузки файлов на
        диск
        :param disk_file_path:
        :return:
        """
        upload_url = f'{self.url}v1/disk/resources/upload/'
        headers = self.get_headers()
        params = {'path': disk_file_path, 'overwrite': "true"}
        response = requests.get(url=upload_url, headers=headers, params=params)
        return response.json()

    def upload_file_to_disk(self, disk_file_path: str, filename: str):
        """
        Метод выполняет выгрузку файлов из указанного пути на рабочей станции в указанный путь на
        Яндекс.Диске
        :param disk_file_path: path для размещения файла на Яндекс.Диске
        :param filename: path до файла на рабочей станции
        :return:
        """

        href = self._get_upload_link(disk_file_path=disk_file_path).get("href", "")
        response = requests.put(url=href, data=open(filename, "rb"))
        response.raise_for_status()
        if response.status_code == 201:
            return 'Success'
        else:
            return 'Fail'

    def upload_photos_from_vk(self, albums: list):
        """
        Метод, получая на вход список словарей,
        создает на Яндекс.Диске корневую папку по шаблонку vk_photos_<date_time>, затем проходя по элементам каждого
        словаря в полученом списке создает в корневой папке еще одну, с названием альбома фотографий пользователя VK и
        уже в нее выгружает все фотографии принадлежащие этому альбому.

        Также в корневой папке создает json file из словаря, который получен на входе и log файл, в котором хранится
        история выгрузки фотграфий на Яндекс.Диск.

        :param albums: Список словарей вида [{album:
                                [{'name_of_file': name_of_file, 'size_of_photo': size_of_photo, 'url': url}]},{...}]
        """
        create_folder_url = f'{self.url}v1/disk/resources/'
        headers = self.get_headers()
        data = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        params = {'path': f'/vk_photos_{data}'}
        requests.put(url=create_folder_url, headers=headers, params=params)

        json_path_temp = os.path.join(os.getcwd(), 'temp_albums.json')
        with open(json_path_temp, 'wt') as json_file:
            json.dump(albums, json_file, ensure_ascii=False, indent=2)
        self.upload_file_to_disk(f'{params["path"]}/albums.json', json_path_temp)

        temp_log_path = os.path.join(os.getcwd(), 'temp_log.txt')

        for album in albums:
            for name_of_album, photos in album.items():
                progress_bar = IncrementalBar(f'Upload album {name_of_album}', max=len(photos),
                                              suffix='%(percent).1f%% - %(elapsed)ds')
                path_for_album_folder = {'path': f'/vk_photos_{data}/{name_of_album}'}
                requests.put(url=create_folder_url, headers=headers, params=path_for_album_folder)
                for photo in photos:
                    progress_bar.next()
                    path_temp = os.path.join(os.getcwd(), 'temp.jpg')
                    with open(path_temp, 'wb') as file:
                        response = requests.get(url=photo["url"])
                        file.write(response.content)
                    status = self.upload_file_to_disk(f'{path_for_album_folder["path"]}/{photo["name_of_file"]}',
                                                      path_temp)
                    with open(temp_log_path, 'a') as log:
                        log.write(f'[{datetime.now().strftime("%d-%m-%Y %H:%M:%S")}] File "{photo["name_of_file"]}"'
                                  f' downloaded at path "YaDisk{path_for_album_folder["path"]} Status: {status}"\n')
                    os.remove(path_temp)
                progress_bar.finish()
        self.upload_file_to_disk(f'{params["path"]}/log.txt', temp_log_path)
        os.remove(temp_log_path)
        os.remove(json_path_temp)
        print(f'\n\nAll photos are downloaded to you YaDisk!\n\n'
              f'Log and json availible at path "YaDisk/{params["path"]}"')

