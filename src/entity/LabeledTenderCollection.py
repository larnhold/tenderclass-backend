class LabelledTenderCollection:

    def __init__(self, labelled_tenders):
        self.labelled_tenders = labelled_tenders

    def get_original_language_entity_description(self):
        return list(map(lambda x: x.get_original_language_entity().description, self.get_tenders()))

    def get_titles(self, language="EN"):
        return list(map(lambda x: x.get_title(language), self.get_tenders()))

    def get_descriptions(self, language="EN"):
        return list(map(lambda x: x.get_description(language), self.get_tenders()))

    def get_tenders(self):
        return [i for i, j in self.labelled_tenders]

    def get_labels(self):
        return [int(j) for i, j in self.labelled_tenders]