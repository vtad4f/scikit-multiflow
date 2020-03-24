import numpy as np
import pandas as pd


class FastBuffer(object):
    """ FastBuffer

    A simple buffer used to keep track of a limited number of unitary entries. It
    updates the buffer following a FIFO method, meaning that when the buffer is
    full and a new entry arrives, the oldest entry is pushed out of the queue.

    In theory it keeps track of simple, primitive objects, such as numeric values,
    but in practice it can be used to store any kind of object.

    For this framework the FastBuffer is mainly used to keep track of true labels
    and predictions in a classification task context, so that we can keep updated
    statistics about the task being executed.

    Parameters
    ----------
    max_size: int
        Maximum size of the queue.

    object_list: list
        An initial list. Optional. If given the queue will be started with the
        values from this list.

    Examples
    --------
    >>> # In the following example we keep track of the last 1000 predictions
    >>> # and true labels
    >>> from skmultiflow.utils.data_structures import FastBuffer
    >>> from skmultiflow.lazy import KNNClassifier
    >>> from skmultiflow.data import FileStream
    >>> file_stream = FileStream("skmultiflow/data/datasets/covtype.csv")
    >>> clf = KNNClassifier(n_neighbors=8, max_window_size=2000, leaf_size=40)
    >>> # Initially we need to partial_fit at least n_neighbors=8 samples
    >>> X, y = file_stream.next_sample(8)
    >>> clf = clf.partial_fit(X, y, classes=file_stream.target_values)
    >>> predictions_buffer = FastBuffer(1000)
    >>> true_labels_buffer = FastBuffer(1000)
    >>> for i in range(2000):
    ...     X, y = file_stream.next_sample()
    ...     true_label_popped = true_labels_buffer.add_element(y)
    ...     prediction_popped = predictions_buffer.add_element(clf.predict(X))
    ...     clf = clf.partial_fit(X, y)

    """

    def __init__(self, max_size, object_list=None):
        super().__init__()
        # Default values
        self.current_size = 0
        self.max_size = None
        self.buffer = []

        self.configure(max_size, object_list)

    def configure(self, max_size, object_list):
        self.max_size = max_size
        if isinstance(object_list, list):
            self.add_element(object_list)

    def add_element(self, element_list):
        """ add_element

        Adds a new entry to the buffer. In case there are more elements in the
        element_list parameter than there is free space in the queue, elements
        from the queue are iteratively popped from the queue and appended to
        a list, which in the end is returned.

        Parameters
        ----------
        element_list: list, numpy.ndarray
            A list with all the elements that are to be added to the queue.

        Returns
        -------
        list
            If no elements need to be popped from the queue to make space for new
            entries there is no return. On the other hand, if elements need to be
            removed, they are added to an auxiliary list, and that list is returned.

        """
        if (self.current_size + len(element_list)) <= self.max_size:
            for i in range(len(element_list)):
                self.buffer.append(element_list[i])
            self.current_size += len(element_list)
            return None

        else:
            aux = []
            for element in element_list:
                if self.is_full():
                    aux.append(self.get_next_element())
                self.buffer.append(element)
                self.current_size += 1
            return aux

    def get_next_element(self):
        """ get_next_element

        Pop the head of the queue.

        Returns
        -------
        int or float
            The first element in the queue.

        """
        result = None
        if len(self.buffer) > 0:
            result = self.buffer.pop(0)
            self.current_size -= 1
        return result

    def clear_queue(self):
        self._clear_all()

    def _clear_all(self):
        del self.buffer[:]
        self.buffer = []
        self.current_size = 0
        self.configure(self.max_size, None)

    def print_queue(self):
        print(self.buffer)

    def is_full(self):
        return self.current_size == self.max_size

    def is_empty(self):
        return self.current_size == 0

    def get_current_size(self):
        return self.current_size

    def peek(self):
        """ peek

        Peek the head of the queue, without removing or altering it.

        Returns
        -------
        int or float
            The head of the queue.

        """
        try:
            return self.buffer[0]
        except IndexError:
            return None

    def get_queue(self):
        return self.buffer

    def get_info(self):
        return 'FastBuffer: max_size: ' + str(self.max_size) + ' - current_size: ' + str(self.current_size)


class FastComplexBuffer(object):
    """ FastComplexBuffer

    A complex buffer used to keep track of a limited number of complex entries. It
    updates the buffer following a FIFO method, meaning that when the buffer is
    full and a new entry arrives, the oldest entry is pushed out of the queue.

    We use the term complex entry to specify that each entry is a set of n
    predictions, one for each classification task. This structure is used to keep
    updated statistics from a multi output context.

    Parameters
    ----------
    max_size: int
        Maximum size of the queue.

    width: int
        The width from a complex entry, in other words how many classification
        tasks are there to keep track of.

    Examples
    --------
    It works similarly to the FastBuffer structure, except that it keeps track
    of more than one value per entry. For a complete example, please see
    skmultiflow.evaluation.measure_collection.WindowMultiTargetClassificationMeasurements'
    implementation, where the FastComplexBuffer is used to keep track of the
    MultiOutputLearner's statistics.

    """

    def __init__(self, max_size, width):
        super().__init__()
        # Default values
        self.current_size = 0
        self.max_size = None
        self.width = None
        self.buffer = []

        self.configure(max_size, width)

    def configure(self, max_size, width):
        self.max_size = max_size
        self.width = width

    def add_element(self, element_list):
        """ add_element

        Adds a new entry to the buffer. In case there are more elements in the
        element_list parameter than there is free space in the queue, elements
        from the queue are iteratively popped from the queue and appended to
        a list, which in the end is returned.

        Parameters
        ----------
        element_list: list or numpy.array
            A list with all the elements that are to be added to the queue.

        Returns
        -------
        list
            If no elements need to be popped from the queue to make space for new
            entries there is no return. On the other hand, if elements need to be
            removed, they are added to an auxiliary list, and that list is returned.

        """
        is_list = True
        dim = 1
        if hasattr(element_list, 'ndim'):
            dim = element_list.ndim
        if (dim > 1) or hasattr(element_list[0], 'append'):
            size, width = 0, 0
            if hasattr(element_list, 'append'):
                size, width = len(element_list), len(element_list[0])
            elif hasattr(element_list, 'shape'):
                is_list = False
                size, width = element_list.shape
            self.width = width
            if width != self.width:
                return None
        else:
            size, width = 0, 0
            if hasattr(element_list, 'append'):
                size, width = 1, len(element_list)
            elif hasattr(element_list, 'size'):
                is_list = False
                size, width = 1, element_list.size
            self.width = width
            if width != self.width:
                return None

        if not is_list:
            if size == 1:
                items = [element_list.tolist()]
            else:
                items = element_list.tolist()
        else:
            if size == 1:
                items = [element_list]
            else:
                items = element_list

        if (self.current_size + size) <= self.max_size:
            for i in range(size):
                self.buffer.append(items[i])
            self.current_size += size
            return None
        else:
            aux = []
            for element in items:
                if self.is_full():
                    aux.append(self.get_next_element())
                self.buffer.append(element)
                self.current_size += 1
            return aux

    def get_next_element(self):
        """ get_next_element

        Pop the head of the queue.

        Returns
        -------
        tuple
            The first element of the queue.

        """
        result = None
        if len(self.buffer) > 0:
            result = self.buffer.pop(0)
            self.current_size -= 1
        return result

    def clear_queue(self):
        self._clear_all()

    def _clear_all(self):
        del self.buffer[:]
        self.buffer = []
        self.current_size = 0
        self.configure(self.max_size, None)

    def print_queue(self):
        print(self.buffer)

    def is_full(self):
        return self.current_size == self.max_size

    def is_empty(self):
        return self.current_size == 0

    def get_current_size(self):
        return self.current_size

    def peek(self):
        """ peek

        Peek the head of the queue, without removing or altering it.

        Returns
        -------
        tuple
            The head of the queue.

        """
        try:
            return self.buffer[0]
        except IndexError:
            return None

    def get_queue(self):
        return self.buffer

    def get_info(self):
        return 'FastBuffer: max_size: ' + str(self.max_size) \
               + ' - current_size: ' + str(self.current_size) \
               + ' - width: ' + str(self.width)


class ConfusionMatrix(object):
    """ ConfusionMatrix

    This structure constitutes a confusion matrix, or an error matrix. It is
    represented by a matrix of shape (n_labels, n_labels), in a simple, one
    classification task context.

    One of the matrices dimension is associated with the true labels, while
    the other is associated with the predictions. If we consider the columns
    to represent predictions and the rows to represent true labels. An entry
    in position [1, 2] means that the true label was 1, while the prediction
    was label 2, thus this was a bad prediction. Important: indices in the
    confusion matrix depend on the arrival order of observed classes.

    This structure is used to keep updated statistics from a classifier's
    performance, which allows to compute different evaluation metrics.

    Parameters
    ----------
    n_targets: int
        The number of targets from the single classification task associated
        with this confusion matrix.

    dtype: data type
        A data type supported by numpy.ndarrays, which can correctly represent
        the entries to the matrix. In most cases this will be ints, which are
        the default option.

    """

    def __init__(self, n_targets=None, dtype=np.int64):
        super().__init__()
        if n_targets is not None:
            self.n_targets = n_targets
        else:
            self.n_targets = 0
        self.sample_count = 0
        self.dtype = dtype

        self.confusion_matrix = np.zeros((self.n_targets, self.n_targets), dtype=dtype)

    def restart(self, n_targets):
        if n_targets is None:
            self.n_targets = 0
        else:
            self.n_targets = n_targets
        self.confusion_matrix = np.zeros((self.n_targets, self.n_targets))
        self.sample_count = 0
        pass

    def _update(self, i, j, weight=1.0):
        self.confusion_matrix[i, j] += weight
        self.sample_count += 1
        return True

    def update(self, i=None, j=None, weight=1.0):
        """ update

        Increases by one the count of occurrences in one of the ConfusionMatrix's
        cells.

        Parameters
        ---------
        i: int
            The index of the row to be updated.

        j: int
            The index of the column to be updated.

        weight: float
            Sample's weight

        Returns
        -------
        bool
            True if the update was successful and False if it was unsuccessful,
            case in which a index is out of range.

        Notes
        -----
        No IndexError or IndexOutOfRange errors raised.

        """
        if i is None or j is None:
            return False
        else:
            m, n = self.confusion_matrix.shape
            if (0 <= i < m) and (0 <= j < n):
                return self._update(i, j, weight)
            else:
                new_size = np.max(i, j) + 1
                if new_size <= m:
                    return False
                else:
                    self.reshape(new_size, new_size)
                    return self._update(i, j, weight)

    def remove(self, i=None, j=None):
        """ remove

        Decreases by one the count of occurrences in one of the ConfusionMatrix's
        cells.

        Parameters
        ----------
        i: int
            The index of the row to be updated.

        j: int
            The index of the column to be updated.

        Returns
        -------
        bool
            True if the removal was successful and False otherwise.

        Notes
        -----
        No IndexError or IndexOutOfRange errors raised.

        """
        if i is None or j is None:
            return False

        m, n = self.confusion_matrix.shape
        if (i <= m) and (i >= 0) and (j <= n) and (j >= 0):
            return self._remove(i, j)

        else:
            return False

    def _remove(self, i, j):
        self.confusion_matrix[i, j] = self.confusion_matrix[i, j] - 1
        self.sample_count -= 1
        return True

    def reshape(self, m, n):
        i, j = self.confusion_matrix.shape

        if (m != n) or (m < i) or (n < j):
            return False
        aux = self.confusion_matrix.copy()
        self.confusion_matrix = np.zeros((m, n), self.dtype)

        for p in range(i):
            for q in range(j):
                self.confusion_matrix[p, q] = aux[p, q]

        return True

    def shape(self):
        """ shape

        Returns
        -------
        tuple
            The confusion matrix's shape.

        """
        return self.confusion_matrix.shape

    def value_at(self, i, j):
        """ value_at

        Parameters
        ----------
        i: int
            An index from one of the matrix's rows.

        j: int
            An index from one of the matrix's columns.

        Returns
        -------
        int
            The current occurrence count at position [i, j].

        """
        return self.confusion_matrix[i, j]

    def row(self, r):
        """ row

        Parameters
        ----------
        r: int
            An index from one of the matrix' rows.

        Returns
        -------
        numpy.array
            The complete row indexed by r.

        """
        return self.confusion_matrix[r: r + 1, :]

    def column(self, c):
        """ column

        Parameters
        ----------
        c: int
            An index from one of the matrix' columns.

        Returns
        -------
        numpy.array
            The complete column indexed by c.

        """
        return self.confusion_matrix[:, c: c + 1]

    def get_sum_main_diagonal(self):
        """ Computes the sum of occurrences in the main diagonal.

        Returns
        -------
        int
            The occurrence count in the main diagonal.

        """
        m, n = self.confusion_matrix.shape
        sum_main_diagonal = 0
        for i in range(m):
            sum_main_diagonal += self.confusion_matrix[i, i]
        return sum_main_diagonal

    @property
    def matrix(self):
        if self.confusion_matrix is not None:
            return self.confusion_matrix
        else:
            return None

    @property
    def _sample_count(self):
        return self.sample_count

    def get_info(self):
        return 'ConfusionMatrix: n_targets: ' + str(self.n_targets) + \
               ' - sample_count: ' + str(self.sample_count) + \
               ' - dtype: ' + str(self.dtype)


class MOLConfusionMatrix(object):
    """ MOLConfusionMatrix

    This structure constitutes a confusion matrix, or an error matrix. It is
    represented by a matrix of shape (n_targets, n_labels, n_labels). It
    basically works as an individual ConfusionMatrix for each of the
    classification tasks in a multi label environment. Thus, n_labels is
    always 2 (binary).

    The first dimension defines which classification task it keeps track of.
    The second dimension is associated with the true labels, while the other
    is associated with the predictions. For example, an entry in position
    [2, 1, 2] represents a miss classification in the classification task of
    index 2, where the true label was index 1, but the prediction was index 2.

    This structure is used to keep updated statistics from a multi output
    classifier's performance, which allows to compute different evaluation
    metrics.

    Parameters
    ----------
    n_targets: int
        The number of classification tasks.

    dtype: data type
        A data type supported by numpy.ndarrays, which can correctly represent
        the entries to the matrix. In most cases this will be ints, which are
        the default option.

    Notes
    -----
    This structure starts with n_targets classification tasks. As the entries
    arrive, if new labels are identified, the matrix may reshape itself to
    accommodate all labels.

    """

    def __init__(self, n_targets=None, dtype=np.int64):
        super().__init__()
        if n_targets is not None:
            self.n_targets = n_targets
        else:
            self.n_targets = 0
        self.dtype = dtype

        self.confusion_matrix = np.zeros((self.n_targets, 2, 2), dtype=dtype)

    def restart(self, n_targets):
        if n_targets is None:
            self.n_targets = 0
        else:
            self.n_targets = n_targets
        self.confusion_matrix = np.zeros((self.n_targets, 2, 2), dtype=self.dtype)
        pass

    def _update(self, target, true, pred, weight=1.0):
        self.confusion_matrix[int(target), int(true), int(pred)] += weight
        return True

    def update(self, target=None, true=None, pred=None, weight=1.0):
        """ update

        Increases by one the occurrence count in one of the matrix's positions.
        As entries arrive, it may reshape the matrix to correctly accommodate all
        possible labels.

        The count will be increased in the matrix's [target, true, pred] position.

        Parameters
        ----------
        target: int
            A classification task's index.

        true: int
            A true label's index.

        weight: float
            Sample's weight

        pred: int
            A prediction's index


        Returns
        -------
        bool
            True if the update was successful, False otherwise.

        """
        if target is None or true is None or pred is None:
            return False
        else:
            m, n, p = self.confusion_matrix.shape
            if (target < m) and (target >= 0) and (true < n) and (true >= 0) and (pred < p) and (pred >= 0):
                return self._update(target, true, pred, weight)
            else:
                if (true > 1) or (true < 0) or (pred > 1) or (pred < 0):
                    return False
                if target > m:
                    return False
                else:
                    self.reshape(target + 1, 2, 2)
                    return self._update(target, true, pred, weight)

    def remove(self, target=None, true=None, pred=None):
        """ remove

        Decreases by one the occurrence count in one of the matrix's positions.

        The count will be increased in the matrix's [target, true, pred] position.

        Parameters
        ----------
        target: int
            A classification task's index.

        true: int
            A true label's index.

        pred: int
            A prediction's index

        Returns
        -------
        bool
            True if the removal was successful, False otherwise.

        """
        if true is None or pred is None or target is None:
            return False
        m, n, p = self.confusion_matrix.shape
        if (target <= m) and (target >= 0) and (true <= n) and (true >= 0) and (pred >= 0) and (pred <= p):
            return self._remove(target, true, pred)
        else:
            return False

    def _remove(self, target, true, pred):
        self.confusion_matrix[target, true, pred] = self.confusion_matrix[target, true, pred] - 1
        return True

    def reshape(self, target, m, n):
        t, i, j = self.confusion_matrix.shape
        if (target > t + 1) or (m != n) or (m != 2) or (m < i) or (n < j):
            return False
        aux = self.confusion_matrix.copy()
        self.confusion_matrix = np.zeros((target, m, n), self.dtype)
        for w in range(t):
            for p in range(i):
                for q in range(j):
                    self.confusion_matrix[w, p, q] = aux[w, p, q]
        return True

    def shape(self):
        return self.confusion_matrix.shape

    def value_at(self, target, i, j):
        """ value_at

        Parameters
        ----------
        target: int
            An index from one of classification's tasks.

        i: int
            An index from one of the matrix's rows.

        j: int
            An index from one of the matrix's columns.

        Returns
        -------
        int
            The current occurrence count at position [target, i, j].

        """
        return self.confusion_matrix[target, i, j]

    def row(self, r):
        """ row

        Parameters
        ----------
        r: int
            An index from one of the matrix' rows.

        Returns
        -------
        numpy.array
            The complete row indexed by r.

        """
        return self.confusion_matrix[r:r + 1, :]

    def column(self, c):
        """ column

        Parameters
        ----------
        c: int
            An index from one of the matrix' columns.

        Returns
        -------
        numpy.array
            The complete column indexed by c.

        """
        return self.confusion_matrix[:, c:c + 1]

    def target(self, t):
        """ target

        Parameters
        ----------
        t: int
            An index from one of the matrix' target.

        Returns
        -------
        numpy.ndarray
            The complete target indexed by t.

        """
        return self.confusion_matrix[t, :, :]

    def get_sum_main_diagonal(self):
        """ get_sum_main_diagonal

        Computes the sum of occurrences in all the main diagonals.

        Returns
        -------
        int
            The occurrence count in the main diagonals.

        """
        t, m, n = self.confusion_matrix.shape
        sum_main_diagonal = 0
        for i in range(t):
            sum_main_diagonal += self.confusion_matrix[i, 0, 0]
            sum_main_diagonal += self.confusion_matrix[i, 1, 1]
        return sum_main_diagonal

    def get_total_sum(self):
        """ get_total_sum

        Returns
        ------
        int
            The sum of occurrences in the matrix.

        """
        return np.sum(self.confusion_matrix)

    def get_total_discordance(self):
        """ get_total_discordance

        The total discordance is defined as all the occurrences where a miss
        classification was detected. In other words it's the sum of all cells
        indexed by [t, i, j] where i and j are different.

        Returns
        -------
        float
            The total discordance from all target's matrices.

        """
        return self.get_total_sum() - self.get_sum_main_diagonal()

    @property
    def matrix(self):
        if self.confusion_matrix is not None:
            return self.confusion_matrix
        else:
            return None

    def get_info(self):
        return 'MOLConfusionMatrix: n_targets: ' + str(self.n_targets) + \
               ' - total_sum: ' + str(self.get_total_sum()) + \
               ' - total_discordance: ' + str(self.get_total_discordance()) + \
               ' - dtype: ' + str(self.dtype)


class InstanceWindow(object):
    """ InstanceWindow

    Keeps a limited size window from the most recent instances seen.
    It updates its recorded instances by the FIFO method, which means
    that when size limit is reached, old instances are dumped to give
    place to new instances.

    Parameters
    ----------
    n_features: int
        The total number of features to be expected.

    n_targets: int
        The total number of target tasks to be expected.

    categorical_list: list
        A list with the indexes from all the categorical attributes.

    max_size: int
        The window's maximum length.

    dtype: data type
        A data type supported by numpy, by default it is a float.

    Raises
    ------
    ValueError: If at any moment, an instance with a different number of
    attributes than that of the n_attributes parameter is passed, a ValueError
    is raised.

    TypeError: If the buffer type is altered by the user, or isn't correctly
    initialized, a TypeError may be raised.

    """

    def __init__(self, n_features=0, n_targets=1, categorical_list=None, max_size=1000, dtype=float):
        super().__init__()
        # default values
        self._buffer = None
        self._n_samples = None
        self._n_attributes = n_features
        self.categorical_attributes = categorical_list
        self.max_size = max_size
        self.dtype = dtype
        self._n_target_tasks = n_targets
        self.configure()

    def configure(self):
        self._buffer = np.zeros((0, self._n_attributes + self._n_target_tasks))
        self._n_samples = 0

    def add_element(self, X, y):
        """ add_element

        Adds a sample to the instance window.

        X: numpy.ndarray of shape (1, 1)
            Feature matrix of a single sample.

        y: numpy.ndarray of shape (1, 1)
            Labels matrix of a single sample.

        Raises
        ------
        ValueError: If at any moment, an instance with a different number of
        attributes than that of the n_attributes parameter is passed, a ValueError
        is raised.

        TypeError: If the buffer type is altered by the user, or isn't correctly
        initialized, a TypeError may be raised.

        """
        if self._n_attributes != X.size:
            if self._n_samples == 0:
                self._n_attributes = X.size
                self._n_target_tasks = y.size
                self._buffer = np.zeros((0, self._n_attributes + self._n_target_tasks))
            else:
                raise ValueError("Number of attributes in X is different from the objects buffer dimension. "
                                 "Call __configure() to correctly set up the InstanceWindow")

        if self._n_samples >= self.max_size:
            self._n_samples -= 1
            self._buffer = np.delete(self._buffer, 0, axis=0)

        if self._buffer is None:
            raise TypeError("None type not supported as the buffer, call configure() to set up the InstanceWindow")

        aux = np.concatenate((X, y), axis=1)
        self._buffer = np.concatenate((self._buffer, aux), axis=0)
        self._n_samples += 1

    def delete_element(self):
        """ delete_element

        Delete the oldest element from the sample window.

        """
        self._n_samples -= 1
        self._buffer = self._buffer[1:, :]

    def get_attributes_matrix(self):
        return self._buffer[:, :self._n_attributes]

    def get_targets_matrix(self):
        return self._buffer[:, self._n_attributes:]

    def at_index(self, index):
        """ at_index

        Returns the complete sample and index = index.

        Parameters
        ----------
        index: int
            An index from the InstanceWindow buffer.

        Returns
        -------
        tuple
            A tuple containing both the attributes and the targets from sample
            indexed of index.

        """
        return self.get_attributes_matrix()[index], self.get_targets_matrix()[index]

    def reset(self):
        self.configure()

    @property
    def buffer(self):
        return self._buffer

    @property
    def n_targets(self):
        return self._n_target_tasks

    @property
    def n_attributes(self):
        return self._n_attributes

    @property
    def n_samples(self):
        return self._n_samples

    def get_info(self):
        return 'InstanceWindow: n_attributes: ' + str(self.n_attributes) + \
               ' - n_target_tasks: ' + str(self.n_targets) + \
               ' - n_samples: ' + str(self.n_samples) + \
               ' - max_size: ' + str(self.max_size) + \
               ' - dtype: ' + str(self.dtype)


class TimeManager(object):
    """ TimeManager

    Manage instances that are related to a timestamp and
    a delay.

    Parameters
    ----------
    timestamp: np.datetime64
        Current timestamp of the stream. This timestamp is always
        updated as the stream is processed to simulate when
        the labels will be available for each sample.

    """

    _columns = ["X", "y_real", "y_pred", "arrival_time", "available_time"]

    def __init__(self, timestamp):
        # get initial timestamp
        self.timestamp = timestamp
        # create dataframe to save time data
        # X = features
        # y_real = real label
        # y_pred = predicted label for each model being evaluated
        # arrival_time = arrival timestamp of the sample
        # available_time = timestamp when the sample label will be available
        self.queue = pd.DataFrame(columns=self._columns)
        # transform queue into datetime if timestamps are not int
        if isinstance(self.timestamp, int):
            self.queue['arrival_time'] = pd.to_datetime(self.queue['arrival_time'])
            self.queue['available_time'] = pd.to_datetime(self.queue['available_time'])

    def _sort_queue(self):
        # sort values by available_time
        self.queue = self.queue.sort_values(by='available_time', ignore_index=True)

    def _cleanup_samples(self, batch_size):
        # check if has batch_size samples to be removed
        if self.queue.shape[0] - batch_size >= 0:
            # drop samples that were already used
            self.queue = self.queue.drop(self.queue.index[[np.arange(batch_size)]])
        else:
            # drop all samples
            self.queue = self.queue.iloc[0:0]

    def update_timestamp(self, timestamp):
        """ update_timestamp

        Update current timestamp of the stream.

        Parameters
        ----------
        timestamp: datetime64
            Current timestamp of the stream. This timestamp is always
            updated as the stream is processed to simulate when
            the labels will be available for each sample.

        """

        self.timestamp = timestamp

    def get_available_samples(self):
        """ get_available_samples

        Get available samples of the stream, i.e., samples that have
        their labels available (available_time <= timestamp).

        Returns
        -------
        tuple
            A tuple containing the data, their real labels and predictions.

        """

        # get samples that have label available
        samples = self.queue[self.queue['available_time'] <= self.timestamp]
        # remove these samples from queue
        self.queue = self.queue[self.queue['available_time'] > self.timestamp]
        # return X, y_real and y_pred for the unqueued samples
        return samples["X"], samples["y_real"], samples["y_pred"]

    def update_queue(self, X, arrival_time, available_time, y_real, y_pred):
        # cretae daraframe for current samples
        frame = pd.DataFrame(list(zip(X, y_real, y_pred, arrival_time, available_time)),
                             columns=self._columns)
        # append new data to queue
        self.queue = self.queue.append(frame)
        # sort queue
        self._sort_queue()

    def has_more_samples(self):
        """ Checks if queue has more samples.

        Returns
        -------
        Boolean
            True if queue has more samples.

        """

        return self.queue.shape[0] > 0

    def next_sample(self, batch_size=1):
        """ Returns next sample from the queue.

        If there is enough instances to supply at least batch_size samples, those
        are returned. Otherwise, the remaining are returned.

        Parameters
        ----------
        batch_size: int (optional, default=1)
            The number of instances to return.

        Returns
        -------
        tuple or tuple list
            Returns the next batch_size instances.
            For general purposes the return can be treated as a numpy.ndarray.

        """

        if self.queue.shape[0] - batch_size >= 0:
            samples = self.queue[:batch_size]
        else:
            samples = self.queue
        # get X
        X = samples["X"]
        # get y_real
        y_real = samples["y_real"]
        # get y_pred
        y_pred = samples["y_pred"]
        # remove samples from queue
        self._cleanup_samples(batch_size)
        # return X, y_real and y_pred for the unqueued samples
        return X, y_real, y_pred
