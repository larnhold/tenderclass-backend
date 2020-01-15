from src.classifier.TenderModel import TenderModel
from src.fetcher.TenderFetcher import TenderFetcher
from datetime import datetime


class TenderRecommender:

    def __init__(self):
        self.tender_fetcher = TenderFetcher()
        self.tender_model = TenderModel()

    def get_recommendations(self, count, date):
        tenders = self.tender_fetcher.get(count, search_criteria=" AND PD=[" + datetime.strftime(date, "%Y%m%d") + "]")
        selected_tenders = self.tender_model.classify(tenders)
        return selected_tenders
