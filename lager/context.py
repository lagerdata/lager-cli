"""
    lager.context

    CLI context management
"""

class LagerContext:
    """
        Lager Context manager
    """
    def __init__(self, session, defaults, colored):
        self.session = session
        self.defaults = defaults
        self.colored = colored

    @property
    def default_gateway(self):
        """
            Get default gateway id from config
        """
        return self.defaults.get('gateway_id')
