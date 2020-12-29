from collections import deque
from math import trunc
from tkinter import Tk, Canvas, Frame, BOTH, messagebox, Button, Label, LEFT, RIGHT
from ai import *
from random import randint
from time import time
import sys
import datetime

class Game:
    def __init__(self, run_type, game_data):
        self.game_state = "gameRunning"
        self.run_type = run_type
        self.game_data = game_data

        self.window = Tk()
        self.frame = Frame(self.window)
        self.canvas = Canvas(self.frame)
        self.tickID = None

        self.play_speed = 10
        self.train_speed = 1000
        self.walls_blocked = True
        if run_type == "playAsPlayer":
            self.auto_start = False
        else:
            self.auto_start = True

        self.X, self.Y = (10, 10)
        self.BLOCK_SIZE = 50
        self.BACKGROUND_COLOR = '#303030'
        self.SNAKE_COLOR = '#0f0'
        self.SNAKE_HEAD_COLOR = '#003300'
        self.FOOD_COLOR = '#f00'
        self.INITIAL_SPEED = self.play_speed
        if run_type == "trainTheAI":
            self.INITIAL_SPEED = self.train_speed
        self.PAUSED = 0

        self.DIRECTION_NONE = 'None'
        self.KEY_LEFT = 'Left'
        self.KEY_RIGHT = 'Right'
        self.KEY_UP = 'Up'
        self.KEY_DOWN = 'Down'
        self.KEY_QUIT = 'q'
        self.KEY_PAUSE = 'p'

        self.VALID_DIRECTIONS = {
            self.DIRECTION_NONE: {self.KEY_LEFT, self.KEY_RIGHT, self.KEY_UP, self.KEY_DOWN},
            self.KEY_LEFT: {self.KEY_LEFT, self.KEY_UP, self.KEY_DOWN},
            self.KEY_RIGHT: {self.KEY_RIGHT, self.KEY_UP, self.KEY_DOWN},
            self.KEY_UP: {self.KEY_UP, self.KEY_LEFT, self.KEY_RIGHT},
            self.KEY_DOWN: {self.KEY_DOWN, self.KEY_LEFT, self.KEY_RIGHT}
        }

        self.MOVEMENTS = {
            self.DIRECTION_NONE: lambda x, y: (x, y),
            self.KEY_LEFT: lambda x, y: (x - 1, y),
            self.KEY_RIGHT: lambda x, y: (x + 1, y),
            self.KEY_UP: lambda x, y: (x, y - 1),
            self.KEY_DOWN: lambda x, y: (x, y + 1)
        }

        print("\n------------------------------")
        print(datetime.datetime.now(tz=datetime.timezone.utc).strftime("%d.%m.%Y %H:%M:%S"))
        print("------------------------------")
        if run_type == "playAsPlayer":
            print("Game Created for player to play.")
        elif run_type == "playAsAI":
            print("Game Created for AI to play.")
        elif run_type == "trainTheAI":
            self.start_time = time()
            print("AI Total Trained Time : " + self.normalize_seconds(self.game_data['ai_trained_seconds']))
            print("------------------------------")
            print("Game Created for AI to train.")
        print("---------------")

        self.game = self.create_game()
        self.running_time = 0
        self.snake_ai = None
        self.ai_input_shape = (32, 1)
        self.invalid_distance = ((self.X * self.X) + (self.Y * self.Y)) ** 0.5
        self.initial_loop_limit = self.X * self.Y
        self.current_loop_limit = self.initial_loop_limit
        self.reward = 0
        self.episode_reward = 0
        self.done = False
        self.state = None
        self.next_state = None
        self.action = None
        self.main()

    def on_closing(self):
        self.window.after_cancel(self.tickID)
        self.window.destroy()
        self.game_state = "gameClosed"
        del self.snake_ai

    def __del__(self):
        if self.run_type == "playAsPlayer":
            print("---------------")
        print("Game Closed.")
        print("------------------------------")
        if self.run_type == "trainTheAI":
            self.running_time += round(time() - self.start_time)
            self.game_data['ai_trained_seconds'] += self.running_time
            print("AI Total Trained Time : " + self.normalize_seconds(self.game_data['ai_trained_seconds']))
            print("------------------------------")
        print(datetime.datetime.now(tz=datetime.timezone.utc).strftime("%d.%m.%Y %H:%M:%S"))
        print("------------------------------\n")

    def normalize_seconds(self, seconds):
        (days, remainder) = divmod(seconds, 60*60*24)
        (hours, remainder) = divmod(remainder, 60*60)
        (minutes, seconds) = divmod(remainder, 60)
        return "{:03d} Days {:02d} Hours {:02d} Minutes {:02d} Seconds".format(days, hours, minutes, seconds)

    def setup_game(self):
        self.window.focus_force()
        window_width, window_height = (self.X * self.BLOCK_SIZE, self.Y * self.BLOCK_SIZE)
        ''' window_width, window_height --> Width and height of window. '''
        screen_width, screen_height = (self.window.winfo_screenwidth(), self.window.winfo_screenheight())
        ''' screen_width, screen_height --> Width and height of screen. '''
        x_coordinate, y_coordinate = (int((screen_width / 2) - (window_width / 2)),
                                      int((screen_height / 2) - (window_height / 2)))
        ''' x_coordinate, y_coordinate --> The starting points of window. '''

        self.window.geometry("{}x{}+{}+{}".format(window_width, window_height, x_coordinate, y_coordinate))
        self.window.resizable(False, False)

        self.frame.master.title("Snake Game   |   SCORE : 0   |   Best Score : 0    |   Best AI Score : 0 ")
        self.frame.pack(fill=BOTH, expand=1)
        self.canvas.pack(fill=BOTH, expand=1)

    def create_game(self):
        snake_randX = randint(0, self.X - 1)
        snake_randY = randint(0, self.Y - 1)

        direction_selector = 0
        if self.auto_start:
            direction_selector = randint(1, len(self.VALID_DIRECTIONS) - 1)

        food_randX = randint(0, self.X - 1)
        food_randY = randint(0, self.Y - 1)
        while (food_randX, food_randY) == (snake_randX, snake_randY):
            food_randX = randint(0, self.X - 1)
            food_randY = randint(0, self.Y - 1)

        return {
            'snake': deque(((snake_randX, snake_randY), (snake_randX, snake_randY))),
            'food': (food_randX, food_randY),
            'direction': list(self.VALID_DIRECTIONS.keys())[direction_selector],
            'moves': deque(),
            'points': 0,
            'speed': self.INITIAL_SPEED
        }

    def reset(self):
        if self.run_type == "playAsPlayer":
            self.message_box('You Lost!', 'Play again...')
            print("Player Score: " + str(self.game['points']) +
                  "   |   Best Player Score: " + str(self.game_data['best_score']))

        elif self.run_type == "playAsAI":
            print("AI Score: " + str(self.game['points']) +
                  "   |   Best AI Score: " + str(self.game_data['ai_best_score']))

        elif self.run_type == "trainTheAI":
            self.next_state = self.get_state()
            self.snake_ai.remember(self.state, self.action, self.reward, self.next_state, self.done)
            self.episode_reward += self.reward
            training_info = self.snake_ai.replay()
            if training_info is not None:
                self.game_data['generation_info'].append(training_info)
                self.game_data['epsilon'] = self.snake_ai.epsilon
                self.game_data['generation'] = self.snake_ai.gen_count
                print("Best Score : " + str(self.game_data['best_score']) + " | Best AI Score : " + str(self.game_data['ai_best_score']))
                print("--------------------------------------------------")

            self.done = False
            self.reward = 0
            self.episode_reward = 0
            self.current_loop_limit = self.initial_loop_limit

        current_speed = self.game['speed']
        self.game = self.create_game()
        self.game['speed'] = current_speed

    def message_box(self, subject, content):
        root = Tk()
        root.attributes("-topmost", True)
        root.withdraw()
        messagebox.showinfo(subject, content)
        try:
            root.destroy()
        except e:
            pass

    def draw_rect(self, x, y, color=None):
        if color is None:
            color = self.SNAKE_COLOR
        x1 = x * self.BLOCK_SIZE
        y1 = y * self.BLOCK_SIZE
        x2 = x1 + self.BLOCK_SIZE
        y2 = y1 + self.BLOCK_SIZE
        return self.canvas.create_rectangle(x1, y1, x2, y2, outline='', fill=color)

    def render(self):
        self.canvas.delete('all')
        self.canvas.configure(background=self.BACKGROUND_COLOR)

        for i in range((len(self.game['snake']) - 1), 0, -1):
            if i == (len(self.game['snake']) - 1):
                self.draw_rect(self.game['snake'][i][0], self.game['snake'][i][1], self.SNAKE_HEAD_COLOR)
            else:
                self.draw_rect(self.game['snake'][i][0], self.game['snake'][i][1])

        x, y = self.game['food']
        self.draw_rect(x, y, color=self.FOOD_COLOR)

    def gen_food(self, snake):
        while True:
            food = randint(0, self.X - 1), randint(0, self.Y - 1)
            if food not in snake:
                return food

    def eat(self, snake):
        self.game['food'] = self.gen_food(snake)
        self.game['points'] += 1

        if self.run_type == "playAsPlayer":
            if self.game['points'] > self.game_data['best_score']:
                self.game_data['best_score'] = self.game['points']
        else:
            if self.game['points'] > self.game_data['ai_best_score']:
                self.game_data['ai_best_score'] = self.game['points']

        if self.run_type == "trainTheAI":
            self.reward = 1
            self.current_loop_limit = self.initial_loop_limit

    def move_snake(self, direction):
        snake = set(self.game['snake'])
        u, w = self.game['snake'][-1]
        next_point = self.MOVEMENTS[direction](u, w)

        x, y = next_point

        if self.walls_blocked and (x<0 or x >= self.X or y < 0 or y >= self.Y):
            if self.run_type == "trainTheAI":
                self.reward = -1
                self.done = True
            self.reset()
        else:
            if x < 0:
                x = x + self.X
            if x >= self.X:
                x = x - self.X
            if y < 0:
                y = y + self.Y
            if y >= self.Y:
                y = y - self.Y

            next_point = x, y

            if next_point == self.game['food'] or self.game['snake'][-1] == self.game['food']:
                self.eat(snake)
            else:
                self.game['snake'].popleft()
                if self.run_type == "trainTheAI":
                    self.reward = - 0.1
                    self.current_loop_limit -= 1

            self.frame.master.title("Snake Game   |   SCORE : " + str(self.game['points']) +
                                    "   |   Best Score : " + str(self.game_data['best_score']) +
                                    "   |   Best AI Score : " + str(self.game_data['ai_best_score']))

            in_snake = 0

            if len(self.game['snake']) > 1:
                for i in range(1, len(self.game['snake'])):
                    if next_point == self.game['snake'][i]:
                        in_snake = 1

                if in_snake == 1:
                    if self.run_type == "trainTheAI":
                        self.reward = -1
                        self.done = True
                    self.reset()
                else:
                    self.game['snake'].append(next_point)
            else:
                self.game['snake'].append(next_point)

            if self.run_type == "trainTheAI" and self.current_loop_limit == 0:
                self.done = True
                self.reset()

    def handle_next_movement(self):
        direction = self.game['moves'].popleft() if self.game['moves'] else self.game['direction']
        self.game['direction'] = direction
        self.move_snake(direction)

    def on_press(self, event):
        key = event.keysym
        if self.PAUSED == 0 and self.run_type == "playAsPlayer":
            prev_direction = self.game['moves'][-1] if self.game['moves'] else self.game['direction']
            if key in self.VALID_DIRECTIONS[prev_direction]:
                self.game['moves'].append(key)
        if key.lower() == self.KEY_QUIT:
            self.on_closing()
        elif key.lower() == self.KEY_PAUSE:
            if self.PAUSED == 0:
                self.PAUSED = 1
                self.frame.master.title("Snake Game   |   PAUSED.")
                if self.run_type == "trainTheAI":
                    self.running_time += round(time() - self.start_time)
            else:
                self.PAUSED = 0
                self.frame.master.title("Snake Game   |   SCORE : " + str(self.game['points']) +
                                        "   |   Best Score : " + str(self.game_data['best_score']) +
                                        "   |   Best AI Score : " + str(self.game_data['ai_best_score']))

                if self.run_type == "trainTheAI":
                    self.start_time = time()

    def tick(self):
        if self.PAUSED == 0:
            if self.run_type == "playAsPlayer":
                self.handle_next_movement()
                self.render()
            else:
                self.Algorithm()

        self.tickID = self.window.after(int(1000 / self.game['speed']), self.tick)

    def calculate_distance(self, x1, x2, y1, y2):
        distance_x = float(abs(x2 - x1))
        distance_y = float(abs(y2 - y1))
        distance = ((distance_x * distance_x) + (distance_y * distance_y)) ** 0.5
        return distance

    def get_key(self, action):
        tmp = self.snake_ai.availableActions[action]

        if self.game['direction'] == 'Left' and tmp == 'Left':
            return 'Down'
        if self.game['direction'] == 'Left' and tmp == 'Right':
            return 'Up'
        if self.game['direction'] == 'Right' and tmp == 'Left':
            return 'Up'
        if self.game['direction'] == 'Right' and tmp == 'Right':
            return 'Down'
        if self.game['direction'] == 'Up' and tmp == 'Left':
            return 'Left'
        if self.game['direction'] == 'Up' and tmp == 'Right':
            return 'Right'
        if self.game['direction'] == 'Down' and tmp == 'Left':
            return 'Right'
        if self.game['direction'] == 'Down' and tmp == 'Right':
            return 'Left'
        if tmp == 'None':
            return self.game['direction']

    def get_state(self):
        """ Wall Distance Vision """
        n_vision_wall = self.calculate_distance(self.game['snake'][-1][0], self.game['snake'][-1][0], self.game['snake'][-1][1], 0)
        s_vision_wall = self.calculate_distance(self.game['snake'][-1][0], self.game['snake'][-1][0], self.game['snake'][-1][1], self.Y - 1)
        e_vision_wall = self.calculate_distance(self.game['snake'][-1][0], self.X - 1, self.game['snake'][-1][1], self.game['snake'][-1][1])
        w_vision_wall = self.calculate_distance(self.game['snake'][-1][0], 0, self.game['snake'][-1][1], self.game['snake'][-1][1])
        ne_vision_wall = self.calculate_distance(self.game['snake'][-1][1], 0, self.game['snake'][-1][1], 0)
        if e_vision_wall <  n_vision_wall:
            ne_vision_wall = self.calculate_distance(self.game['snake'][-1][0], self.X - 1, self.game['snake'][-1][0], self.X - 1)
        se_vision_wall = self.calculate_distance(self.game['snake'][-1][1], self.Y - 1, self.game['snake'][-1][1], self.Y - 1)
        if e_vision_wall < s_vision_wall:
            se_vision_wall = self.calculate_distance(self.game['snake'][-1][0], self.X - 1, self.game['snake'][-1][0], self.X - 1)
        sw_vision_wall = self.calculate_distance(self.game['snake'][-1][1], self.Y - 1, self.game['snake'][-1][1], self.Y - 1)
        if w_vision_wall < s_vision_wall:
            sw_vision_wall = self.calculate_distance(self.game['snake'][-1][0], 0, self.game['snake'][-1][0], 0)
        nw_vision_wall = self.calculate_distance(self.game['snake'][-1][1], 0, self.game['snake'][-1][1], 0)
        if w_vision_wall < n_vision_wall:
            nw_vision_wall = self.calculate_distance(self.game['snake'][-1][0], 0, self.game['snake'][-1][0], 0)

        """ Apple Distance Vision """
        n_vision_apple = self.invalid_distance
        if self.game['snake'][-1][0] == self.game['food'][0] and self.game['snake'][-1][1] > self.game['food'][1]:
            n_vision_apple = self.calculate_distance(self.game['snake'][-1][0], self.game['food'][0], self.game['snake'][-1][1], self.game['food'][1])

        s_vision_apple = self.invalid_distance
        if self.game['snake'][-1][0] == self.game['food'][0] and self.game['snake'][-1][1] < self.game['food'][1]:
            s_vision_apple = self.calculate_distance(self.game['snake'][-1][0], self.game['food'][0], self.game['snake'][-1][1], self.game['food'][1])

        e_vision_apple = self.invalid_distance
        if self.game['snake'][-1][1] == self.game['food'][1] and self.game['snake'][-1][0] < self.game['food'][0]:
            e_vision_apple = self.calculate_distance(self.game['snake'][-1][0], self.game['food'][0], self.game['snake'][-1][1], self.game['food'][1])

        w_vision_apple = self.invalid_distance
        if self.game['snake'][-1][1] == self.game['food'][1] and self.game['snake'][-1][0] > self.game['food'][0]:
            w_vision_apple = self.calculate_distance(self.game['snake'][-1][0], self.game['food'][0], self.game['snake'][-1][1], self.game['food'][1])

        ne_vision_apple = self.invalid_distance
        x, y = self.game['snake'][-1]
        while x < self.X - 1 and y > 1:
            x += 1
            y -= 1
            if self.game['food'] == (x, y):
                ne_vision_apple = self.calculate_distance(self.game['snake'][-1][0], self.game['food'][0], self.game['snake'][-1][1], self.game['food'][1])
                break

        se_vision_apple = self.invalid_distance
        x, y = self.game['snake'][-1]
        while x < self.X - 1 and y < self.Y - 1:
            x += 1
            y += 1
            if self.game['food'] == (x, y):
                se_vision_apple = self.calculate_distance(self.game['snake'][-1][0], self.game['food'][0], self.game['snake'][-1][1], self.game['food'][1])
                break

        nw_vision_apple = self.invalid_distance
        x, y = self.game['snake'][-1]
        while x > 1 and y > 1:
            x -= 1
            y -= 1
            if self.game['food'] == (x, y):
                nw_vision_apple = self.calculate_distance(self.game['snake'][-1][0], self.game['food'][0], self.game['snake'][-1][1], self.game['food'][1])
                break

        sw_vision_apple = self.invalid_distance
        x, y = self.game['snake'][-1]
        while x > 1 and y < self.Y - 1:
            x -= 1
            y += 1
            if self.game['food'] == (x, y):
                sw_vision_apple = self.calculate_distance(self.game['snake'][-1][0], self.game['food'][0], self.game['snake'][-1][1], self.game['food'][1])
                break

        """ Snake Distance Vision """
        n_vision_snake = self.invalid_distance
        if len(self.game['snake']) > 1:
            x, y = self.game['snake'][-1]
            while y > 1:
                y -= 1
                for i in range(1, len(self.game['snake'])):
                    if (x, y) == self.game['snake'][i]:
                        tmp_n_vision_snake = self.calculate_distance(self.game['snake'][-1][0], self.game['snake'][i][0], self.game['snake'][-1][1], self.game['snake'][i][1])
                        if tmp_n_vision_snake < n_vision_snake:
                            n_vision_snake = tmp_n_vision_snake

        s_vision_snake = self.invalid_distance
        if len(self.game['snake']) > 1:
            x, y = self.game['snake'][-1]
            while y < self.Y - 1:
                y += 1
                for i in range(1, len(self.game['snake'])):
                    if (x, y) == self.game['snake'][i]:
                        tmp_s_vision_snake = self.calculate_distance(self.game['snake'][-1][0], self.game['snake'][i][0], self.game['snake'][-1][1], self.game['snake'][i][1])
                        if tmp_s_vision_snake < s_vision_snake:
                            s_vision_snake = tmp_s_vision_snake

        e_vision_snake = self.invalid_distance
        if len(self.game['snake']) > 1:
            x, y = self.game['snake'][-1]
            while x < self.X - 1:
                x += 1
                for i in range(1, len(self.game['snake'])):
                    if (x, y) == self.game['snake'][i]:
                        tmp_e_vision_snake = self.calculate_distance(self.game['snake'][-1][0], self.game['snake'][i][0], self.game['snake'][-1][1], self.game['snake'][i][1])
                        if tmp_e_vision_snake < e_vision_snake:
                            e_vision_snake = tmp_e_vision_snake

        w_vision_snake = self.invalid_distance
        if len(self.game['snake']) > 1:
            x, y = self.game['snake'][-1]
            while x > 0:
                x -= 1
                for i in range(1, len(self.game['snake'])):
                    if (x, y) == self.game['snake'][i]:
                        tmp_w_vision_snake = self.calculate_distance(self.game['snake'][-1][0], self.game['snake'][i][0], self.game['snake'][-1][1], self.game['snake'][i][1])
                        if tmp_w_vision_snake < w_vision_snake:
                            w_vision_snake = tmp_w_vision_snake

        ne_vision_snake = self.invalid_distance
        if len(self.game['snake']) > 1:
            x, y = self.game['snake'][-1]
            while x < self.X - 1 and y > 1:
                x += 1
                y -= 1
                for i in range(1, len(self.game['snake'])):
                    if (x, y) == self.game['snake'][i]:
                        tmp_ne_vision_snake = self.calculate_distance(self.game['snake'][-1][0], self.game['snake'][i][0], self.game['snake'][-1][1], self.game['snake'][i][1])
                        if tmp_ne_vision_snake < ne_vision_snake:
                            ne_vision_snake = tmp_ne_vision_snake

        se_vision_snake = self.invalid_distance
        if len(self.game['snake']) > 1:
            x, y = self.game['snake'][-1]
            while x < self.X - 1 and y < self.Y - 1:
                x += 1
                y += 1
                for i in range(1, len(self.game['snake'])):
                    if (x, y) == self.game['snake'][i]:
                        tmp_se_vision_snake = self.calculate_distance(self.game['snake'][-1][0], self.game['snake'][i][0], self.game['snake'][-1][1], self.game['snake'][i][1])
                        if tmp_se_vision_snake < se_vision_snake:
                            se_vision_snake = tmp_se_vision_snake

        nw_vision_snake = self.invalid_distance
        if len(self.game['snake']) > 1:
            x, y = self.game['snake'][-1]
            while x > 1 and y > 1:
                x -= 1
                y -= 1
                for i in range(1, len(self.game['snake'])):
                    if (x, y) == self.game['snake'][i]:
                        tmp_nw_vision_snake = self.calculate_distance(self.game['snake'][-1][0], self.game['snake'][i][0], self.game['snake'][-1][1], self.game['snake'][i][1])
                        if tmp_nw_vision_snake < nw_vision_snake:
                            nw_vision_snake = tmp_nw_vision_snake

        sw_vision_snake = self.invalid_distance
        if len(self.game['snake']) > 1:
            x, y = self.game['snake'][-1]
            while x > 1 and y < self.Y - 1:
                x -= 1
                y += 1
                for i in range(1, len(self.game['snake'])):
                    if (x, y) == self.game['snake'][i]:
                        tmp_sw_vision_snake = self.calculate_distance(self.game['snake'][-1][0], self.game['snake'][i][0], self.game['snake'][-1][1], self.game['snake'][i][1])
                        if tmp_sw_vision_snake < sw_vision_snake:
                            sw_vision_snake = tmp_sw_vision_snake

        direction = self.game['direction']
        tail_direction = self.game['direction']
        if len(self.game['snake']) > 2:
            if self.game['snake'][2][0] < self.game['snake'][1][0]:
                tail_direction = 'Left'
            elif self.game['snake'][2][0] > self.game['snake'][1][0]:
                tail_direction = 'Right'
            elif self.game['snake'][2][1] < self.game['snake'][1][1]:
                tail_direction = 'Up'
            elif self.game['snake'][2][1]> self.game['snake'][1][1]:
                tail_direction = 'Down'

        tmp_state = np.zeros((32, 1))

        tmp_state[0] = n_vision_wall / self.invalid_distance
        tmp_state[1] = n_vision_apple / self.invalid_distance
        tmp_state[2] = n_vision_snake / self.invalid_distance
        tmp_state[3] = ne_vision_wall / self.invalid_distance
        tmp_state[4] = ne_vision_apple / self.invalid_distance
        tmp_state[5] = ne_vision_snake / self.invalid_distance
        tmp_state[6] = e_vision_wall / self.invalid_distance
        tmp_state[7] = e_vision_apple / self.invalid_distance
        tmp_state[8] = e_vision_snake / self.invalid_distance
        tmp_state[9] = se_vision_wall / self.invalid_distance
        tmp_state[10] = se_vision_apple / self.invalid_distance
        tmp_state[11] = se_vision_snake / self.invalid_distance
        tmp_state[12] = s_vision_wall / self.invalid_distance
        tmp_state[13] = s_vision_apple / self.invalid_distance
        tmp_state[14] = s_vision_snake / self.invalid_distance
        tmp_state[15] = sw_vision_wall / self.invalid_distance
        tmp_state[16] = sw_vision_apple / self.invalid_distance
        tmp_state[17] = sw_vision_snake / self.invalid_distance
        tmp_state[18] = w_vision_wall / self.invalid_distance
        tmp_state[19] = w_vision_apple / self.invalid_distance
        tmp_state[20] = w_vision_snake / self.invalid_distance
        tmp_state[21] = nw_vision_wall / self.invalid_distance
        tmp_state[22] = nw_vision_apple / self.invalid_distance
        tmp_state[23] = nw_vision_snake / self.invalid_distance

        if direction == "Up":
            tmp_state[24] = 1
            tmp_state[25] = 0
            tmp_state[26] = 0
            tmp_state[27] = 0
        elif direction == "Right":
            tmp_state[24] = 0
            tmp_state[25] = 1
            tmp_state[26] = 0
            tmp_state[27] = 0
        elif direction == "Down":
            tmp_state[24] = 0
            tmp_state[25] = 0
            tmp_state[26] = 1
            tmp_state[27] = 0
        elif direction == "Left":
            tmp_state[24] = 0
            tmp_state[25] = 0
            tmp_state[26] = 0
            tmp_state[27] = 1

        if tail_direction == "Up":
            tmp_state[28] = 1
            tmp_state[29] = 0
            tmp_state[30] = 0
            tmp_state[31] = 0
        elif tail_direction == "Right":
            tmp_state[28] = 0
            tmp_state[29] = 1
            tmp_state[30] = 0
            tmp_state[31] = 0
        elif tail_direction == "Down":
            tmp_state[28] = 0
            tmp_state[29] = 0
            tmp_state[30] = 1
            tmp_state[31] = 0
        elif tail_direction == "Left":
            tmp_state[28] = 0
            tmp_state[29] = 0
            tmp_state[30] = 0
            tmp_state[31] = 1

        tmp_state = np.expand_dims(tmp_state, axis=0)
        return tmp_state

    def Algorithm(self):
        self.state = self.get_state()
        self.action = self.snake_ai.act(self.state)
        key = self.get_key(self.action)
        prev_direction = self.game['moves'][-1] if self.game['moves'] else self.game['direction']
        if key in self.VALID_DIRECTIONS[prev_direction]:
            self.game['moves'].append(key)

        self.handle_next_movement()
        self.render()
        if self.run_type == "trainTheAI":
            self.next_state = self.get_state()
            self.snake_ai.remember(self.state, self.action, self.reward, self.next_state, self.done)
            self.episode_reward += self.reward
            self.snake_ai.replay()

    def main(self):
        self.setup_game()
        if self.run_type == "trainTheAI":
            self.snake_ai = AI(self.ai_input_shape, self.game_data['generation'], self.game_data['epsilon'])
        elif self.run_type == "playAsAI":
            self.snake_ai = AI(self.ai_input_shape, self.game_data['generation'], 0)

        self.tick()
        self.window.bind('<Key>', self.on_press)
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
