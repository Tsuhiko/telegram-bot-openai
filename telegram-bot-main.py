import asyncio
import config
import openai
from telethon import TelegramClient, events
from telethon.tl.custom import Button

openai.api_key = config.openai_key

client = TelegramClient(config.session_name_bot, config.API_ID, config.API_HASH, bot_token=config.BOT_TOKEN)

keyboard_stop = [[Button.inline("Зупинити розмову", b"stop")]]

async def send_question_and_retrieve_result(prompt, conv, keyboard):
    message = await conv.send_message(prompt, buttons=keyboard)
    loop = asyncio.get_event_loop()
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
    prompt = "🌟 Привіт, я тут, щоб освітити твій день знаннями та допомогою! 🚀 Якщо тобі потрібна допомога або ти маєш запитання, просто скажи слово, і я перетворю твої сумніви на впевненість! 💡" 
    try:
        await client.send_message(SENDER, prompt)

        async with client.conversation(await event.get_chat(), exclusive=True, timeout=10000) as conv:
            history = []

            while True:
                prompt = "📬 Шановний користувачу, будемо вдячні за ваші думки та ідеї для покращення нашого Telegram-ChatGPT-Bота. Ваш внесок є цінним! ✍️"
                user_input = await send_question_and_retrieve_result(prompt, conv, keyboard_stop)
                if user_input is None:
                    prompt = "✨ Ваш запит оброблено! Щоб почати з чистого аркуша, просто введіть /start. Чекаємо на ваші нові ідеї! 🌟"
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

    except openai.error.OpenAIError as e:
        print(f"Помилка API OpenAI: {e}")
        await client.send_message(SENDER, "Помилка генерації відповіді від API OpenAI. Будь ласка, спробуйте знову пізніше.")

    except asyncio.TimeoutError:
        print("Час розмови минув")
        await client.send_message(SENDER, "<b>Розмова завершена✔️</b>\nПройшло занадто багато часу з моменту вашої останньої відповіді. Будь ласка, введіть /start, щоб розпочати нову розмову.", parse_mode='html')
        return

    except telethon.errors.common.AlreadyInConversationError:
        print("Користувач вже в розмові")
        pass

    except Exception as e: 
        print(f"Сталася помилка: {e}")
        await client.send_message(SENDER, "<b>Розмова завершена✔️</b>\nЩось пішло не так. Будь ласка, введіть /start, щоб розпочати нову розмову.", parse_mode='html')
        return

async def main():
    async with client:
        await client.run_until_disconnected()

if __name__ == "__main__":
    print("Бот запущено...")
    asyncio.run(main())