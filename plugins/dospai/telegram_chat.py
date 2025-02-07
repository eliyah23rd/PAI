"""
Original code for this file created by https://github.com/Wladastic
"""
import asyncio
import traceback

from telegram import Bot, Update
from telegram.ext import CallbackContext
from telegram.error import TimedOut, TelegramError # , BadRequest

response_queue = ""


class TelegramUtils():
    def __init__(self, api_key: str = None, chat_id: str = None, extra_commands = None):
        self.api_key = api_key
        self.chat_id = chat_id
        self._last_update_id = 0
        self._commands = []
        self._extra_commands = [] if extra_commands is None else list(extra_commands)
        # self._ignore_old_updates()

    def is_authorized_user(self, update: Update):
        return update.effective_user.id == int(self.chat_id)

    @staticmethod
    def handle_response(self, update: Update, context: CallbackContext):
        try:
            print("Received response: " + update.message.text)

            if self.is_authorized_user(update):
                response_queue.put(update.message.text)
        except Exception as e:
            print(e)

    def init_commands(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = None
        try:
            if loop and loop.is_running():
                loop.create_task(self.get_bot(binit=True))
            else:
                asyncio.run(self.get_bot(binit=True))
        except TimedOut:
            print('Failed to access telegram messages')
        return

    def ignore_old_updates(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = None
        try:
            if loop and loop.is_running():
                loop.create_task(self._set_last_update_id())
            else:
                asyncio.run(self._set_last_update_id())
        except TimedOut:
            print('Failed to access telegram messages')
        return

    async def _set_last_update_id(self):
        bot = await self.get_bot()
        updates = await bot.get_updates(offset=0)
        if len(updates) > 0:
            self._last_update_id = updates[-1].update_id
        else:
            self._last_update_id = 0


    async def delete_old_messages(self):
        bot = await self.get_bot()
        updates = await bot.get_updates(offset=0)
        count = 0
        for update in updates:
            try:
                print(
                    "Deleting message: "
                    + update.message.text
                    + " "
                    + str(update.message.message_id)
                )
                await bot.delete_message(
                    chat_id=update.message.chat.id, message_id=update.message.message_id
                )
            except Exception as e:
                print(
                    f"Error while deleting message: {e} \n"
                    + f" update: {update} \n {traceback.format_exc()}"
                )
            count += 1
        if count > 0:
            print("Cleaned up old messages.")

    async def get_bot(self, binit = False):
        bot_token = self.api_key
        bot = Bot(token=bot_token)
        if binit:
            await bot.delete_my_commands()
        self._commands = await bot.get_my_commands()
        if len(self._commands) == 0:
            await self.set_commands(bot)
            self._commands = await bot.get_my_commands()
        return bot

    async def set_commands(self, bot):
        await bot.set_my_commands(
            [
                ("start", "Start Auto-GPT"),
                ("stop", "Stop Auto-GPT"),
                ("help", "Show help"),
                ("yes", "Confirm"),
                ("no", "Deny"),
            ]
            +
            self._extra_commands
        )
        pass

    def send_message(self, message):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = None
        if loop and loop.is_running():
            return loop.create_task(self._send_message(message=message))
        else:
            return asyncio.run(self._send_message(message=message))

    def send_voice(self, voice_file):
        try:
            self.get_bot().send_voice(
                chat_id=self.chat_id, voice=open(voice_file, "rb")
            )
        except RuntimeError:
            print("Error while sending voice message")

    async def _send_message(self, message):
        print("Sending message to Telegram.. ")
        recipient_chat_id = self.chat_id
        bot = await self.get_bot()
        try:
            for i in range(0, len(message), 4096):
                await bot.send_message(chat_id=recipient_chat_id, text=message[i:i+4096])
            return f'Telegram message sent: {message}.'
        except TelegramError as te:
            return f'Error sending telegram message. Error {te}'

    async def ask_user_async(self, prompt):
        global response_queue
        question = prompt + " (reply to this message) \n Confirm: /yes     Decline: /no"

        response_queue = ""
        # await delete_old_messages()

        print("Asking user: " + question)
        self.send_message(message=question)

        print("Waiting for response on Telegram chat...")
        await self._poll_updates()

        if response_queue == "/start":
            response_queue = await self.ask_user(
                prompt="I am already here... \n Please use /stop to stop me first."
            )
        if response_queue == "/help":
            response_queue = await self.ask_user(
                prompt="You can use /stop to stop me \n and /start to start me again."
            )

        if response_queue == "/stop":
            self.send_message("Stopping Auto-GPT now!")
            exit(0)
        elif response_queue == "/yes":
            response_text = "yes"
            response_queue = "yes"
        elif response_queue == "/no":
            response_text = "no"
            response_queue = "no"
        if response_queue.capitalize() in [
            "Yes",
            "Okay",
            "Ok",
            "Sure",
            "Yeah",
            "Yup",
            "Yep",
        ]:
            response_text = "y"
        elif response_queue.capitalize() in ["No", "Nope", "Nah", "N"]:
            response_text = "n"
        else:
            response_text = response_queue

        print("Response received from Telegram: " + response_text)
        return response_text

    async def _poll_updates(self):
        global response_queue
        bot = await self.get_bot()

        last_update = await bot.get_updates(timeout=30)
        if len(last_update) > 0:
            last_update_id = last_update[-1].update_id
        else:
            last_update_id = 0

        while True:
            try:
                print("Polling updates...")
                updates = await bot.get_updates(offset=last_update_id + 1, timeout=30)
                for update in updates:
                    if update.message and update.message.text:
                        if self.is_authorized_user(update):
                            response_queue = update.message.text
                            return
                    last_update_id = max(last_update_id, update.update_id)
            except Exception as e:
                print(f"Error while polling updates: {e}")

            await asyncio.sleep(1)

    def ask_user(self, prompt):
        print("Asking user: " + prompt)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = None
        try:
            if loop and loop.is_running():
                return loop.create_task(self.ask_user_async(prompt=prompt))
            else:
                return asyncio.run(self.ask_user_async(prompt=prompt))
        except TimedOut:
            print("Telegram timeout error, trying again...")
            return self.ask_user(prompt=prompt)

    async def _single_poll(self):
        bot = await self.get_bot()

        updates = await bot.get_updates(offset=self._last_update_id + 1, timeout=3)
        if len(updates) > 0:
            last_update_id = updates[-1].update_id
        else:
            return ''

        resposes = ''
        for update in updates:
            if update.message and update.message.text:
                if self.is_authorized_user(update):
                    resposes += update.message.text + '\n'
            self._last_update_id = max(last_update_id, update.update_id)
        return resposes



    async def _user_check_async(self):
        print("Waiting for response on Telegram chat...")
        ret =  await self._single_poll() 
        print("Completed wait for response on Telegram chat...")
        return ret

    def check_for_user_input(self, bblock = False, num_tries=0):
        print("Checking for messages from user")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = None
        try:
            while True:
                if loop and loop.is_running():
                    ret = loop.create_task(self._user_check_async())
                else:
                    ret = asyncio.run(self._user_check_async())
                if not bblock or len(ret) > 0:
                    return ret
        except TimedOut:
            if num_tries < 3:
                print("Telegram timeout error, trying again...")
                return self.check_for_user_input(bblock, num_tries+1)
            else:
                print('Failed to access telegram messages')
                return ''
