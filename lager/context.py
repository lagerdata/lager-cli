"""
    lager.context

    CLI context management
"""

class LagerContext:
    """
        Lager Context manager
    """
    def __init__(self, session):
        self.session = session

