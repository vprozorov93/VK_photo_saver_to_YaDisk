from VK import VK as vk
from YaDisk import YaUploader
version_vk_api = '5.131'

if __name__ == '__main__':

    while True:
        user_id = input('Input a user ID or domain for get his photos: ')
        count_for_save_photo = input('Input count of photos witch you want to download: ')
        if count_for_save_photo.isdigit():
            break
    vk_token = input('Input VK token: ')
    vk_photo = vk(vk_token, version_vk_api)

    while True:
        menu_text = """
        МЕНЮ:
        [1] Download photos in your PC
        [2] Upload photos to Yandex.Disk
        [3] Exit"""
        print(menu_text)
        user_choise = input('Select a menu item : ')
        if user_choise == "1":
            vk_photo.download_photos_to_pc(user_id, count_for_save_photo)
        elif user_choise == "2":
            yad_token = input('Input Yandex.Disk token: ')
            yandex_loader = YaUploader(yad_token)
            yandex_loader.upload_photos_from_vk(vk_photo.get_photos_link(user_id, count_for_save_photo))
        elif user_choise == "3":
            break
        else:
            print('Select a correct menu item ')




