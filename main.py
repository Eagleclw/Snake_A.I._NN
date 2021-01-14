import numpy as np
import matplotlib.pyplot as plt
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

def plot_stats():
    global game_data

    if game_data["generation"] - 1 == len(game_data["generation_info"]):
        if game_data["generation"] > 1:

            avg_episode_rewards = []
            episode_actions = []
            gens = list(range(0, game_data["generation"] - 1, 1))

            for i in range(0, len(game_data["generation_info"])):
                avg_episode_rewards.append(game_data["generation_info"][i]["AverageReward"])
                episode_actions.append(game_data["generation_info"][i]["Actions"])

            if len(gens) == len(avg_episode_rewards):
                x_gens = np.array(gens)
                y_rewards = np.array(avg_episode_rewards)
                y_actions = np.array(episode_actions)

                plt.title("Snake AI Stats")
                plt.xlabel("Generations")
                plt.ylabel("Average Episode Rewards")
                plt.plot(x_gens, y_rewards, color="red")
                plt.show()

                plt.title("Snake AI Stats")
                plt.xlabel("Generations")
                plt.ylabel("Episode Actions")
                plt.plot(x_gens, y_actions, color="red")
                plt.show()
            else:
                print("Unexpected error occurred during plot stats process...")
    else:
        print("Invalid game data. Can not plot stats...")

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
    plot_stats()
