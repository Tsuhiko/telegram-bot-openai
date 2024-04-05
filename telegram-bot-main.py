import asyncio
import config
import random
import string
import openai
import telethon
from telethon import TelegramClient, events
from telethon.tl.custom import Button
import pymysql

try:
    # Connect to the database
    db_connection = pymysql.connect(
        host='mysql',
        port=3306,
        user='root',
        password=config.MYSQL_ROOT_PASSWORD,
        database=config.MYSQL_DATABASE
    )

except pymysql.Error as e:
    # Handle errors in connecting to the database
    with open("mysql_error_log.txt", "w") as file:
        file.write(f"Помилка при з'єднанні з MySQL: {e}")

else:
    try:
        # Create a cursor object
        cursor = db_connection.cursor()

        # Create the database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS " + config.MYSQL_DATABASE)

        # Switch to the specified database
        cursor.execute("USE " + config.MYSQL_DATABASE)

        # Create the sessions table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INT AUTO_INCREMENT PRIMARY KEY,
                session_uuid VARCHAR(255) NOT NULL,
                user_id INT NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    except pymysql.Error as e:
        # Handle errors in executing SQL queries
        with open("error_log.txt", "w") as file:
            file.write(f"Помилка при виконанні запиту до бази даних: {e}")
    finally:
        # Close the cursor and connection
        if 'cursor' in locals():
            cursor.close()

finally:
    # Close the connection
    if 'db_connection' in locals():
        db_connection.close()

def generate_uuid():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

async def save_message_to_db(session_uuid, user_id, message, response):
    try:
        db_connection = pymysql.connect(
            host='mysql',
            user='root',
            password=config.MYSQL_ROOT_PASSWORD,
            database=config.MYSQL_DATABASE,
            port=3306
        )
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO sessions (session_uuid, user_id, message, response) VALUES (%s, %s, %s, %s)",
                       (session_uuid, user_id, message, response))
        db_connection.commit()
        cursor.close()
        db_connection.close()
    except Exception as e:
        print(f"Помилка при записі до бази даних: {e}")

openai.api_key = config.openai_key

client = TelegramClient(config.session_name_bot, config.API_ID, config.API_HASH).start(bot_token=config.BOT_TOKEN)

keyboard_stop = [[Button.inline("Зупинити розмову", b"stop")]]

async def send_question_and_retrieve_result(prompt, conv, keyboard):
    message = await conv.send_message(prompt, buttons=keyboard)
    loop = asyncio.get_running_loop()
    task1 = loop.create_task(conv.wait_event(events.CallbackQuery()))
    task2 = loop.create_task(conv.get_response())
    done, _ = await asyncio.wait({task1, task2}, return_when=asyncio.FIRST_COMPLETED)
    result = done.pop().result()
    await message.delete()

    if isinstance(result, events.CallbackQuery.Event):
        return None
    else:
        return result.message.strip()

@client.on(events.NewMessage(pattern="(?i)/start"))
async def handle_start_command(event):
    SENDER = event.sender_id
    session_uuid = generate_uuid()
    prompt = "🌟 Привіт, я тут, щоб освітити твій день знаннями та допомогою! 🚀"
    try:
        await client.send_message(SENDER, prompt)
        async with client.conversation(await event.get_chat(), exclusive=True, timeout=10000) as conv:
            history = []
            while True:
                prompt = "📬 Шановний користувачу, будемо вдячні за ваші думки та ідеї для покращення нашого Telegram-ChatGPT-Bота. Ваш внесок є цінним! ✍️"
                user_input = await send_question_and_retrieve_result(prompt, conv, keyboard_stop)
                if user_input is None:
                    prompt = "✨ Ваш запит оброблено! Щоб почати з чистого аркуша, просто введіть /start."
                    await client.send_message(SENDER, prompt)
                    break
                else:
                    prompt = "✅ Отримано! Розглядаю ваше запитання та скоро надам відповідь. 🤓"
                    thinking_message = await client.send_message(SENDER, prompt)
                    history.append({"role":"user", "content": user_input})
                    chat_completion = openai.ChatCompletion.create(
                        model=config.model_engine,
                        messages=history,
                        max_tokens=500,
                        n=1,
                        temperature=0.1
                    )
                    response = chat_completion.choices[0].message.content
                    history.append({"role": "assistant", "content": response})
                    await thinking_message.delete()
                    await client.send_message(SENDER, response, parse_mode='Markdown')
                    await save_message_to_db(session_uuid, SENDER, user_input, response)
    except openai.error.OpenAIError as e:
        print(f"Помилка API OpenAI: {e}")
        await client.send_message(SENDER, "Помилка генерації відповіді від API OpenAI. Будь ласка, спробуйте знову пізніше.")
    except asyncio.TimeoutError:
        print("Час розмови минув")
        await client.send_message(SENDER, "<b>Розмова завершена✔️</b>\nПройшло занадто багато часу з моменту вашої останньої відповіді. Будь ласка, введіть /start, щоб розпочати нову розмову.", parse_mode='html')
    except Exception as e: 
        print(f"Сталася помилка: {e}")
        await client.send_message(SENDER, "<b>Розмова завершена✔️</b>\nЩось пішло не так. Будь ласка, введіть /start, щоб розпочати нову розмову.", parse_mode='html')

if __name__ == "__main__":
    print("Бот запущено...")
    client.run_until_disconnected()
