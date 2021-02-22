import logging
import matplotlib.pyplot as plt
import numpy as np
from scripts.hashing.fuzzy_hash_common import get_fuzzy_hash_documents_by_regex, filter_fuzzy_hash_documents_by_firmware
from model import LzjdHash
from scripts.rq_tasks.task_util import create_app_context


def start_cluster_analysis(regex_filter, firmware_id_list):
    create_app_context()
    lzjd_hash_list = get_fuzzy_hash_documents_by_regex(regex_filter, LzjdHash)
    lzjd_hash_list = filter_fuzzy_hash_documents_by_firmware(lzjd_hash_list, firmware_id_list)
    calc_cluster_by_nearest_neighbour(lzjd_hash_list)


def calc_cluster_by_nearest_neighbour(lzjd_hash_list):
    from pyLZJD import sim
    from sklearn.manifold import TSNE
    from sklearn.model_selection import cross_val_score
    from sklearn.neighbors import KNeighborsClassifier

    def lzjd_dist(a, b):
        a_i = lzjd_hash_list[int(a[0])]
        b_i = lzjd_hash_list[int(b[0])]
        return 1.0 - sim(a_i, b_i)

    labels_true = list(set([x[x.filename.find(".") + 1:] for x in lzjd_hash_list]))
    Y = np.asarray([labels_true.index(x[x.filename.find(".") + 1:]) for x in lzjd_hash_list])
    X = [[i] for i in range(len(lzjd_hash_list))]

    knn_model = KNeighborsClassifier(n_neighbors=5, algorithm='brute', metric=lzjd_dist)
    scores = cross_val_score(knn_model, X, Y, cv=5)
    logging.info("Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))
    X_embedded = TSNE(n_components=2, perplexity=5, metric=lzjd_dist).fit_transform(X)

    colors = [plt.cm.get_cmap("Spectral", each) for each in np.linspace(0, 1, len(labels_true))]
    for k, col in zip([z for z in range(len(labels_true))], colors):
        if k == -1:
            # Black used for noise.
            col = [0, 0, 0, 1]
        class_member_mask = (Y == k)
        xy = X_embedded[class_member_mask]
        plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col), markeredgecolor='k', markersize=5,
                 label=labels_true[k])
    plt.title('TSNE Visualization')
    plt.legend(loc='upper left')
    plt.show()
    #plt.savefig('foo.pdf')



