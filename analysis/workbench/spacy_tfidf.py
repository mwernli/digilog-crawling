# Note: This requires these setup steps:
#   pip install tmtoolkit[recommended]
#   python -m tmtoolkit setup en
from tmtoolkit.corpus import Corpus, tokens_table, lemmatize, to_lowercase, dtm
from tmtoolkit.bow.bow_stats import tfidf, sorted_terms_table
from datetime import datetime
# load built-in sample dataset and use 4 worker processes
start0 = datetime.now()
# corp = Corpus.from_builtin_corpus('en-News100', max_workers=4)
corp = Corpus(text_dict['text'], language='de')
end = datetime.now() - start0
print(f'create corpus: {end.seconds/60} mins')

# investigate corpus as dataframe
start = datetime.now()
toktbl = tokens_table(corp)
end = datetime.now() -start
print(f'create token table: {end.seconds/60} mins')
# print(toktbl)

# apply some text normalization
start = datetime.now()
lemmatize(corp)
end = datetime.now() -start
print(f'lemmatice corpus: {end.seconds/60} mins')

start = datetime.now()
to_lowercase(corp)
end = datetime.now() -start
print(f'lower case corpus: {end.seconds/60} mins')
# build sparse document-token matrix (DTM)
# document labels identify rows, vocabulary tokens identify columns
start = datetime.now()
mat, doc_labels, vocab = dtm(corp, return_doc_labels=True, return_vocab=True)
end = datetime.now() -start
print(f'build sparse document-token matrix (DTM): {end.seconds/60} mins')
# apply tf-idf transformation to DTM
# operation is applied on sparse matrix and uses few memory
start = datetime.now()
tfidf_mat = tfidf(mat)
end = datetime.now() -start
print(f'apply tf-idf transformation to DTM: {end.seconds/60} mins')
# show top 5 tokens per document ranked by tf-idf
start = datetime.now()
top_tokens = sorted_terms_table(tfidf_mat, vocab, doc_labels, top_n=5)
end = datetime.now() -start
print(f'show top 5 tokens per document ranked by tf-idf: {end.seconds/60} mins')
# print(top_tokens)
print(f'time for all: {(datetime.now() - start0)/60} min')