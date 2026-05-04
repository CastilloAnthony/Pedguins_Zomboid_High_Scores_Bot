# Developed by Anthony Castillo (ComradeWolf) for Peter Mann (Pedguin)
# Last Update: 04/05/2026 (DD/MM/YYYY)
# WIP (Currently Unused)

from classes.bot import Discord_Bot
import asyncio
from threading import Thread
class Command_Line_Interface():
    def __init__(self):
        self.__commands = ['help', 'commands', 'restart', 'stop', 'start', 'test',] # 'sync'
        self.__confirms = ['y', 'yes', 'confirm']
        self.__running = True
        self.__bot = Discord_Bot()
        self.__bot_thread = None
        self.__command_descriptions = {
            'help': ' Displays the help text for the given command (Usage: "help" or "help commands")',
            'commands': 'Displays a list of commands',
            'start': 'Starts the discord bot.',
            'stop': 'Stops the discord bot.',
            'restart': 'Stops and then restarts the discord bot.',
            'reload': 'Reloads a given module for the bot (Usage: "reload cog_core.py")',
            # 'sync': 'Attempts to sync all discord bot commands.',
            'test': 'blank',
        }
    # end __init__

    def get_user_input(self):
        return input('').lower().split()
    # end get_user_input

    def read_commands(self, user_input:str):
        if user_input[0] in self.__commands:
            if user_input[0] == 'help':
                if len(user_input) == 1:
                    print(f'{user_input[0]}: {self.__command_descriptions[user_input[0]]}')
                elif user_input[1] in self.__commands:
                    print(f'{user_input[1]}: {self.__command_descriptions[user_input[1]]}')
            elif user_input[0] == 'commands':
                print('List of available commands: '+', '.join(self.__commands))
            elif user_input[0] == 'start':
                self.__bot_thread = Thread(target=self.__bot.start_bot, name='Discord_Bot_Main_Thread')
                self.__bot_thread.start()
                # self.__bot.start_bot()
            elif user_input[0] == 'stop':
                asyncio.run(self.__bot.stop_bot())
                self.__bot_thread.join()
            elif user_input[0] == 'restart':
                self.__bot.restart_bot()
            elif user_input[0] == 'reload':
                if len(user_input) == 1:
                    print(f'{user_input[0]}: {self.__command_descriptions[user_input[0]]}')
                else:
                    self.__bot.reload_cog(user_input[1])
            elif user_input[0] == 'test':
                print(self.__bot.get_extensions())
            elif user_input[0] == 'quit':
                self.stop_interface()
    # end read_commands

    def toggle_running(self) -> None:
        if self.__running:
            self.__running = False
        else:
            self.__running = True
    # end toggle_running

    def stop_interface(self):
        asyncio.run(self.__bot.stop_bot())
        self.__bot_thread.join()
        # self.__bot.stop_bot()
        self.toggle_running()
    # end stop_interface

    def run_interface(self):
        print('Interface Ready: ')
        while self.__running:
            user_input = self.get_user_input()
            self.read_commands(user_input)
        # end while
    # end run_interface
# end Interfarce