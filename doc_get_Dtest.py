from threading import Thread
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import vk_api as vk_api
import bot_settings
import discord
from discord.ext import commands
import asyncio

# ==========================================================

Vk_message_is = False
Message_for_all = {"photo": None, 'text': [''], "doc": ['']}
user_get = ''


# ===================|Сортировка текста|========================================
def split_text_2(text: str, max_chars: int = 2000) -> list:
    """
    Разделяет текст по символам
    :param text: Текст
    :param max_chars: Максимально допустимая длина части текста
    """
    result = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
    return result


# =============================================================
def Get_photo():
    pass


def Get_doc(attachments):
    #  Передаётся весь словарь attachments
    #  и из него на выходе функция должна
    #  выдать массив с url на каждый прикреплённый док
    doc_list = []
    for i in range(len(attachments)):
        if attachments[i]['type'] == "doc":
            doc_list.append(attachments[i]['doc']['url'])
    print('DOC_LIST = ' + str(doc_list))
    return doc_list
def get_fwd_rec(fwd_messages,rtn = None):

    c = (f"Пересланный: {fwd_messages}")
    print(c)
    if len(fwd_messages['fwd_messages']) !=0: # должен быть цикл for который пробегается по верхнему уровню пересланных сообщений и дальше только проверка вложенных
        rtn = fwd_messages['fwd_messages']
    else:
        rtn = None
    return rtn


def Get_forwrd_message_text(message):
    res = message['fwd_messages']
    if len(res) != 0:
        while True:
            res = get_fwd_rec(res)
            if res == None:
                print('Не найдено пересланных сообщений')
                break
    else:
        res = None
    return res




# ==================|discord\===============================


bot = commands.Bot(command_prefix=bot_settings.D_prefix)


@bot.event  # отлавливаем событие
async def on_ready():  # Как только бот подключён выводим сообщение в консоль
    print('Ready!')


# ===============================|Embed|===========================================
def createEmb(text='', photo=None, count="", doc=''):
    global user_get  # словарь с имененм автора сообщения

    embed_m = discord.Embed(title=f"‼|Важная информация|‼", description=f"⦁ ⦁ ⦁\n{text}\n⦁ ⦁ ⦁", color=0x00aad5)
    embed_m.set_thumbnail(url="https://sun9-73.userapi.com/impg/pIqm8Ca1gO25VwvtG0_TtPoWK_YWbWOadmzngQ/4FaZa1I7XIk.jpg?size=303x306&quality=96&sign=790a802a88c77ff996564f3679169411&type=album")
    if photo != None:  # Если поступило сообщение и нет фото
        embed_m.set_image(url=photo)
    if doc != '':
        for i in range(len(doc)):
            embed_m.add_field(name="🔗 Ссылка на документ: " + str(doc[i]), value="📜", inline=False)
    embed_m.set_footer(
        text=f"{user_get[0]['first_name']} {user_get[0]['last_name']}")  # подпись под каждым сообщением, кто был автором (можно сделать будет проверку на автортсво)
    return embed_m


# ==================================================================================
async def sender():
    global Vk_message_is
    global Message_for_all

    await bot.wait_until_ready()

    channel = bot.get_channel(bot_settings.D_idChannel)


    while True:

        if Vk_message_is == True:
            try:
                for i in range(len(Message_for_all['text'])):
                    await channel.send(embed=createEmb(text=Message_for_all["text"][i], photo=Message_for_all["photo"],
                                                       count=str(i + 1), doc=Message_for_all["doc"]))
                    if i > 1:
                        Message_for_all[
                            "photo"] = None  # Должно отправить только одну фотку при большом количестве эмбедов с текстом
                    Vk_message_is = False
            except IndexError:  # Если нет фото то тут выбрасывает ошибку
                for i in range(len(Message_for_all['text'])):
                    print('Траблы с фото')
                    await channel.send(embed=createEmb(text=Message_for_all['text'][i], count=str(i + 1)),
                                       doc=Message_for_all["doc"])
                    Vk_message_is = False
            else:  # вроде не нужно но пусть будет
                Vk_message_is = False

    await asyncio.sleep(10)


# ===============|vk|===================================

token = bot_settings.Vk_token

vk_session = vk_api.VkApi(token=token)

session_api = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, bot_settings.Vk_idChat)
print('Vk is active')


# ===============|code|=========================
def bb1():
    bot.loop.create_task(sender())

    bot.run(bot_settings.D_token)


def bb2():
    global Vk_message_is
    global Message_for_all
    global user_get
    print('Ожидаем...')

    while True:
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:

                if event.from_chat:
                    if "@all" in event.message.text.lower():

                        Message_for_all['text'] = split_text_2(event.message.text, max_chars=4096)  # Берём текст
                        print(event.message)
                        # print("\nТекст сообщения: "+ str(event.message.text)+"\nВремя отправки: "+str(datetime.utcfromtimestamp(event.message.date).strftime('%Y-%m-%d %H:%M:%S')+"(+ 4 часа)") )

                        id = event.message.from_id
                        user_get = vk_session.method("users.get", {
                            "user_ids": id})  # first_name = user_get[0]['first_name'] or last_name = user_get[0]['last_name']

                        # Берём фото (пока что только 1)
                        try:
                            photo = event.message["attachments"][0]["photo"]["sizes"][4]["url"]  # Берём фотографию

                            Message_for_all[
                                'photo'] = photo  # Словарь который содержит всё, что нужно отправить и прикрепить в дс
                        except:
                            print('Фото Отсутвует')
                            photo = None
                            Message_for_all['photo'] = photo
                        # берём документ
                        # try:
                        # Берём фотографию
                        Forward_msg = Get_forwrd_message_text(event.message)
                        print(Forward_msg)
                        Message_for_all['doc'] = Get_doc(event.message[
                                                             "attachments"])  # Словарь который содержит всё, что нужно отправить и прикрепить в дс
                        # except:
                        # 	print('Фото Отсутвует')
                        # 	photo = None
                        # 	Message_for_all['photo'] = photo
                        Vk_message_is = True


thr1 = Thread(target=bb1)
thr2 = Thread(target=bb2)

thr1.start()
thr2.start()
# +-------------+------------------------+
# |    Field    |         Limit          |
# +-------------+------------------------+
# | title       | 256 characters         |
# | description | 4096 characters*       |
# | fields      | Up to 25 field objects |
# | field.name  | 256 characters         |
# | field.value | 1024 characters        |
# | footer.text | 2048 characters        |
# | author.name | 256 characters         |
# +-------------+------------------------+
