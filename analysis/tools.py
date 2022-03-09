from DataSourceSlim import DataSourceSlim
import numpy as np
import matplotlib.pyplot as plt

ds = DataSourceSlim() 
docs = ds.mongo.db.simpleresults.find({'crawl_id': 524})  
items = [item for item in docs]     
ar = np.array([len(item['html']) for item in items])
desc_ind = ar.argsort()[::-1]
print(np.quantile(ar, 0.99))
print(ar[desc_ind][0])

plt.hist(ar, bins = 100)
plt.show()

big_items = [item for item in items if len(item['html']) > 800000]
big_ar = np.array([item for item in ar if item > 800000])
big_desc_ind = big_ar.argsort()[::-1]

plt.plot(
	# np.arange(len(ar)-1), 
	np.arange(100),
	np.diff(ar[desc_ind])[:100]
)
plt.show()

