import asyncio
from classes.bot import Discord_Bot
# from class_interface import Command_Line_Interface

def main():
    newBot = Discord_Bot()
    # newInterface = Command_Line_Interface()
    
    try:
        newBot.start_bot()
        # newInterface.run_interface()
    except KeyboardInterrupt:
        # newInterface.stop_interface()
        asyncio.run(newBot.stop_bot())
# main

if __name__ == "__main__":
    main()