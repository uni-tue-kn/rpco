import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from keras.models import Sequential

from collections import defaultdict

from libs.Evaluator import Evaluator

from traffic_models.Disjoint import Disjoint


class RLAgent:

    def __init__(self, number_of_ports=32, n_clusters=1):
        self.number_of_ports = number_of_ports
        self.n_clusters=n_clusters

        self._preprocessing()

        self.replay_buffer = []

    def _preprocessing(self, samples=[]):
        processedSamples = np.array([])

        for s in samples:
            tmp = np.zeros(self.number_of_ports)

            for port in s:
                tmp[port-1] = 1

            processedSamples = np.append(processedSamples, tmp)

        return processedSamples.reshape((-1, self.number_of_ports))

    def _build_network(self):
        model = Sequential()
        model.add(layers.Input(shape=(None, self.number_of_ports)))
        model.add(layers.LSTM(256))
        model.add(layers.Dense(128, activation="relu"))
        model.add(layers.Dense(self.number_of_ports, activation="sigmoid"))

        model.compile(loss=self.custom_loss_function, optimizer="adam")

        return model

    def _build_labels(self, prediction=None):
        labels = defaultdict(int)

        for index, value in enumerate(prediction):
            for n in range(1, self.n_clusters+1):
                if value <= n/self.n_clusters:
                    labels[index+1] = n - 1

                    break

        return labels

    def custom_loss_function(self, y, y_predict):
        loss = map(lambda x: Evaluator(labels=self._build_labels(prediction=x)).get_recirculations(), y_predict)

        return loss

    def train(self, steps=1000):
        pass






d = Disjoint(number_of_ports=9, group_sizes=[3, 3, 3], name="DisjointModel")
samples = d.sample(n=20)
agent = RLAgent(number_of_ports=9, n_clusters=3)
data = np.array([agent._preprocessing(samples=samples), ])


model = agent._build_network()
model_target = agent._build_network()

model.summary()

#model.fit(data, [])
print(model.predict(data))






