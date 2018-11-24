import numpy as np
from Data import *
from time import time
from helpers import sigmoid, mse, normalize

class NeuralNetwork:
  def __init__(self, data_directory='../data_samples', final_testing=False):
    if final_testing:
      self.train_ = Data(data_directory=data_directory, is_test_data=False)
      self.test_ = Data(data_directory=data_directory, is_test_data=True)
    else:
      self.train_, self.test_ = Data.train_and_pseudo_test()

    print('Data loaded.')

    # self.train_labels = [expected(label) for label in self.train.labels()]
    self.train_labels = self.train_.labels()
    self.train_images = self.train_.images()

    # self.test_labels = [expected(label) for label in self.test.labels()]
    self.test_labels = self.test_.labels()
    self.test_images = self.test_.images()

    # Hyperparameters
    self.input_size = 28*28
    self.hidden_size = 20
    self.output_size = 62
    self.num_hidden_layers = 2
    self.learning_rate = 0.001
    self.batch_size = 500
    self.epochs = 1

    # self.hidden_activation = sigmoid
    # self.final_activation = softmax
    self.activation = sigmoid

    self._create_weights_and_biases()

    print('Neural network created.')

  def _create_weights_and_biases(self):
    '''
    Create weight matrices and bias vectors for layer-to-layer transition.
    '''
    self.weight_matrices = []
    self.bias_vectors = []
    lengths = self.layer_lengths()
    for n in range(len(lengths) - 1):
      self.weight_matrices.append(np.random.rand(lengths[n+1], lengths[n]))
      self.bias_vectors.append(np.random.rand(lengths[n+1]))
    print('Weight matrices and bias vectors initialized.')

  def layer_lengths(self):
    '''
    Return the length of each of the layers of the NN in the form of a list.
    [input layer, {...hidden layers...} , output layer]
    '''
    shapes = [self.input_size]
    for i in range(self.num_hidden_layers):
      shapes.append(self.hidden_size)
    shapes.append(self.output_size)
    return shapes

  def feed_forward(self, x):
    '''
    Give output of neural network with current weights and biases if input is
    vector (np.array) x. len(x) = self.input_size.

    Output is np.array with size self.output_size, and has been pushed through
    self.activation.
    '''
    last = len(self.weight_matrices) - 1
    y = normalize(np.copy(x))
    for i, (W, b) in enumerate(zip(self.weight_matrices, self.bias_vectors)):
      z = np.dot(W, y) + b
      y = self.activation(z)
      # if i == last:
      #   y = self.final_activation(z)
      # else:
      #   y = self.hidden_activation(z)
    return y

  def train(self):
    '''
    Perform all the training batches, and make a graph or something.
    '''
    for iteration in range(np.ceil(len(self.train_labels) / self.batch_size)):
      self.train_batch(iteration)
      if iteration % 100 == 0:
        # Add a point on a graph or something. This is after 50000 (100*500)
        # training examples!
        pass
    # Do the graphing (or something) thing here, after all the batches, as well

  def train_batch(self, batch_number):
    '''
    Perform a forward-propagation pass, training some stuff
    '''
    n = self.batch_size
    k = self.learning_rate
    first_ind = n * batch_number
    last_ind = n * (batch_number + 1)
    dE_dW = [np.zeros(W.shape) for W in self.weight_matrices]
    dE_dB = [np.zeros(b.shape) for b in self.bias_vectors]
    for i in range(first_ind, last_ind):
      if i >= len(self.train_labels):
        # Don't want an exception to be raised when training the last batch!
        break
      else: # In the clear
        input_image  = self.train_images[i]
        target_label = self.train_labels[i]
        _dW, _dB = self.backpropagation(input_image, target_label)
        dE_dW = [dW + dW_ for dW, dW_ in zip(dE_dW, _dW)]
        dE_dB = [dB + dB_ for dB, dB_ in zip(dE_dB, _dB)]

    # k is learning rate, n is for averaging
    self.weight_matrices = [W - (k * dW / n) for W, dW in
                            zip(self.weight_matrices, dE_dW)]
    self.bias_vectors = [b - (k * dB / n) for b, dB in
                         zip(self.bias_vectors, dE_dB)]
    # print('haha we are training, trust me comrade')

  def backpropagation(self, input_image, target_label):
    '''
    Compute gradients for weight matrices and bias vectors based on one
    training example.

    Return gradient of error function with respect to each weight matrix and
    bias vector, as a 2-tuple where the first value is a list of grad values
    for each weight matrix and the second value is a list of grad values for
    each bias vector.

    NOTE: Scale final dW and dB values by -self.learning_rate
    '''
    n = 1 + self.num_hidden_layers + 1 # input + num_hidden + output
    dW = [np.zeros(W.shape) for W in self.weight_matrices]
    dB = [np.zeros(b.shape) for b in self.bias_vectors]
    a = input_image
    a_vals = [a] # Store neuron activation values
    z_vals = [] # Store neuron values before passing thru activation function
    # This does nearly the same thing as self.feed_forward, but it stores the
    # a- and z-values in lists
    for i, (W, b) in enumerate(zip(self.weight_matrices, self.bias_vectors)):
      z_i = np.dot(W, a) + b
      z_vals.append(z_i)
      a = self.activation(z_i)
      a_vals.append(a)

    # dE_da = cross_entropy(a_vals[-1], target_label, derivative=True)
    dE_da = mse(a_vals[-1], target_label, derivative=True)
    da_dz = softmax(z_vals[-1], derivative=True)
    dE_dz = dE_da * da_dz
    dW[-1] = np.dot(dE_dz, np.transpose(a_vals[-2]))
    dB[-1] = dE_dz # * 1

    # Recursively & iteratively compute dE/dW and dE/dB
    for i in range(2, n):
      next_ = -i + 1  # Layer that curr_ influences
      prev_ = -i - 1  # Layer that influences curr_
      curr_ = -i      # Current layer

      z = z_vals[curr_]
      dE_dz = np.dot(np.transpose(self.weight_matrices[next_]), dE_dz) * \
          self.activation(z_vals[curr_], derivative=True)
      # dE/dW
      dW[curr_] = np.dot(dE_dz, np.transpose(a_vals[prev_]))
      # dE/dB
      dB[curr_] = dE_dz # * 1

    return (dW, dB)

  def test(self):
    '''
    Test how well the network currently performs on the test data. Return a
    proportion of correct answers to test sample size.
    '''
    print('Testing...')
    correct = 0
    for label, image in zip(self.test_labels, self.test_images):
      if np.argmax(self.feed_forward(image)) == label:
        correct += 1
    return correct/len(self.test_labels)


if __name__ == '__main__':
  t0 = time()

  n = NeuralNetwork()
  print('Correctly guessed', n.test(), 'percent')

  dt = time() - t0
  mins, secs = int(dt // 60), int(dt % 60)
  print('-'*80 +
        '\nCompleted in {:0>2d}:{:0>2d}\n'.format(mins, secs) +
        '-'*80)
