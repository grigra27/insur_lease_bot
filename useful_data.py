import pandas as pd

df = pd.read_csv('tariffs_online.csv', sep=';')


def search_in_our_base(search_phrase):
    """
    Функция производит поиск предмета лизинга в базе данных и возвращает подробную информацию о результатах.
    :param search_phrase: Строка, по которой производится поиск
    :return: Строка с информацией о найденных записях
    """
    used_df = df[df.property.str.contains(search_phrase, case=False)]
    if len(used_df) == 0:
        return f"Предмет лизинга '{search_phrase}' не найден в нашей базе данных."
    records_count = len(used_df)
    property_min = round((used_df.property_value.min()) / 1000000, 3)
    property_median = round((used_df.property_value.median()) / 1000000, 3)
    property_max = round((used_df.property_value.max()) / 1000000, 3)
    tarif_min = round(used_df.tarif.min(), 2)
    tarif_median = round(used_df.tarif.median(), 2)
    tarif_max = round(used_df.tarif.max(), 2)
    insurance_type = used_df.type.mode()[0]
    insurance_company = used_df.insurer.mode()[0]
    result_phrase = f"""
🔍 *Результаты по запросу:* _"{search_phrase}"_

📄 Найдено *{records_count}* запис{"ь" if records_count == 1 else "и"} о таком предмете лизинга.

💰 *Цена объекта лизинга:*
• Медианная цена: *{property_median} млн ₽*
• Диапазон: от *{property_min} млн ₽* до *{property_max} млн ₽*

🛡 *Страховой тариф:*
• Медианный тариф: *{tarif_median}%*
• Диапазон: от *{tarif_min}%* до *{tarif_max}%*

🏷 Чаще всего этот предмет лизинга страхуется как: *"{insurance_type}"* 
🏢 Чаще всего этот предмет лизинга страхуется в страховой компании: *"{insurance_company}"*
"""

    result_phrase2 = f'''
Вы искали предмет лизинга "{search_phrase}". В нашей базе найдено {records_count} запис{"ь" if records_count == 1 else "и"} о таком предмете лизинга.

Медианная цена объекта лизинга - {property_median} млн р. Разброс цен на это имущество от {property_min} млн р. до {property_max} млн р.
Медианный страховой тариф - {tarif_median}%. Разброс страховых тарифов от {tarif_min}% до {tarif_max}%.

Чаще всего этот предмет лизинга страхуется как "{insurance_type}".
Чаще всего этот предмет лизинга страхуется в страховой компании "{insurance_company}".
'''
    return result_phrase


def get_welcome_phrase():
    return f'Вы можете поискать данные о страховании лизинга. Сейчас в базе {len(df)} записей об объектах. Введите запрос.'