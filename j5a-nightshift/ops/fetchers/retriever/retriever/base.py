class BaseAgent:
    def supports(self, target):
        raise NotImplementedError
    def retrieve(self, target, **kw):
        raise NotImplementedError
