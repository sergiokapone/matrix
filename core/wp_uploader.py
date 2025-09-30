# core/wp_uploader.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()
WP_AUTH = (os.getenv("WP_USER"), os.getenv("WP_PASSWORD"))
WP_URL = "https://apd.ipt.kpi.ua/wp-json/wp/v2/pages"


def update_wordpress_page(content, page_id=None, slug=None, data=None):
    """
    Оновлює або створює сторінку WordPress.
    
    Args:
        content: HTML контент сторінки
        page_id: ID сторінки для оновлення (якщо відомий)
        slug: Slug для пошуку/створення сторінки
        data: Додаткові дані (title, parent, status тощо)
    
    Returns:
        tuple: (success: bool, link: str|None, message: str)
    """
    post_data = {
        'content': content,
        'status': 'publish'
    }
    
    # Додаємо додаткові дані якщо є
    if data:
        post_data.update(data)
    
    try:
        # Якщо передано page_id - одразу оновлюємо
        if page_id:
            print(f"♻️ Оновлюємо існуючу сторінку з id={page_id}")
            update_url = f"{WP_URL}/{page_id}"
            update_response = requests.post(update_url, json=post_data, auth=WP_AUTH, timeout=30)
            
            if update_response.status_code == 200:
                created_link = update_response.json().get('link')
                return True, created_link, f"✅ Оновлено сторінку (id={page_id})"
            else:
                return False, None, f"❌ Помилка оновлення: {update_response.status_code} → {update_response.text}"
        
        # Якщо передано slug - шукаємо сторінку
        elif slug:
            check_response = requests.get(WP_URL, params={"slug": slug}, auth=WP_AUTH, timeout=30)
            
            if check_response.status_code != 200:
                return False, None, f"❌ Помилка перевірки: {check_response.status_code}"
            
            existing_pages = check_response.json()
            
            if existing_pages:
                # Сторінка існує - оновлюємо
                found_page_id = existing_pages[0]['id']
                print(f"♻️ Оновлюємо існуючу сторінку: {slug} (id={found_page_id})")
                
                update_url = f"{WP_URL}/{found_page_id}"
                update_response = requests.post(update_url, json=post_data, auth=WP_AUTH, timeout=30)
                
                if update_response.status_code == 200:
                    created_link = update_response.json().get('link')
                    return True, created_link, f"♻️ Оновлено існуючу сторінку (id={found_page_id})"
                else:
                    return False, None, f"❌ Помилка оновлення: {update_response.status_code} → {update_response.text}"
            else:
                # Сторінки не існує - створюємо нову
                create_response = requests.post(WP_URL, json=post_data, auth=WP_AUTH, timeout=30)
                
                if create_response.status_code == 201:
                    created_link = create_response.json().get('link')
                    return True, created_link, "✅ Створено нову сторінку"
                else:
                    return False, None, f"❌ Помилка створення: {create_response.status_code} → {create_response.text}"
        
        else:
            return False, None, "❌ Потрібно передати page_id або slug"
            
    except requests.exceptions.RequestException as e:
        return False, None, f"❌ Помилка з'єднання: {str(e)}"
    except Exception as e:
        return False, None, f"❌ Несподівана помилка: {str(e)}"