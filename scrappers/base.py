class BaseScrapper:
    source = None

    def scrap(self, fini, ffin, q="", limit=100):
        raise NotImplementedError("Subclasses must implement this method.")