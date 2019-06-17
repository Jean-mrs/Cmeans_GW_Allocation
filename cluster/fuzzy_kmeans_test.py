import numpy as np
import random
import matplotlib.pyplot as plt
import pandas as pd
import os
from sklearn.cluster import KMeans
from cluster.optimalK_methods.kmeans_gap_statistics import gap_statistics_kmeans
from cluster.optimalK_methods.fuzzy_gap_statistics import gap_statistics_fuzzy
from cluster.fuzzycmeans.cmeans_algorithm import cmeans


points = 1000


# Data Setup
x = [random.randint(1, 10000) for j in range(points)]
y = [random.randint(1, 10000) for i in range(points)]
X = np.array(list(list(x) for x in zip(x, y)))

plt.scatter(X[:, 0], X[:, 1], s=10)
plt.show()

xpts = X[:, 0]
ypts = X[:, 1]
alldata = np.vstack((xpts,  ypts))

# optimalK = OptimalK(parallel_backend='rust')
# print(optimalK)
#
# n_clusters = optimalK(X, cluster_array=np.arange(1, 30))
# print('Optimal clusters: ', n_clusters)
#
# plt.plot(optimalK.gap_df.n_clusters, optimalK.gap_df.gap_value, linewidth=3)
# plt.scatter(optimalK.gap_df[optimalK.gap_df.n_clusters == n_clusters].n_clusters,
#             optimalK.gap_df[optimalK.gap_df.n_clusters == n_clusters].gap_value, s=250, c='r')
# plt.grid(True)
# plt.xlabel('cluster Count')
# plt.ylabel('Gap Value')
# plt.title('Gap Values by cluster Count')
# plt.show()

#K-means Gap Statistics
k, sk, gapdf, gapsk = gap_statistics_kmeans(X, nrefs=500, maxClusters=30)
print('Optimal k is: ', k)
plt.plot(gapdf.clusterCount, gapdf.gap, linewidth=3)
plt.scatter(gapdf[gapdf.clusterCount == k].clusterCount, gapdf[gapdf.clusterCount == k].gap, s=250, c='r')
plt.grid(True)
plt.xlabel('cluster Count')
plt.ylabel('Gap Value')
plt.title('Gap Values by cluster Count (K-Means)')
plt.show()
#
plt.bar(gapsk.clusterCount, gapsk.Gap_sk)
plt.xlabel('cluster Count')
plt.ylabel('gap[k] - gap[k+1] - sk[k+1]')
#plt.xticks(index, label, fontsize=5, rotation=30)
#plt.title('Market Share for Each Genre 1995-2017')
plt.show()

# K-means Algorithm
km = KMeans(k)
km.fit(X)

# Plot K-means
df = pd.DataFrame(X, columns=['x', 'y'])
df['label'] = km.labels_
colors = plt.get_cmap('Spectral')(np.linspace(0, 1, len(df.label.unique())))
for color, label in zip(colors, df.label.unique()):
    tempdf = df[df.label == label]
    plt.scatter(tempdf.x, tempdf.y, c=color, s=10)
plt.scatter(km.cluster_centers_[:, 0], km.cluster_centers_[:, 1], c='r', s=30, alpha=0.7, )
plt.grid(True)
plt.show()

# Fuzzy Gap Statistics
c, gapdfs, fpca, gapsk = gap_statistics_fuzzy(X, nrefs=500, maxClusters=30)
print('Optimal C is: ', c)
plt.plot(gapdfs.clusterCount, gapdfs.gap, linewidth=3)
plt.scatter(gapdfs[gapdfs.clusterCount == c[0]].clusterCount, gapdfs[gapdfs.clusterCount == c[0]].gap, s=250, c='r')
plt.grid(True)
plt.xlabel('cluster Count')
plt.ylabel('Gap Value')
plt.title('Gap Values by cluster Count (Fuzzy C-Means)')
plt.show()


plt.bar(gapsk.clusterCount, gapsk.Gap_sk)
plt.xlabel('cluster Count')
plt.ylabel('gap[k] - gap[k+1] - sk[k+1]')
#plt.title('Market Share for Each Genre 1995-2017')
plt.show()

# Fuzzy C-Means Algorithm
cntr, u, u0, d, jm, p, fpc = cmeans(data=alldata, c=c[0], m=2, error=0.005, maxiter=1000, init=None)
print("Euclidian Distance Matrix: ")
print(pd.DataFrame(d))
print("\n")
print("Final Matrix: ")
print(pd.DataFrame(u))
print("\n")

# Plot Fuzzy
#draw_model_2d(cntr, data=X, membership=np.transpose(u))

# Save Output
# X_df = pd.DataFrame(X)
# cntr_df = pd.DataFrame(cntr)
# export_csv = cntr_df.to_csv(r'/home/jean/Documentos/CEA-ML/cluster/Output/gateways'  + '.csv', header=True)
# export_csv2 = X_df.to_csv(r'/home/jean/Documentos/CEA-ML/cluster/Output/devices' + '.csv', header=True)
