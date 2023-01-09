from myelasticsearch.es_wrapper import ESWrapper

es_dev = ESWrapper(env="dev")
card_dev = ESWrapper(env="dev", service="card")
commerce_dev = ESWrapper(env="dev", service="commerce_dev")
commerce = ESWrapper(env="dev", service="commerce")
advice_dev = ESWrapper(env="dev", service="advice")
project_dev = ESWrapper(env="dev", service="project")
question_dev = ESWrapper(env="dev", service="question")

SERVICE_LIST = es_dev.get_service_list()
SERVICE_TO_ES = {
    "card": card_dev,
    "commerce": commerce,
    "commerce_dev": commerce_dev,
    "advice": advice_dev,
    "project": project_dev,
    "question": question_dev,
}


if __name__ == '__main__':
    import json
    from ranking.card import *
    searcher = card_dev
    query = '멀티탭커버'
    query = 'Dion Horstman'
    query = '흙쇼파'
    query = '핸드폰케이스'
    query = '길이조절바구니'
    query = '러그'
    # res = searcher.get_search_result(query)
    # res = searcher.get_search_result(request_body=asis.generate(query), explain=True)
    # res = searcher.get_search_result(request_body=asis_proximity_shingle.generate(query), explain=True)
    # res = searcher.get_search_result(request_body=asis_proximity_match_phrase.generate(query), explain=True)
    # res = searcher.get_search_result(request_body=asis_proximity_match_phrase_rescore.generate(query), explain=True)
    # res = searcher.get_search_result(request_body=bm25norm_tobe.generate(query), explain=True)
    res = searcher.get_search_result(request_body=ltr_test.generate(query,ltr_model="xgb-lambdamart-1w.v3.20220427.card.test.v1"), explain=True)

    print(json.dumps(res["result"], indent=4, ensure_ascii=False))
