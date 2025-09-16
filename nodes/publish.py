from chains.publish_chain import build_publish_chain

class PublishNode:
    def __init__(self):
        self.chain = build_publish_chain()

    def run(self, request):
        return self.chain.run(request)
