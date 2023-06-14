import json
import datetime as dt
import os


# class for storing result for metrics
class Result:
    def __init__(self, title=None):
        self.__title__ = "Result"
        if title:
            self.__title__ = title
        # Stuff for time tracking
        self.__start__ = None
        # Metrics stored in dict
        self.__metrics__ = dict()
        # Explain results stored in dict
        self.__explain_results__ = dict()
        self.__query__ = dict()


    def startTimer(self):
        self.__start__ = dt.datetime.now()

    def stopTimer(self):
        if self.__start__ is not None:
            delta = dt.datetime.now() - self.__start__
            self.__start__ = None
            return delta
        else:
            print("timer not started")
            return None

    def setMetric(self, name, value):
        self.__metrics__[name] = value

    def printPadded(self, txt, width, fill='='):
        space = ' '
        w = int((width - len(txt) - 2 * len(space)) / 2)
        x = len(txt) % 2  # extra fill char if needed
        print(fill * w + space + txt + space + fill * x + fill * w)

    def printResultHeader(self, title):
        title = self.__title__ if not title else title
        width = 60
        print("=" * width)
        self.printPadded(title, width)
        print("=" * width)

    def printResultFooter(self):
        self.printResultHeader("End Results")

    def printMetrics(self, title=None):
        self.printResultHeader(title)
        for key, value in self.__metrics__.items():
            print("%s: %s" % (key, value))
        self.printResultFooter()

    def setExplainResult(self, query, result):
        self.__explain_results__[query] = result

    def setQuery(self, id, query):
        self.__query__[id] = query

    def saveMetrics(self, results_dir, folder):
        path = os.path.join(results_dir, folder)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        metrics = dict()
        for key, value in self.__metrics__.items():
            metrics[key] = str(value)
        with open(os.path.join(path, self.__title__ + '.json'), 'w') as fp:
            json.dump(metrics, fp, indent=4, sort_keys=True)

    def saveExplainResults(self, results_dir, folder):
        path = os.path.join(results_dir, folder)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        metrics = dict()
        for key, value in self.__explain_results__.items():
            metrics[key] = str(value)
        with open(os.path.join(path, 'Explain.json'), 'w') as fp:
            json.dump(metrics, fp, indent=4, sort_keys=True)
    def saveExplainResults_costOff(self, results_dir, folder):
        path = os.path.join(results_dir, folder)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        metrics = dict()
        for key, value in self.__explain_results__.items():
            metrics[key] = str(value)
        with open(os.path.join(path, 'Explain_costOff.json'), 'w') as fp:
            json.dump(metrics, fp, indent=4, sort_keys=True)

    def saveQuery(self, results_dir, folder):
        path = os.path.join(results_dir, folder)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        metrics = dict()
        for key, value in self.__query__.items():
            metrics[key] = str(value)
        with open(os.path.join(path, 'query_plans.json'), 'w') as fp:
            json.dump(metrics, fp, indent=4, sort_keys=True)
