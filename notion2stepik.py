# Run with Python 3

import requests, html, json, os.path
from notion.client import NotionClient

''' 

Настройки, которые задают, что и куда нужно копировать  
Измените их перед началом работы

'''

notion_url = "https://www.notion.so/firstwebapp/f084b3b40ce244f7b6b34e82a60ab24b"
stepik_lesson = 277089

'''

Класс, который делает все копирование

'''

class NotionToStepik():

    notion_client = None
    stepik_token = None

    def __init__(self, notion_token, stepik_id, stepik_secret):

        self.notion_client = NotionClient(token_v2=notion_token)
        print("Соединение с Notion установлено...")

        self.stepik_get_token(stepik_id, stepik_secret)
        print("Соединение со Stepik установлено...")

    def stepik_get_token(self, stepik_id, stepik_secret):

        auth = requests.auth.HTTPBasicAuth(stepik_id, stepik_secret)
        response = requests.post('https://stepik.org/oauth2/token/', data={'grant_type': 'client_credentials'},
                                 auth=auth)
        token = response.json().get('access_token', None)
        if not token:
            print('Unable to authorize with provided credentials')
            exit(1)

        self.stepik_token = token
        return True

    def notion_get_page(self, url):

        page = self.notion_client.get_block(url)

        return page

    def notion_convert_page(self, page):

        def convert_block(block):

            print(".",end="") # делаем небольшую анимацию процесса обработки блоков

            if block._type == "text":
                if len(block.title)<1 :
                    return ""
                return "<p>{}</p>\r\n".format(block.title)
            elif block._type in ["header", "sub_header"]:
                return "<h2>{}</h2>\r\n".format(block.title)

            elif block._type == "sub_sub_header":
                return "<p><b>{}</b></p>\r\n".format(block.title)

            elif block._type =="code":
                code = html.escape(block.title)
                return "<pre><code class='language-python'>\r\n{}</code></pre>\r\n".format(code)

            elif block._type =="divider":
                return "<hr>\r\n"

            elif block._type in ["bulleted_list","numbered_list"]:
                return "<li>{}</li>\r\n".format(block.title)

            else:
                return ""

        blocks = page.children  # получаем список блоков
        output = "<h1>{}</h1>".format(page.title)  # сюда пишем название страницы

        print("Найдено {} блоков на странице {} ".format(len(blocks), page.title))

        for block in blocks:
            output += convert_block(block)

        print()

        return output


    def stepik_split_and_push(self, lesson, content):

        steps = content.split("<hr>")

        print("Делим на степы, найдено {} степов".format(len(steps)))

        for stepcontent in steps:
            self.stepik_push_text_step(lesson,stepcontent)

    def stepik_push_text_step(self, lesson, content,position=1):

        # print("Добавляем шаг в начало")

        api_url = 'https://stepik.org/api/step-sources'

        data = {
            'stepSource': {
                'block': {
                    'name': 'text',
                    'text': content
                },
                'lesson': lesson,
                'position': position
            }
        }

        r = requests.post(api_url, headers={'Authorization': 'Bearer ' + self.stepik_token}, json=data)

        step_id = r.json()['step-sources'][0]['id']

        return step_id

    def stepik_push_mcq_step(self, lesson, quiz):
        pass


print("*"*64,"\r\n","Привет! Notion 2 Stepik превращает страничку на Notion в шаги на Stepik!","\r\n"+"*"*64,"\r\n")

if not os.path.exists("config.json"):

    config = {}

    print("У меня пока нет ключей к Notion и Stepik.\r\nВведи их, пожалуйста.\r\nТебе пригодится инструкция: https://github.com/kushedow/NotionToStepik \r\n ")
    config['notion_token'] = input("Введи Notion token_v2 ")
    config['stepik_id'] = input("Введи Stepic id")
    config['stepik_secret'] = input("Введи Stepic Secret")

    with open("config.json", "w") as f:
        f.write(json.dumps(config))
        print("Настройки сохранены в файле config.json – там ты сможешь их изменить!")

else:

    print("Настройки найдены, работаем...")
    with open("config.json", "r") as f:
        config = json.load(f)


n2s = NotionToStepik(config['notion_token'], config['stepik_id'], config['stepik_secret'])

page = n2s.notion_get_page(notion_url)
content = n2s.notion_convert_page(page)
n2s.stepik_split_and_push(stepik_lesson,content)

print("Готово: https://stepik.org/lesson/{}".format(stepik_lesson))
