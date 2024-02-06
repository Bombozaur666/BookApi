class AsyncIter:
    def __init__(self, value_list: list):
        self.value_list = value_list
        self.current = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        self.current += 1
        if self.current == len(self.value_list):
            raise StopAsyncIteration
        return self.value_list[self.current]
