class BaseScrapper:
    source = None

    def scrap(self):
        raise NotImplementedError("Subclasses must implement this method.")