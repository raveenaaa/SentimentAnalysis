import findspark
findspark.init()
from pyspark import SparkConf, SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
import operator
import numpy as np
import matplotlib.pyplot as plt
import functools
import logging

def main():

    conf = SparkConf().setMaster("local[2]").setAppName("Streamer")
    sc = SparkContext(conf=conf)
    ssc = StreamingContext(sc, 10)   # Create a streaming context with batch interval of 10 sec
    ssc.checkpoint("checkpoint")

    pwords = load_wordlist("positive.txt")
    nwords = load_wordlist("negative.txt")
   
    counts = stream(ssc, pwords, nwords, 100)
    make_plot(counts)


def make_plot(counts):
    """
    Plot the counts for the positive and negative words for each timestep.
    Use plt.show() so that the plot will popup.
    """

    positives = list(map(lambda x: x[1], list(filter(lambda x: x[0] == 'positive', counts))))
    negatives = list(map(lambda x: x[1], list(filter(lambda x: x[0] == 'negative', counts))))
    plt.plot(positives, c = 'b', linestyle = '-', marker = 'o', label = 'positives')
    plt.plot(negatives, c = 'g', linestyle = '-', marker = 'o', label = 'negatives')
    plt.legend(loc = 'upper left')
    plt.ylabel('Word Count').
    
    plt.xlabel('Time Step')
    plt.show()


def load_wordlist(filename):
    """ 
    This function should return a list or set of words from the given filename.
    """
    file_contents = set(open(filename, "r").read().split())
    return file_contents

def updateFunction(newValues, runningCount):
    if runningCount is None:
        runningCount = 0        
    addition = sum(newValues)
    return (runningCount + addition)

def stream(ssc, pwords, nwords, duration):
    kstream = KafkaUtils.createDirectStream(
        ssc, topics = ['twitterstream'], kafkaParams = {"metadata.broker.list": 'localhost:9092'})
    tweets = kstream.map(lambda x: x[1])  

    # Each element of tweets will be the text of a tweet.
    # You need to find the count of all the positive and negative words in these tweets.
    # Keep track of a running total counts and print this at every time step (use the pprint function).
    # YOUR CODE HERE
    words = tweets.flatMap(lambda x: x.split(" "))
    filtered = words.filter(lambda word: word in pwords or word in nwords)
    pairs = filtered.map(lambda word: ('positive', 1) if word in pwords else ('negative', 1))
    aggregates = pairs.reduceByKey(lambda x,y: x+y)
    runningCounts = aggregates.updateStateByKey(updateFunction)
    runningCounts.pprint()

    # Let the counts variable hold the word counts for all time steps
    # You will need to use the foreachRDD function.
    # For our implementation, counts looked like:
    #   [[("positive", 100), ("negative", 50)], [("positive", 80), ("negative", 60)], ...]
    counts = []
    aggregates.foreachRDD(lambda t, rdd: counts.append(rdd.collect()))
    ssc.start()                         # Start the computation
    ssc.awaitTerminationOrTimeout(duration)
    ssc.stop(stopGraceFully=True)

    return counts


if __name__=="__main__":
    main()
