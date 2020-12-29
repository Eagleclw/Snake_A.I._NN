import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from random import uniform
from math import floor
import random
import json
import numpy as np
import time
from collections import deque
from keras.models import Sequential, load_model, model_from_json
from keras.layers import Dense, Flatten, BatchNormalization
from keras.callbacks import ModelCheckpoint
from keras.optimizers import Adam, RMSprop

class AI:
    def __init__(self, state_size, gen_count, epsilon):
        print("AI Created.")
        print("-----")
        self.state_size = state_size
        self.availableActions = ['Left', 'None', 'Right']
        self.action_size = len(self.availableActions)

        self.gen_count = gen_count
        self.child_count = 0
        self.child_limit = 500
        self.child_rewards = 0
        self.child_current_score = 0
        self.child_best_score = 0
        self.action_limit = 5_000_000

        self.states = []
        self.train_targets = []

        self.gamma = 0.95
        self.learning_rate = 0.001

        self.epsilon = epsilon
        self.epsilon_decay = 0.999
        self.epsilon_min = 0.01

        self.model_checkpoint_callback = ModelCheckpoint(filepath="checkpoint/", save_weights_only=True, monitor='accuracy', mode='max')
        self.model = self.build_model()
        try:
            self.model.load_weights("checkpoint/").expect_partial().assert_consumed()
        except:
            pass

    def on_closing(self):
        del self

    def __del__(self):
        print("-----")
        print("AI Closed.")
        print("---------------")

    def build_model(self):
        model = Sequential()
        model.add(Flatten(input_shape=self.state_size))
        model.add(BatchNormalization())
        model.add(Dense(20, activation="relu"))
        model.add(Dense(12, activation="relu"))
        model.add(Dense(self.action_size, activation="softmax"))
        model.compile(loss="mse", optimizer=Adam(lr=self.learning_rate), metrics=['accuracy'])
        return model

    def remember(self, state, action, reward, next_state, done):
        self.child_rewards += reward
        if reward == 1:
            self.child_current_score += 1
            if self.child_current_score > self.child_best_score:
                self.child_best_score = self.child_current_score

        if done:
            self.child_count += 1

            print("Collecting actions for training... Generation : " + str(self.gen_count)
                  + " | Childs : " + str(self.child_count) + "/" + str(self.child_limit)
                  + " | Actions : " + str(len(self.states) + 1) + "/" + str(self.action_limit)
                  + " | Score : " + str(self.child_current_score)
                  + " | Best Score : " + str(self.child_best_score))

            self.child_current_score = 0
            target = reward
        else:
            target = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
        train_target = self.model.predict(state)
        train_target[0][action] = target

        self.states.append(np.squeeze(state, axis=0))
        self.train_targets.append(np.squeeze(train_target, axis=0))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])

    def replay(self):
        if self.child_count < self.child_limit and len(self.states) < self.action_limit:
            return

        generation_info = {
                            "Generation": self.gen_count,
                            "Childs": self.child_count,
                            "Actions": len(self.states),
                            "BestScore": self.child_best_score,
                            "AverageReward": round(self.child_rewards / self.child_count, 5),
                            "Epsilon": round(self.epsilon, 5)
                        }
        print("")
        print(generation_info)
        print("--------------------------------------------------")
        print("Training with collected actions...\n")
        self.model.fit(np.array(self.states), np.array(self.train_targets), verbose=1, epochs=10, shuffle=True, callbacks=[self.model_checkpoint_callback])
        print("\nTraining completed...")
        print("--------------------------------------------------")
        self.states.clear()
        self.train_targets.clear()
        self.gen_count += 1
        self.child_count = 0
        self.child_rewards = 0
        self.child_best_score = 0
        self.adaptiveEGreedy()

        return generation_info

    def adaptiveEGreedy(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
