import telethon
from telethon.tl.custom import Button
from telethon import TelegramClient, events

import asyncio
import config
import openai

openai.api_key = config.openai_key  # Встановлює ключ OpenAI API з конфігураційного файлу

client = TelegramClient(config.session_name_bot, config.API_ID, config.API_HASH).start(bot_token=config.BOT_TOKEN)  # Підключаємося до Telegram за допомогою Telethon

keyboard_stop = [[Button.inline("Зупинити розмову", b"stop")]]  # Створюємо клавіатуру для зупинки розмови

async def send_question_and_retrieve_result(prompt, conv, keyboard):

    message = await conv.send_message(prompt, buttons=keyboard)  # Надсилаємо запит та отримуємо повідомлення

    loop = asyncio.get_event_loop()  # Отримуємо цикл подій asyncio

    task1 = loop.create_task(
        conv.wait_event(events.CallbackQuery())
    )  # Створюємо завдання для очікування події з кнопкою
    task2 = loop.create_task(
        conv.get_response()
    )  # Створюємо завдання для отримання відповіді від користувача

    done, _ = await asyncio.wait({task1, task2}, return_when=asyncio.FIRST_COMPLETED)  # Очікуємо на завершення будь-якої з подій

    result = done.pop().result()  # Отримуємо результат першої завершеної події
    await message.delete()  # Видаляємо повідомлення

    if isinstance(result, events.CallbackQuery.Event):  # Перевіряємо, чи користувач натиснув кнопку зупинки
        return None
    else:
        return result.message.strip()  # Повертаємо відповідь користувача


@client.on(events.NewMessage(pattern="(?i)/start"))  # Обробник команди /start
async def handle_start_command(event):

    SENDER = event.sender_id  # Отримуємо ідентифікатор відправника
    prompt = "🌟 Привіт, я тут, щоб освітити твій день знаннями та допомогою! 🚀 Якщо тобі потрібна допомога або ти маєш запитання, просто скажи слово, і я перетворю твої сумніви на впевненість! 💡" 
    try:
        await client.send_message(SENDER, prompt)  # Надсилаємо початкове повідомлення

        async with client.conversation(await event.get_chat(), exclusive=True, timeout=10000) as conv:
            history = []  # Історія розмови

            while True:
                prompt = "📬 Шановний користувачу, будемо вдячні за ваші думки та ідеї для покращення нашого Telegram-ChatGPT-Bота. Ваш внесок є цінним! ✍️"
                user_input = await send_question_and_retrieve_result(prompt, conv, keyboard_stop)  # Отримуємо введення користувача
                
                if user_input is None:  # Перевіряємо, чи користувач вирішив зупинити розмову
                    prompt = "✨ Ваш запит оброблено! Щоб почати з чистого аркуша, просто введіть /start. Чекаємо на ваші нові ідеї! 🌟"
                    await client.send_message(SENDER, prompt)  # Повідомлення про завершення розмови
                    break
                else:
                    prompt = "✅ Отримано! Розглядаю ваше запитання та скоро надам відповідь. 🤓"
                    thinking_message = await client.send_message(SENDER, prompt)  # Повідомлення про обробку запиту

                    history.append({"role":"user", "content": user_input})  # Додаємо введення користувача до історії

                    chat_completion = openai.ChatCompletion.create(
                        model=config.model_engine,
                        messages=history,
                        max_tokens=500,
                        n=1,
                        temperature=0.1
                    )  # Запит до OpenAI для створення відповіді

                    response = chat_completion.choices[0].message.content  # Отримуємо відповідь від OpenAI

                    history.append({"role": "assistant", "content": response})  # Додаємо відповідь до історії

                    await thinking_message.delete()  # Видаляємо повідомлення про обробку

                    await client.send_message(SENDER, response, parse_mode='Markdown')  # Надсилаємо відповідь користувачу

    except openai.error.OpenAIError as e:
        print(f"Помилка API OpenAI: {e}")  # Обробка помилок OpenAI
        await client.send_message(SENDER, "Помилка генерації відповіді від API OpenAI. Будь ласка, спробуйте знову пізніше.")

    except asyncio.TimeoutError:
        print("Час розмови минув")  # Обробка випадку, коли час розмови минув
        await client.send_message(SENDER, "<b>Розмова завершена✔️</b>\nПройшло занадто багато часу з моменту вашої останньої відповіді. Будь ласка, введіть /start, щоб розпочати нову розмову.", parse_mode='html')
        return

    except telethon.errors.common.AlreadyInConversationError:
        print("Користувач вже в розмові")  # Обробка випадку, коли користувач вже в розмові
        pass

    except Exception as e: 
        print(f"Сталася помилка: {e}")  # Обробка загальних помилок
        await client.send_message(SENDER, "<b>Розмова завершена✔️</b>\nЩось пішло не так. Будь ласка, введіть /start, щоб розпочати нову розмову.", parse_mode='html')
        return

if __name__ == "__main__":
    print("Бот запущено...")  # Виводимо повідомлення про запуск бота
    client.run_until_disconnected()  # Запускаємо бота``