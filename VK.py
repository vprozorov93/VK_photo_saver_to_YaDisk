import requests
import os
import json
import time
from datetime import datetime
from progress.bar import IncrementalBar


class VK:
    base_url = 'https://api.vk.com/method/'

    def __init__(self, token, ver):
        self.params = {
            'access_token': token,
            'v': ver
        }

    def _get_user_photo_albums(self, user_id):
        """
        Метод получает от VK API информацию о всех доступных альбомах указанного пользователя
        :param user_id: ID пользователя VK.COM
        :return: Возвращает полученный ответ от VK API в формате json с информацией о альбомах
        """
        url = f'{self.base_url}photos.getAlbums'
        user_album_photo_params = {
            'owner_id': user_id,
            'need_system': 1
        }
        response = requests.get(url=url, params={**self.params, **user_album_photo_params})
        return response.json()

    def _get_user_photos(self, user_id, album_id, photo_count):
        """
        Метод получает от VK API информацию о фотографиях пользователя в указаном альбоме
        :param user_id: ID пользователя VK.COM
        :param album_id: ID альбома пользователя VK.COM
        :param photo_count: Количество фото которое необходимо получить из альбома
        :return: Возвращает полученный ответ от VK API в формате json с информацией о фотографиях в указаном альбоме
        """
        url = f'{self.base_url}photos.get'
        photo_user_params = {
            'album_id': album_id,
            'owner_id': user_id,
            'extended': 1,
            'photo_sizes': 1,
            'count': photo_count
        }
        response = requests.get(url=url, params={**self.params, **photo_user_params})
        return response.json()

    def get_photos_link(self, user_id_screen_name, photo_count=5):
        """
        Используя методы _get_user_photos и _get_user_photo_albums этот метод формирует список альбомов и принадлежащих
         им фотографий, для дальнейшей обработки

        :param user_id_screen_name: ID или отображаемое имя пользователя VK.COM
        :param photo_count: Количество необходимых фотографий в каждом альбоме пользователя
        :return: Возвращает список словарей, где ключ- название альбома пользователя, а значение- список словарей,
        в которых ключ - название фото, значение - ссылка для скачивания.
        """

        user_id = self._get_user_info(user_id_screen_name)
        albums = self._get_user_photo_albums(user_id)['response']['items']
        photos = []

        for album in albums:
            photos_in_album = []
            title = album.get('title')
            photos_of_album = self._get_user_photos(user_id, album.get('id'), photo_count)['response']['items']

            for photo in photos_of_album:
                like_count = photo['likes']['count']
                date_of_create = datetime.utcfromtimestamp(photo['date']).strftime('%d-%m-%Y')
                name_of_file = f'{date_of_create}_{like_count}.jpg'
                url = photo['sizes'][-1]['url']
                size_of_photo = photo['sizes'][-1]['type']
                photos_in_album.append({'name_of_file': name_of_file, 'size_of_photo': size_of_photo,
                                        'url': url})

            photos.append({title: photos_in_album})

        return photos

    def download_photos_to_pc(self, user_id_or_screen_name, photo_count=5):
        """
        Используя метод get_photos_link получает список альбомов, а затем выгружает все содержащиеся для каждого альбома
        фотграфии в текущий каталог.
        Создает json файл, содержащий в себе список словарей, где ключ - название
        альбома пользователя, а значение - список словарей, где ключи - name_of_file, size_of_photo, url,
        а значения - соответствующие этим ключам типы ифнормации.
        Создает txt файл лога выгрузки изображений.

        :param user_id_or_screen_name: ID или отображаемое имя пользователя VK.COM
        :param photo_count: Количество необходимых фотографий в каждом альбоме пользователя
        """
        user_id = self._get_user_info(user_id_or_screen_name)
        albums = self.get_photos_link(user_id, photo_count)
        json_path = os.path.join(os.getcwd(), 'albums.json')
        log_path = os.path.join(os.getcwd(), 'log.txt')

        with open(json_path, 'wt') as json_file:
            json.dump(albums, json_file, ensure_ascii=False, indent=2)

        for album in albums:
            for name_of_album, photos in album.items():
                progress_bar = IncrementalBar(f'Download album {name_of_album}', max=len(photos),
                                              suffix='%(percent).1f%% - %(elapsed)ds')
                path_dir = os.path.join(os.getcwd(), f'{name_of_album}(id{user_id})')
                os.mkdir(path_dir)
                for photo in photos:
                    info = list(photo.items())
                    path = os.path.join(path_dir, info[0][1])
                    with open(path, 'wb') as file:
                        response = requests.get(url=info[2][1])
                        file.write(response.content)
                        with open(log_path, 'a') as log:
                            log.write(f'[{datetime.now().strftime("%d-%m-%Y %H:%M:%S")}] File "{info[0][1]}"'
                                      f' downloaded at path "{path_dir}"\n')
                    progress_bar.next()
                    time.sleep(1)
                progress_bar.finish()
        print(f'\n\nAll photos are downloaded to you PC!\n\nLog availible at path {log_path}\n'
              f'json availible at path {json_path}')

    def _get_user_info(self, user_id_or_screen_name):
        url = f'{self.base_url}users.get'
        user_params = {
            'user_ids': user_id_or_screen_name
        }
        response = requests.get(url=url, params={**self.params, **user_params})

        return response.json()['response'][0]['id']
