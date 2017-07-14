import os, json
from libpgm.graphskeleton import GraphSkeleton
from libpgm.pgmlearner import PGMLearner
from libpgm.CPDtypes.discrete import Discrete


def bn_learn(attr, cicli, passed_file):
    path_to_sentiments = 'sentiment_AFINN'
    
    print "Using AFINN sentiment dictionary"

    if attr == 0:
        print "Considering tweets' number"
    elif attr == 1:
        print "Considering averaged number of positive, negative and neutral tweets"
    elif attr == 2:
        print "Considering averaged value of positive and negative tweets"
    elif attr == 3:
        print "Considering positive and negative tweets\' increment"
    elif attr == 4:
        print "Considering bullisment index obtained by number of tweets sentiment"
    elif attr == 5:
        print "Considering bullisment index obtained by tweets value of sentiment"

    print "And considering market trend"

    all_data = []
    files = [path_to_sentiments + "/" + file for file in os.listdir(path_to_sentiments) if file.endswith('.json')]
    for file in files:
        with open(file) as sentiment_file:
            data = json.load(sentiment_file)

            vdata = {}
            if attr == 0:
                vdata["com"] = data["n_tweets"]
            elif attr == 1:
                vdata["pos"] = data["n_pos_ave"]
                vdata["neg"] = data["n_neg_ave"]
                vdata["neu"] = data["n_neu_ave"]
            elif attr == 2:
                vdata["pos"] = data["pos_val_ave"]
                vdata["neg"] = data["neg_val_ave"]
            elif attr == 3:
                vdata["pos"] = data["pos_inc"]
                vdata["neg"] = data["neg_inc"]
            elif attr == 4:
                vdata["com"] = data["bull_ind"]
            elif attr == 5:
                vdata["com"] = data["bull_ind_val"]

            vdata["market"] = data["market_inc"]

            all_data.append(vdata)

    skel = GraphSkeleton()
    if len(all_data[0]) == 2:
        skel.load("network_struct_1_vertex.json")
        print "Loading structure with 2 node"
    elif len(all_data[0]) == 3:
        skel.load("network_struct_2_vertex.json")
        print "Loading structure with 3 node"
    elif len(all_data[0]) == 4:
        skel.load("network_struct_3_vertex.json")
        print "Loading structure with 4 node"
    skel.toporder()

    learner = PGMLearner()
    result = learner.lg_mle_estimateparams(skel, all_data)
    for key in result.Vdata.keys():
        result.Vdata[key]['type'] = 'lg'

    prob_pos = prob_neg = prob_neu = 0
    for data in all_data:
        if data['market'] == 1:
            prob_pos += 1
        elif data['market'] == 0:
            prob_neu += 1
        else:
            prob_neg += 1
    prob_pos = float(prob_pos) / float(len(all_data))
    prob_neg = float(prob_neg) / float(len(all_data))
    prob_neu = float(prob_neu) / float(len(all_data))

    tmp = {}
    tmp['numoutcomes'] = len(all_data)
    tmp['cprob'] = [prob_pos, prob_neg, prob_neu]
    tmp['parents'] = result.Vdata['market']['parents']
    tmp['vals'] = ['positive', 'negative', 'neutral']
    tmp['type'] = 'discrete'
    tmp['children'] = result.Vdata['market']['children']
    result.Vdata['market'] = tmp

    node = Discrete(result.Vdata["market"])
    print "Loading node as Discrete"
    
    estimated, real = mcmc_json(passed_file, attr, cicli, node)

    return estimated, real

def mcmc_json(file, attr, cicli, node):
    with open(file) as passed:
        data = json.load(passed)

    pos = neg = neu = com = 0

    if attr == 0:
        com = data["n_tweets"]
        print "Work on number of tweets"
    elif attr == 1:
        pos = data["n_pos_ave"]
        neg = data["n_neg_ave"]
        neu = data["n_neu_ave"]
        print "Work on averaged number of positive, negative and neutral tweets"
    elif attr == 2:
        pos = data["pos_val_ave"]
        neg = data["neg_val_ave"]
        print "Work on averaged value of positive and negative tweets"
    elif attr == 3:
        pos = data["pos_inc"]
        neg = data["neg_inc"]
        print "Work on increment of positive and negative tweets"
    elif attr == 4:
        com = data["bull_ind"]
        print "Work on bullisment index obtained by number of tweets sentiment"
    elif attr == 5:
        com = data["bull_ind_val"]
        print "Work on bullisment index obtained by tweets value of sentiment"

    market = 0
    for i in range(cicli):
        if attr == 1:
            market += node.choose([pos, neg, neu])
        elif attr == 2 or attr == 3:
            market += node.choose([pos, neg])
        elif attr == 0 or attr == 4 or attr == 5:
            market += node.choose([com])
    
    estimated = round(market / cicli, 4)
    real = data["market_inc"]

    real_trend_str = "Neutral"
    if real > 0:
        real_trend_str = "Positive"
    elif real < 0:
        real_trend_str = "Negative"

    est_trend_str = "Neutral"
    if estimated > 0:
        est_trend_str = "Positive"
    elif estimated < 0:
        est_trend_str = "Negative"
    
    print("\nEstimated market trend is: " + est_trend_str + "(" + str(round(estimated, 4)) + "). " +
          "Real market trend was: " + real_trend_str + "(" + str(round(real, 4)) + ").")

    return estimated, rea

if __name__ == '__main__':
    attributes = 1
    n_cycles = 1000
    path_to_sentiments = 'sentiment_AFINN'
    
    files = [path_to_sentiments + "/" + file for file in os.listdir(path_to_sentiments) if file.endswith('.json')]
    for file in files:
        bn_learn(attributes, n_cycles, file)

    print "DONE! :D"