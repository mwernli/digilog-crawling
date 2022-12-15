from DataSourceSlim import DataSourceSlim

ds = DataSourceSlim()
items = [ds.mongo.db.simpleanalysis.find_one({'crawl_id': crawl_id}) for crawl_id in range(4186, 4243)]
