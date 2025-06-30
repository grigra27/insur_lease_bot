import pandas as pd
import asyncio

df = pd.read_csv('tariffs_online.csv', sep=';')

async def search_in_our_base(search_phrase):
    """
    Асинхронная функция поиска предмета лизинга в базе данных и возврата подробной информации о результатах.
    :param search_phrase: Строка, по которой производится поиск
    :return: Строка с информацией о найденных записях
    """
    # имитируем асинхронность для совместимости с async handler
    await asyncio.sleep(0)
    used_df = df[df.property.str.contains(search_phrase, case=False)]
    if len(used_df) == 0:
        return f"""
❗️*Ничего не найдено по запросу* **«{search_phrase}»**.

🔍 Пожалуйста, проверьте правильность написания или попробуйте другой вариант названия.

💡 *Примеры запросов:*
- `Haval Jolion`
- `sitrak`
- `BMW X5`
"""
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

💰 *Цена предмета лизинга:*
• Медианная цена: *{property_median} млн ₽*
• Диапазон: от *{property_min} млн ₽* до *{property_max} млн ₽*

🛡 *Страховой тариф:*
• Медианный тариф: *{tarif_median}%*
• Диапазон: от *{tarif_min}%* до *{tarif_max}%*

🏷 Чаще всего страхуется как: *"{insurance_type}"* 
🏙 Чаще всего страхуется в страховой компании: *"{insurance_company}"*
"""
    return result_phrase


def get_welcome_phrase():
    return (
        f"👋 Добро пожаловать!\n\n"
        f"📊 Вы можете найти информацию о страховании лизингового имущества."
        f"В нашей базе сейчас {len(df)} записей.\n\n"
        f"🔎 Просто введите название интересующего вас предмета лизинга, "
        f"например 'Haval Dargo' или 'sitrak'."
    )
