from json import dump, load
from game import *
from menu import *

main_menu = "Not initiated yet."
game_data = {}

def load_file():
    global game_data

    try:
        f = open('game_data.json')
        game_data = load(f)
    except:
        game_data = {
                        "best_score": 0,
                        "ai_best_score": 0,
                        "ai_trained_seconds": 0,
                        "epsilon": 1,
                        "generation":1,
                        "generation_info": []
                    }

def save_file():
    global game_data

    with open('game_data.json', 'w') as f:
        dump(game_data, f)

def main():
    global main_menu
    global game_data

    if main_menu == "Not initiated yet." or main_menu == "Deleted.":
        main_menu = Menu()
        if main_menu.state == "playAsPlayer" or main_menu.state == "playAsAI" or main_menu.state == "trainTheAI":
            x = main_menu.state
            del main_menu
            main_menu = "Deleted."
            snake_game = Game(x, game_data)
            if snake_game.game_state == "gameClosed":
                game_data = snake_game.game_data
                del snake_game
        main()

if __name__ == '__main__':
    load_file()
    main()
    save_file()